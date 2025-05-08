import { useState, useEffect, useRef } from 'react'
import './App.css'
import { WebSocketClient, ServiceType } from './utils/WebSocketClient'
import ActivityMonitor from './components/ActivityMonitor'
import EC2Instances from './components/EC2Instances'
import ECSClusters from './components/ECSClusters'
import EKSClusters from './components/EKSClusters'
import WebSocketConsole from './components/WebSocketConsole'
import Timer from './components/Timer'
import AboutModal from './components/AboutModal'
import LicenseModal from './components/LicenseModal'
import type { EC2Instance, ECSCluster, EKSCluster, ActivityStatus, WebSocketMessage } from './types/aws'
import { useTranslation } from 'react-i18next'

// 타이머 최대값 기본값 (30분 = 30 * 60 * 1000 밀리초)
// WebSocket으로부터 maxtime이 전달되면 이 값을 대체함
const DEFAULT_MAX_TIMER_VALUE = 30 * 60 * 1000;

// 지원하는 언어 목록
const SUPPORTED_LANGUAGES = [
  { code: 'en', name: 'English' },
  { code: 'ko', name: '한국어' },
  { code: 'ja', name: '日本語' },
  { code: 'zh', name: '中文' }
];

// 브라우저 언어 감지 함수
const detectBrowserLanguage = (): string => {
  const browserLang = navigator.language.split('-')[0]; // 'ko-KR' -> 'ko'
  const supportedLangCodes = SUPPORTED_LANGUAGES.map(lang => lang.code);
  
  // 지원하는 언어인지 확인하고, 지원하는 언어면 해당 언어 반환, 아니면 영어 반환
  return supportedLangCodes.includes(browserLang) ? browserLang : 'en';
};

function App() {
	// Initialize i18n hooks
	const { t, i18n } = useTranslation();

	// State for data received from WebSocket
	const [activityStatus, setActivityStatus] = useState<ActivityStatus>({
		keyboard: false,
		mouseMovement: false,
		mouseClick: false,
		screen: false,
		audio: false,
		activeWindow: ''
	});
	const [ec2Instances, setEC2Instances] = useState<EC2Instance[]>([]);
	const [ecsClusters, setECSClusters] = useState<ECSCluster[]>([]);
	const [eksClusters, setEKSClusters] = useState<EKSCluster[]>([]);
	const [connectionStatus, setConnectionStatus] = useState<string>('disconnected');
	const [socketMessages, setSocketMessages] = useState<WebSocketMessage[]>([]);
	const [isProcessingAction, setIsProcessingAction] = useState<boolean>(false);
	
	// Modal visibility states
	const [isAboutModalOpen, setIsAboutModalOpen] = useState<boolean>(false);
	const [isLicenseModalOpen, setIsLicenseModalOpen] = useState<boolean>(false);
	
	// 타이머 상태 추가 - 서버에서 전송하는 값을 사용
	const [timerValue, setTimerValue] = useState<number>(0);
	const [maxTimerValue, setMaxTimerValue] = useState<number>(DEFAULT_MAX_TIMER_VALUE); // 동적으로 설정될 수 있는 최대 타이머 값
	const [isUserActive, setIsUserActive] = useState<boolean>(false);
	
	// 언어 설정 상태 추가
	const [currentLanguage, setCurrentLanguage] = useState<string>('en');
	
	// 모바일 메뉴 토글 상태
	const [isMobileMenuOpen, setIsMobileMenuOpen] = useState<boolean>(false);

	// Reference to WebSocketClient instance
	const webSocketClientRef = useRef<WebSocketClient | null>(null);

	// WebSocket port - 백엔드 서버 포트와 일치하도록 수정
	const WEBSOCKET_PORT = 20201; 

	// Maximum number of socket messages to store
	const MAX_MESSAGES = 500;

	// Change language handler
	const handleLanguageChange = (lang: string) => {
		setCurrentLanguage(lang);
		i18n.changeLanguage(lang);
		localStorage.setItem('language', lang);
	};

	// Modal handlers
	const openAboutModal = () => {
		setIsAboutModalOpen(true);
		// Close mobile menu if open
		if (isMobileMenuOpen) setIsMobileMenuOpen(false);
	};

	const closeAboutModal = () => {
		setIsAboutModalOpen(false);
	};

	const openLicenseModal = () => {
		setIsLicenseModalOpen(true);
		// Close mobile menu if open
		if (isMobileMenuOpen) setIsMobileMenuOpen(false);
	};

	const closeLicenseModal = () => {
		setIsLicenseModalOpen(false);
	};

	// 빈 샘플 데이터 설정
	const loadMockData = () => {
		// Empty EC2 data
		setEC2Instances([]);

		// Empty ECS data
		setECSClusters([]);

		// Empty EKS data
		setEKSClusters([]);

		// Only set active flags for keyboard, mouse movement, and mouse click
		setActivityStatus({
			keyboard: false,
			mouseMovement: false,
			mouseClick: false,
			screen: false,
			audio: false,
			activeWindow: ''
		 });
		
		// 타이머 값도 초기화
		setTimerValue(0);
	};

	useEffect(() => {
		// Initialize language from localStorage or detect browser language
		const savedLanguage = localStorage.getItem('language') || detectBrowserLanguage();
		setCurrentLanguage(savedLanguage);
		i18n.changeLanguage(savedLanguage);

		// 초기 화면 표시를 위해 즉시 샘플 데이터 로드
		loadMockData();
		
		// Create a WebSocket client instance
		const webSocketClient = new WebSocketClient(
			WEBSOCKET_PORT,
			handleWebSocketMessage,
			"localhost" // 호스트 명시적으로 설정
		);
		
		// 연결 끊김 콜백 설정
		webSocketClient.setDisconnectCallback(() => {
			setConnectionStatus('disconnected');
			// 연결이 끊어지면 데이터 초기화
			loadMockData();
		});
		
		// Store the client in ref for later use
		webSocketClientRef.current = webSocketClient;
		
		// Connect to the WebSocket server
		webSocketClient.connect();
		setConnectionStatus('connecting');

		// WebSocket 연결 상태 주기적 체크
		const connectionCheck = setInterval(() => {
			// getConnectionStatus 메서드를 통해 연결 상태 확인
			if (webSocketClientRef.current && webSocketClientRef.current.getConnectionStatus()) {
				setConnectionStatus('connected');
				clearInterval(connectionCheck);
			}
		}, 1000);

		// 서버에 연결되면 실제 데이터 요청
		const requestDataInterval = setInterval(() => {
			// getConnectionStatus 메서드를 통해 연결 상태 확인
			if (webSocketClientRef.current && webSocketClientRef.current.getConnectionStatus()) {
				// 연결되었으면 실제 데이터 요청
				webSocketClientRef.current.send({
					type: "AWS_SERVICE_LIST_ALL",
					content: {
						region: "ap-northeast-2"
					}
				});

				clearInterval(requestDataInterval);
			}
		}, 2000);

		// Clean up the WebSocket connection on component unmount
		return () => {
			webSocketClient.disconnect();
			clearInterval(connectionCheck);
			clearInterval(requestDataInterval);
		};
	}, [i18n]);

	// Save language preference to localStorage when it changes
	useEffect(() => {
		localStorage.setItem('language', currentLanguage);
	}, [currentLanguage]);

	// Handle messages received from WebSocket
	const handleWebSocketMessage = (message: WebSocketMessage) => {
		// console.log("WebSocket 메시지 수신:", message);
		setConnectionStatus('connected');
		
		// Add the message to the console messages
		setSocketMessages(prevMessages => {
			// Add new message and limit to MAX_MESSAGES by removing old ones
			const updatedMessages = [...prevMessages, message];
			return updatedMessages.slice(Math.max(0, updatedMessages.length - MAX_MESSAGES));
		});
		
		// 서비스 타입에 따라 적절한 데이터 처리
		if (message.service === "ec2" && message.instances) {
			setEC2Instances(message.instances);
			// EC2 인스턴스 상태 변경 후 처리 완료
			if (message.status === "updated") {
				setIsProcessingAction(false);
			}
		}
		else if (message.service === "ecs" && message.clusters) {
			// Type assertion to ensure we're setting the correct cluster type
			setECSClusters(message.clusters as ECSCluster[]);
		}
		else if (message.service === "eks" && message.clusters) {
			setEKSClusters(message.clusters as EKSCluster[]);
		}
		else if (message.service === "activity") {
			// 활동 상태 업데이트 처리
			if (message.data && typeof message.data === 'object') {
				setActivityStatus(prev => ({...prev, ...message.data}));
			}
		}
		// 새로운 메시지 형식 처리: USER_ACTIVITY 타입
		else if (message.type === "USER_ACTIVITY" && message.content?.activity) {
			const activityType = message.content.activity;
			
			 // TIMER_TICK 처리
			if (activityType === "TIMER_TICK" && message.content?.nowtime) {
				setTimerValue(message.content.nowtime);
				// maxtime이 제공되면 타이머 최대값 업데이트
				if (message.content?.maxtime) {
					setMaxTimerValue(message.content.maxtime);
				}
				return;
			}
			
			// 활동 유형에 따라 상태 업데이트
			const activityUpdate: Partial<ActivityStatus> = {
				keyboard: activityType === "KEYBOARD_ACTIVITY" ? true : false,
				mouseMovement: activityType === "MOUSE_MOVEMENT" ? true : false,
				mouseClick: activityType === "MOUSE_CLICK" ? true : false,
				audio: activityType === "AUDIO_PLAYBACK" ? true : false,
			};
			
			// 활동 상태 업데이트
			setActivityStatus(prev => ({
				...prev,
				...activityUpdate
			}));
			
			// 사용자 활동 상태 업데이트
			setIsUserActive(true);
			
			// 깜빡임 효과를 위해 잠시 후 상태 초기화
			setTimeout(() => {
				setActivityStatus(prev => ({
					...prev,
					keyboard: false,
					mouseMovement: false,
					mouseClick: false,
					audio: false
				}));
				setIsUserActive(false);
			}, 1000);
		}
		// EC2 인스턴스 업데이트 처리
		else if (message.type === "AWS_EC2_UPDATE" && message.content) {
			if (message.content.instances) {
				setEC2Instances(message.content.instances);
			}
			setIsProcessingAction(false); // 액션 처리 완료
		}
		// EC2 인스턴스 에러 처리
		else if (message.type === "AWS_EC2_ERROR" && message.content) {
			setIsProcessingAction(false); // 에러지만 액션 처리 완료
			// 에러 메시지 표시 로직이 있다면 여기에 추가
		}
		// 기존 메시지 형식 지원
		else if (message.type) {
			if (message.type === "activity" && message.data) {
				setActivityStatus(message.data);
			}
			else if (message.type === "ec2-instances" && message.data) {
				setEC2Instances(message.data);
			}
			else if (message.type === "ecs-clusters" && message.data) {
				setECSClusters(message.data);
			}
			else if (message.type === "eks-clusters" && message.data) {
				setEKSClusters(message.data);
			}
			// 응답이 content 필드에 데이터가 있는 경우
			else if (message.content) {
				const content = message.content;
				if (content.instances) {
					setEC2Instances(content.instances);
				}
				if (content.clusters && message.type.includes("ECS")) {
					setECSClusters(content.clusters);
				}
				if (content.clusters && message.type.includes("EKS")) {
					setEKSClusters(content.clusters);
				}
				if (content.activity) {
					// content.activity가 문자열인 경우 (새로운 형식)
					if (typeof content.activity === 'string') {
						const activityType = content.activity;
						const activityUpdate: Partial<ActivityStatus> = {
							keyboard: activityType === "KEYBOARD_ACTIVITY" ? true : false,
							mouseMovement: activityType === "MOUSE_MOVEMENT" ? true : false,
							mouseClick: activityType === "MOUSE_CLICK" ? true : false
						};
						
						setActivityStatus(prev => ({
							...prev,
							...activityUpdate
						}));
						
						// 사용자 활동 상태 업데이트
						setIsUserActive(true);
						
						// 깜빡임 효과를 위해 잠시 후 상태 초기화
						setTimeout(() => {
							setActivityStatus(prev => ({
								...prev,
								keyboard: false,
								mouseMovement: false,
								mouseClick: false
							}));
							setIsUserActive(false);
						}, 1000);
					} 
					// 기존 형식 (객체)
					else {
						setActivityStatus(prev => ({...prev, ...content.activity}));
					}
				}
			}
		}
	};

	// Clear console messages
	const clearSocketMessages = () => {
		setSocketMessages([]);
	};

	// Try to reconnect WebSocket
	const handleReconnect = () => {
		if (webSocketClientRef.current) {
			setConnectionStatus('connecting');
			webSocketClientRef.current.connect();
			
			// 연결 후 데이터 요청
			setTimeout(() => {
				// getConnectionStatus 메서드를 통해 연결 상태 확인
				if (webSocketClientRef.current && webSocketClientRef.current.getConnectionStatus()) {
					// 표준 JSON 형식으로 메시지 전송
					webSocketClientRef.current.send({
						type: "AWS_SERVICE_LIST_ALL",
						content: {
							region: "ap-northeast-2"
						}
					});
				}
			}, 2000);
		}
	};

	// 데이터 새로고침
	const handleRefreshData = () => {
		// getConnectionStatus 메서드를 통해 연결 상태 확인
		if (webSocketClientRef.current && webSocketClientRef.current.getConnectionStatus()) {
			// 표준 JSON 메시지 형식으로 요청
			webSocketClientRef.current.send({
				type: "AWS_SERVICE_LIST_ALL",
				content: {
					region: "ap-northeast-2"
				}
			});
		} else {
			// 연결이 안되어 있으면 샘플 데이터 새로고침
			loadMockData();
		}
	};

	// 서비스별 개별 데이터 새로고침
	const handleRefreshEC2 = () => {
		if (webSocketClientRef.current && webSocketClientRef.current.getConnectionStatus()) {
			// EC2 인스턴스 목록 요청 (표준 JSON 형식)
			webSocketClientRef.current.send({
				action: "refresh_service",
				service: "ec2",
			});
		} else {
			// Mock data - empty for now
			setEC2Instances([]);
		}
	};

	const handleRefreshECS = () => {
		if (webSocketClientRef.current && webSocketClientRef.current.getConnectionStatus()) {
			// ECS 클러스터 목록 요청 (표준 JSON 형식)
			webSocketClientRef.current.send({
				action: "refresh_service",
				service: "ec2",
			});
		} else {
			// Mock data - empty for now
			setECSClusters([]);
		}
	};

	const handleRefreshEKS = () => {
		if (webSocketClientRef.current && webSocketClientRef.current.getConnectionStatus()) {
			// EKS 클러스터 목록 요청 (표준 JSON 형식)
			webSocketClientRef.current.send({
				action: "refresh_service",
				service: "ec2",
			});
		} else {
			// Mock data - empty for now
			setEKSClusters([]);
		}
	};

	// EC2 인스턴스 시작 처리
	const handleStartEC2Instance = (instanceId: string) => {
		if (webSocketClientRef.current && webSocketClientRef.current.getConnectionStatus()) {
			// 이미 처리 중인 작업이 있으면 무시
			if (isProcessingAction) {
				return;
			}
			
			setIsProcessingAction(true); // 처리 중 상태 설정
			
			// 메시지 전송 방식 1: 기존 action 방식
			webSocketClientRef.current.send({
				action: "startInstance",
				instanceId: instanceId,
				region: "ap-northeast-2"
			});
			
			// 메시지 전송 방식 2: 새로운 타입 기반 방식 (둘 중 하나만 선택)
			// webSocketClientRef.current.send({
			//   type: "AWS_EC2_START_INSTANCE",
			//   content: {
			//     instanceId: instanceId,
			//     region: "ap-northeast-2"
			//   }
			// });
			
			// 인스턴스 상태 임시 업데이트 (UX 개선)
			setEC2Instances(prevInstances => 
				prevInstances.map(instance => 
					instance.id === instanceId 
						? { ...instance, state: 'pending' } 
						: instance
				)
			);
			
			// 콘솔 메시지에도 기록
			setSocketMessages(prev => [...prev, {
				type: 'CLIENT_ACTION',
				content: {
					action: 'startInstance',
					instanceId: instanceId
				},
				timestamp: new Date().toISOString()
			}]);
		}
	};
	
	// EC2 인스턴스 중지 처리
	const handleStopEC2Instance = (instanceId: string) => {
		if (webSocketClientRef.current && webSocketClientRef.current.getConnectionStatus()) {
			// 이미 처리 중인 작업이 있으면 무시
			if (isProcessingAction) {
				return;
			}
			
			setIsProcessingAction(true); // 처리 중 상태 설정
			
			// 메시지 전송 방식 1: 기존 action 방식
			webSocketClientRef.current.send({
				action: "stopInstance",
				instanceId: instanceId,
				region: "ap-northeast-2"
			});
			
			// 메시지 전송 방식 2: 새로운 타입 기반 방식 (둘 중 하나만 선택)
			// webSocketClientRef.current.send({
			//   type: "AWS_EC2_STOP_INSTANCE",
			//   content: {
			//     instanceId: instanceId,
			//     region: "ap-northeast-2"
			//   }
			// });
			
			// 인스턴스 상태 임시 업데이트 (UX 개선)
			setEC2Instances(prevInstances => 
				prevInstances.map(instance => 
					instance.id === instanceId 
						? { ...instance, state: 'stopping' } 
						: instance
				)
			);
			
			// 콘솔 메시지에도 기록
			setSocketMessages(prev => [...prev, {
				type: 'CLIENT_ACTION',
				content: {
					action: 'stopInstance',
					instanceId: instanceId
				},
				timestamp: new Date().toISOString()
			}]);
		}
	};

	// Simulate activity for testing purposes
	const simulateActivity = () => {
		const randomKeyboard = Math.random() > 0.5;
		const randomMouseMovement = Math.random() > 0.5;
		const randomMouseClick = Math.random() > 0.5;
		
		setActivityStatus(prev => ({
			...prev,
			keyboard: randomKeyboard,
			mouseMovement: randomMouseMovement,
			mouseClick: randomMouseClick
		}));
		
		// Reset after a short delay to simulate the blinking effect
		setTimeout(() => {
			setActivityStatus(prev => ({
				...prev,
				keyboard: false,
				mouseMovement: false,
				mouseClick: false
			}));
		}, 1000);
	};

	// Simulate activity periodically for demonstration
	useEffect(() => {
		const activityInterval = setInterval(() => {
			if (!webSocketClientRef.current?.getConnectionStatus()) {
				simulateActivity();
			}
		}, 3000);
		
		return () => clearInterval(activityInterval);
	}, []);

	// Mobile menu toggle function
	const toggleMobileMenu = () => {
		setIsMobileMenuOpen(!isMobileMenuOpen);
	};

	return (
		<>
			<div className="dashboard-container">
				<header className="dashboard-header">
					<h1>Studente AWS</h1>
					
					{/* Mobile menu toggle button */}
					<button 
						className="mobile-menu-button" 
						onClick={toggleMobileMenu}
						aria-label="Toggle menu"
					>
						{isMobileMenuOpen ? '✕' : '☰'}
					</button>
					
					<div className={`header-controls ${isMobileMenuOpen ? 'mobile-open' : ''}`}>
						<div className="header-actions">
							<button className="refresh-button" onClick={handleRefreshData}>
								{t('buttons.refresh')}
							</button>
							
							<div className={`connection-status ${connectionStatus}`}>
								{t(`connection.${connectionStatus}`)}
							</div>
							
							{connectionStatus === 'disconnected' && (
								<button className="retry-button" onClick={handleReconnect}>
									{t('buttons.retry')}
								</button>
							)}
						</div>
						
						{/* 언어 선택 드롭다운 */}
						<div className="language-selector">
							<span className="language-label">{t('header.language')}</span>
							<select 
								value={currentLanguage} 
								onChange={(e) => handleLanguageChange(e.target.value)}
								className="language-dropdown"
							>
								{SUPPORTED_LANGUAGES.map(lang => (
									<option key={lang.code} value={lang.code}>
										{lang.name}
									</option>
								))}
							</select>
						</div>
						
						{/* About/License 페이지 링크 - Connect to modal functions */}
						<div className="page-links">
							<button className="about-button" onClick={openAboutModal}>
								{t('header.about')}
							</button>
							<button className="license-button" onClick={openLicenseModal}>
								{t('header.license')}
							</button>
						</div>
					</div>
				</header>

				{/* Tracker Download Box - Shows only when disconnected */}
				{connectionStatus === 'disconnected' && (
					<div className="tracker-download-box">
						<div className="download-content">
							<h3>{t('download.title', 'Download Tracker Application')}</h3>
							<p>{t('download.description', 'To connect to AWS services, you need to install the Studente AWS Tracker application.')}</p>
							<div className="download-buttons">
								<a 
									href="https://github.com/taxi-tabby/studente_aws/raw/refs/heads/main/dist/main.exe" 
									className="download-button"
									target="_blank"
									rel="noopener noreferrer"
								>
									{t('download.windows', 'Download for Windows')}
								</a>
							</div>
						</div>
					</div>
				)}

				<main className="dashboard-content">
					{/* 모든 컴포넌트에 연결 상태 전달 */}
					<ActivityMonitor 
						activityStatus={activityStatus} 
						isConnected={connectionStatus === 'connected'} 
					/>
					
					<Timer 
						value={timerValue} 
						maxValue={maxTimerValue} 
						isActive={isUserActive || activityStatus.keyboard || activityStatus.mouseMovement || activityStatus.mouseClick || activityStatus.audio}
						isConnected={connectionStatus === 'connected'} 
					/>

					{/* Control Panel */}
					<div className={`control-panel ${connectionStatus !== 'connected' ? 'disconnected' : ''}`}>
						<div className="control-panel-container">
							<div className="control-panel-header">
								<h3>{t('controlPanel.title', 'Control Panel')}</h3>
								{connectionStatus !== 'connected' && (
									<span className="control-panel-connection-warning">({t('connection.disconnected')})</span>
								)}
							</div>
							
							<div className="control-panel-grid">
								{/* Session Time Control */}
								<div className="control-panel-section">
									<h4>{t('controlPanel.sessionSettings', 'Session Settings')}</h4>
									<div className="control-group">
										<label htmlFor="max-session-time">{t('controlPanel.maxSessionTime', 'Maximum Session Time')}</label>
										<div className="input-with-unit">
											<input 
												id="max-session-time" 
												type="number" 
												className="control-input" 
												min="5" 
												max="240" 
												defaultValue="30" 
												disabled={connectionStatus !== 'connected'}
											/>
											<span className="input-unit">{t('controlPanel.minutes', 'minutes')}</span>
										</div>
										<button 
											className="control-button primary"
											disabled={connectionStatus !== 'connected'}
										>
											{t('controlPanel.apply', 'Apply')}
										</button>
									</div>
								</div>
								
								{/* Dashboard Security */}
								<div className="control-panel-section">
									<h4>{t('controlPanel.security', 'Dashboard Security')}</h4>
									<div className="control-group">
										<label htmlFor="current-password">{t('controlPanel.currentPassword', 'Current Password')}</label>
										<input 
											id="current-password" 
											type="password" 
											className="control-input" 
											placeholder="••••••••" 
											disabled={connectionStatus !== 'connected'}
										/>
									</div>
									<div className="control-group">
										<label htmlFor="new-password">{t('controlPanel.newPassword', 'New Password')}</label>
										<input 
											id="new-password" 
											type="password" 
											className="control-input" 
											placeholder="••••••••" 
											disabled={connectionStatus !== 'connected'}
										/>
									</div>
									<div className="control-group">
										<label htmlFor="confirm-password">{t('controlPanel.confirmPassword', 'Confirm Password')}</label>
										<input 
											id="confirm-password" 
											type="password" 
											className="control-input" 
											placeholder="••••••••" 
											disabled={connectionStatus !== 'connected'}
										/>
										<button 
											className="control-button primary"
											disabled={connectionStatus !== 'connected'}
										>
											{t('controlPanel.changePassword', 'Change Password')}
										</button>
									</div>
								</div>
								
								{/* Activity Monitor Settings */}
								<div className="control-panel-section">
									<h4>{t('controlPanel.activitySettings', 'Activity Settings')}</h4>
									<div className="control-group">
										<label>{t('controlPanel.monitorSettings', 'Activity Detection')}</label>
										<div className="checkbox-group">
											<div className="checkbox-item">
												<input 
													id="keyboard-monitor" 
													type="checkbox" 
													defaultChecked 
													disabled={connectionStatus !== 'connected'}
												/>
												<label htmlFor="keyboard-monitor">{t('activity.keyboard')}</label>
											</div>
											<div className="checkbox-item">
												<input 
													id="mouse-movement-monitor" 
													type="checkbox" 
													defaultChecked 
													disabled={connectionStatus !== 'connected'}
												/>
												<label htmlFor="mouse-movement-monitor">{t('activity.mouseMovement')}</label>
											</div>
											<div className="checkbox-item">
												<input 
													id="mouse-click-monitor" 
													type="checkbox" 
													defaultChecked 
													disabled={connectionStatus !== 'connected'}
												/>
												<label htmlFor="mouse-click-monitor">{t('activity.mouseClick')}</label>
											</div>
											<div className="checkbox-item">
												<input 
													id="screen-monitor" 
													type="checkbox" 
													defaultChecked 
													disabled={connectionStatus !== 'connected'}
												/>
												<label htmlFor="screen-monitor">{t('activity.screenChange')}</label>
											</div>
											<div className="checkbox-item">
												<input 
													id="audio-monitor" 
													type="checkbox" 
													defaultChecked 
													disabled={connectionStatus !== 'connected'}
												/>
												<label htmlFor="audio-monitor">{t('activity.audio')}</label>
											</div>
										</div>
										<button 
											className="control-button primary"
											disabled={connectionStatus !== 'connected'}
										>
											{t('controlPanel.saveSettings', 'Save Settings')}
										</button>
									</div>
								</div>
							</div>
						</div>
					</div>


					<div className="aws-services">
						<EC2Instances 
							instances={ec2Instances} 
							onRefresh={handleRefreshEC2} 
							onStartInstance={handleStartEC2Instance}
							onStopInstance={handleStopEC2Instance}
							isConnected={connectionStatus === 'connected'}
						/>
						<ECSClusters 
							clusters={ecsClusters} 
							onRefresh={handleRefreshECS}
							isConnected={connectionStatus === 'connected'} 
						/>
						<EKSClusters 
							clusters={eksClusters} 
							onRefresh={handleRefreshEKS}
							isConnected={connectionStatus === 'connected'} 
						/>
					</div>
					
					<div className="console-section">
						<div className="console-header">
							<h2>Messages</h2>
						</div>
						<WebSocketConsole 
							messages={socketMessages}
							isConnected={connectionStatus === 'connected'}
							onClearMessages={clearSocketMessages}
						/>
					</div>
				</main>

				<footer className="dashboard-footer">
					<p>Studente AWS &copy; {new Date().getFullYear()} by <i>rkdmf0000@gmail.com</i></p>
				</footer>
			</div>

			{/* Render modal components */}
			<AboutModal 
				isOpen={isAboutModalOpen}
				onClose={closeAboutModal}
			/>
			
			<LicenseModal
				isOpen={isLicenseModalOpen}
				onClose={closeLicenseModal} 
			/>
		</>
	)
}

export default App
