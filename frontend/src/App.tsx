import { useState, useEffect, useRef } from 'react'
import './App.css'
import { WebSocketClient } from './utils/WebSocketClient'
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

	// 비밀번호 관련 상태
	const [password, setPassword] = useState<string>('');
	const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
	const [passwordError, setPasswordError] = useState<string | null>(null);
	const [isInitialSetup, setIsInitialSetup] = useState<boolean>(false); // 최초 비밀번호 설정 여부
	const [authKey, setAuthKey] = useState<string | null>(null); // 서버에서 발급받은 인증 키
	const [newPassword, setNewPassword] = useState<string>(''); // 신규 비밀번호 설정
	const [confirmPassword, setConfirmPassword] = useState<string>(''); // 비밀번호 확인

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
	};	useEffect(() => {
		// Initialize language from localStorage or detect browser language
		const savedLanguage = localStorage.getItem('language') || detectBrowserLanguage();
		setCurrentLanguage(savedLanguage);
		i18n.changeLanguage(savedLanguage);

		// 저장된 인증 키 확인
		const savedAuthKey = sessionStorage.getItem('authKey');
		if (savedAuthKey) {
			setAuthKey(savedAuthKey);
			// 인증 키 유효성 검사는 서버 연결 후 수행
		}

		// 기본적으로는 인증 안됨 상태로 시작 (서버에서 확인 필요)
		setIsAuthenticated(false);
		
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
		
		// 연결 시도 횟수를 추적하기 위한 변수
		let connectionAttempts = 0;
		
		// WebSocket 연결 상태 주기적 체크
		const connectionCheck = setInterval(() => {
			// getConnectionStatus 메서드를 통해 연결 상태 확인
			if (webSocketClientRef.current && webSocketClientRef.current.getConnectionStatus()) {
				setConnectionStatus('connected');
				
				// 연결 성공 시 비밀번호 상태 확인 요청
				webSocketClientRef.current.send({
					type: "PASSWORD_STATUS_CHECK"
				});
				
				// 저장된 인증 키가 있다면 검증 요청
				const savedAuthKey = sessionStorage.getItem('authKey');
				if (savedAuthKey) {
					webSocketClientRef.current.send({
						type: "VERIFY_AUTH_KEY",
						content: {
							authKey: savedAuthKey
						}
					});
				}
						// 서버에서 PASSWORD_STATUS 응답이 올 때까지 대기
				// 실제 서버에서는 응답이 올 것이므로 여기서는 임시 설정을 하지 않음
				const responseTimeout = setTimeout(() => {
					if (!isAuthenticated) {
						console.log("서버에서 응답 대기 중");
						// 임시 초기 설정 모드 활성화는 제거
					}
					clearTimeout(responseTimeout);
				}, 10000);
						clearInterval(connectionCheck);
			} else {				// 연결 시도 횟수를 추적
				connectionAttempts++;
				if (connectionAttempts > 10) {
					console.log("서버 연결 실패, 계속 연결 시도 중");
					// 연결이 안 된 상태에서는 초기 설정 모드 활성화하지 않음
					clearInterval(connectionCheck);
				}
			}
		}, 1000);

		// 서버에 연결되면 실제 데이터 요청
		// const requestDataInterval = setInterval(() => {
		// 	// getConnectionStatus 메서드를 통해 연결 상태 확인
		// 	if (webSocketClientRef.current && webSocketClientRef.current.getConnectionStatus()) {
		// 		// 연결되었으면 실제 데이터 요청
		// 		webSocketClientRef.current.send({
		// 			type: "AWS_SERVICE_LIST_ALL",
		// 			content: {
		// 				region: "ap-northeast-2"
		// 			}
		// 		});

		// 		clearInterval(requestDataInterval);
		// 	}
		// }, 2000);

		// Clean up the WebSocket connection on component unmount
		return () => {
			webSocketClient.disconnect();
			clearInterval(connectionCheck);
			// clearInterval(requestDataInterval);
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

		// 비밀번호 초기 설정 필요 여부 확인
		if (message.type === "PASSWORD_STATUS") {
			if (message.content?.isInitialSetup) {
				// 비밀번호가 아직 설정되지 않은 상태
				setIsInitialSetup(true);
			} else {
				// 비밀번호가 이미 설정되어 있는 상태
				setIsInitialSetup(false);
			}
			return;
		}

		// 비밀번호 검증 응답 처리
		if (message.type === "PASSWORD_VERIFY_RESPONSE") {
			if (message.content?.success) {
				setIsAuthenticated(true);
				setPasswordError(null);
				
				// 서버에서 발급한 인증 키 저장
				if (message.content?.authKey) {
					setAuthKey(message.content.authKey);
					// 로컬에 인증 키 저장 (실제 구현에서는 세션이나 안전한 쿠키 사용 필요)
					sessionStorage.setItem('authKey', message.content.authKey);
				}
			} else {
				setPasswordError(message.content?.error || t('password.error.invalid', '잘못된 비밀번호입니다.'));
			}
			return;
		}
		
		// 비밀번호 설정 응답 처리
		if (message.type === "PASSWORD_CREATE_RESPONSE") {
			if (message.content?.success) {
				setIsAuthenticated(true);
				setIsInitialSetup(false);
				setPasswordError(null);
				
				// 서버에서 발급한 인증 키 저장
				if (message.content?.authKey) {
					setAuthKey(message.content.authKey);
					// 로컬에 인증 키 저장 (실제 구현에서는 세션이나 안전한 쿠키 사용 필요)
					sessionStorage.setItem('authKey', message.content.authKey);
				}
			} else {
				setPasswordError(message.content?.error || t('password.error.setup', '비밀번호 설정 중 오류가 발생했습니다.'));
			}
			return;
		}
		
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
			// setTimeout(() => {
			// 	// getConnectionStatus 메서드를 통해 연결 상태 확인
			// 	if (webSocketClientRef.current && webSocketClientRef.current.getConnectionStatus()) {
			// 		// 표준 JSON 형식으로 메시지 전송
			// 		webSocketClientRef.current.send({
			// 			type: "AWS_SERVICE_LIST_ALL",
			// 			content: {
			// 				region: "ap-northeast-2"
			// 			}
			// 		});
			// 	}
			// }, 2000);
		}
	};	// 비밀번호 검증 함수
	const verifyPassword = () => {
		if (password.trim() === '') {
			setPasswordError(t('password.error.empty', '비밀번호를 입력해주세요.'));
			return;
		}
		
		// 소켓을 통한 검증
		if (webSocketClientRef.current && webSocketClientRef.current.getConnectionStatus()) {
			// 소켓이 연결된 경우 서버로 검증 요청
			webSocketClientRef.current.send({
				type: "VERIFY_PASSWORD",
				content: {
					password: password
				}
			});
			
			// 요청을 보낸 후 로딩 상태 표시를 할 수 있음
			setPasswordError(t('password.verifying', '비밀번호 확인 중...'));
		} else {
			// 소켓 연결이 필요하다는 메시지 표시 (연결 재시도 추가)
			setPasswordError(t('password.error.connectionRequired', '서버 연결이 필요합니다. 연결 중입니다...'));
			
			// 연결 재시도
			handleReconnect();
			
			// 3초 후에 연결 상태 다시 확인
			setTimeout(() => {
				if (webSocketClientRef.current && webSocketClientRef.current.getConnectionStatus()) {
					// 연결되었으면 비밀번호 확인 다시 시도
					setPasswordError(null);
				} else {
					// 여전히 연결되지 않았으면 오류 메시지 업데이트
					setPasswordError(t('password.error.connectionFailed', '서버에 연결할 수 없습니다. 트래커 애플리케이션이 실행 중인지 확인하세요.'));
				}
			}, 3000);
		}
	};
		// 신규 비밀번호 설정 함수
	const createPassword = () => {
		// 입력 값 검증
		if (newPassword.trim() === '') {
			setPasswordError(t('password.error.empty', '비밀번호를 입력해주세요.'));
			return;
		}
		
		if (newPassword !== confirmPassword) {
			setPasswordError(t('password.error.mismatch', '비밀번호가 일치하지 않습니다.'));
			return;
		}
		
		// 비밀번호 복잡성 검증 (최소 6자 이상)
		if (newPassword.length < 6) {
			setPasswordError(t('password.error.tooShort', '비밀번호는 최소 6자 이상이어야 합니다.'));
			return;
		}
		
		// 소켓을 통한 비밀번호 설정
		if (webSocketClientRef.current && webSocketClientRef.current.getConnectionStatus()) {
			webSocketClientRef.current.send({
				type: "CREATE_PASSWORD",
				content: {
					password: newPassword
				}
			});
			
			// 요청을 보낸 후 로딩 상태 표시
			setPasswordError(t('password.creating', '비밀번호 설정 중...'));
		} else {
			// 소켓 연결이 필요하다는 메시지 표시 (연결 재시도 추가)
			setPasswordError(t('password.error.connectionRequired', '서버 연결이 필요합니다. 연결 중입니다...'));
			
			// 연결 재시도
			handleReconnect();
			
			// 3초 후에 연결 상태 다시 확인
			setTimeout(() => {
				if (webSocketClientRef.current && webSocketClientRef.current.getConnectionStatus()) {
					// 연결되었으면 비밀번호 확인 다시 시도
					setPasswordError(null);
				} else {
					// 여전히 연결되지 않았으면 오류 메시지 업데이트
					setPasswordError(t('password.error.connectionFailed', '서버에 연결할 수 없습니다. 트래커 애플리케이션이 실행 중인지 확인하세요.'));
				}
			}, 3000);
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



	// Mobile menu toggle function
	const toggleMobileMenu = () => {
		setIsMobileMenuOpen(!isMobileMenuOpen);
	};	// 로그아웃 함수
	const handleLogout = () => {
		setIsAuthenticated(false);
		setAuthKey(null);
		sessionStorage.removeItem('authKey');
		
		// 서버에 로그아웃 알림 (필요한 경우)
		if (webSocketClientRef.current && webSocketClientRef.current.getConnectionStatus()) {
			webSocketClientRef.current.send({
				type: "LOGOUT"
			});
		}
	};
	
	// 헤더에 로그아웃 버튼 텍스트 번역 추가
	const logout = t('header.logout', '로그아웃');
	// 개발 환경에서 임시 인증 처리 (테스트 목적) - 실제 서버 구현 시 제거 필요
	const handleDevAuth = () => {
		// 임시 인증 키 생성 (실제 서버 구현에서는 서버에서 발급)
		const tempAuthKey = 'dev-temp-auth-key-' + new Date().getTime();
		
		// 개발 환경에서 인증 상태 임시 설정
		if (isInitialSetup) {
			// 비밀번호 설정 성공 시뮬레이션
			setIsAuthenticated(true);
			setIsInitialSetup(false);
			setAuthKey(tempAuthKey);
			// 세션 스토리지에 저장 (새로고침 시에도 유지)
			sessionStorage.setItem('authKey', tempAuthKey);
			console.log('개발 환경: 비밀번호 설정 성공 시뮬레이션');
			setPasswordError(null); // 오류 메시지 초기화
		} else {
			// 비밀번호 검증 성공 시뮬레이션
			setIsAuthenticated(true);
			setAuthKey(tempAuthKey);
			// 세션 스토리지에 저장 (새로고침 시에도 유지)
			sessionStorage.setItem('authKey', tempAuthKey);
			console.log('개발 환경: 비밀번호 검증 성공 시뮬레이션');
			setPasswordError(null); // 오류 메시지 초기화
		}
		
		// 콘솔 메시지에 로그 추가
		setSocketMessages(prev => [...prev, {
			type: 'DEV_AUTH',
			content: {
				action: isInitialSetup ? 'create_password' : 'verify_password',
				timestamp: new Date().toISOString(),
				note: '개발 환경에서의 임시 인증'
			},
			timestamp: new Date().toISOString()
		}]);
	};
		// 개발 환경에서 비밀번호 설정 상태 토글 (테스트 목적) - 실제 서버 구현 시 제거 필요
	const toggleInitialSetup = () => {
		setIsInitialSetup(!isInitialSetup);
		// 화면 전환 시 상태 초기화
		setPassword('');
		setNewPassword('');
		setConfirmPassword('');
		setPasswordError(null);
		
		// 콘솔에 로그 기록
		console.log(`개발 환경: 비밀번호 설정 상태 변경 - ${!isInitialSetup ? '초기 설정 필요' : '이미 설정됨'}`);
		
		// 콘솔 메시지에도 기록
		setSocketMessages(prev => [...prev, {
			type: 'DEV_MODE',
			content: {
				action: 'toggle_setup_mode',
				mode: !isInitialSetup ? 'setup' : 'login',
				timestamp: new Date().toISOString()
			},
			timestamp: new Date().toISOString()
		}]);
	};
	
	// 개발 환경에서 바로 대시보드로 이동 (테스트 목적) - 실제 서버 구현 시 제거 필요
	const goToDashboardDirectly = () => {
		// 임시 인증 키 생성 (실제 서버 구현에서는 서버에서 발급)
		const tempAuthKey = 'dev-direct-auth-key-' + new Date().getTime();
		
		// 인증 상태 즉시 설정
		setIsAuthenticated(true);
		setAuthKey(tempAuthKey);
		
		// 세션 스토리지에 저장 (새로고침 시에도 유지)
		sessionStorage.setItem('authKey', tempAuthKey);
		
		// 콘솔에 로그 기록
		console.log('개발 환경: 대시보드 바로 이동');
		
		// 콘솔 메시지에도 기록
		setSocketMessages(prev => [...prev, {
			type: 'DEV_DIRECT_ACCESS',
			content: {
				action: 'direct_dashboard_access',
				timestamp: new Date().toISOString(),
				note: '개발 환경에서의 대시보드 직접 접근'
			},
			timestamp: new Date().toISOString()
		}]);
	};

	return (
		<>
			<div className="dashboard-container">				<header className="dashboard-header">
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
							</button>							{isAuthenticated && (
								<button className="logout-button" onClick={handleLogout}>
									{t('header.logout', '로그아웃')}
								</button>
							)}
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
				)}				{/* 비밀번호 입력 또는 설정 화면 - 인증되지 않았을 때만 표시 */}
				{!isAuthenticated && (
					<div className="password-container">
						<div className="password-content">
							{isInitialSetup ? (
								// 최초 비밀번호 설정 화면
								<>
									<h3>{t('password.setup.title', '비밀번호 설정')}</h3>
									<p>{t('password.setup.description', '대시보드 접근을 위한 비밀번호를 설정하세요.')}</p>
									<div className="password-setup-form">
										<div className="password-input-row">
											<label htmlFor="new-password">{t('password.setup.new', '새 비밀번호')}</label>
											<input 
												id="new-password"
												type="password"
												className="password-input"
												value={newPassword}
												onChange={(e) => setNewPassword(e.target.value)}
												placeholder={t('password.setup.newPlaceholder', '새 비밀번호 입력 (6자 이상)')}
											/>
										</div>
										<div className="password-input-row">
											<label htmlFor="confirm-password">{t('password.setup.confirm', '비밀번호 확인')}</label>
											<input 
												id="confirm-password"
												type="password"
												className="password-input"
												value={confirmPassword}
												onChange={(e) => setConfirmPassword(e.target.value)}
												placeholder={t('password.setup.confirmPlaceholder', '비밀번호 재입력')}
												onKeyPress={(e) => e.key === 'Enter' && createPassword()}
											/>
										</div>
										<button 
											className="password-submit-button"
											onClick={createPassword}
										>
											{t('password.setup.submit', '비밀번호 설정')}
										</button>										{passwordError && <p className="password-error">{passwordError}</p>}
										
										{/* 개발 도구 - 서버 연결 상태에 따라 표시 여부 결정 */}
										{connectionStatus === 'connected' && (
											<div className="dev-tools">
												<div className="dev-buttons">
													<button 
														className="dev-toggle-button"
														onClick={toggleInitialSetup}
													>
														화면 전환 ({isInitialSetup ? '로그인 화면으로' : '초기 설정 화면으로'})
													</button>
												</div>
											</div>
										)}
									</div>
								</>
							) : (
								// 기존 비밀번호 입력 화면
								<>
									<h3>{t('password.title', '접근 비밀번호')}</h3>
									<p>{t('password.description', '대시보드에 접근하려면 비밀번호를 입력하세요.')}</p>
									<div className="password-input-group">
										<input 
											type="password"
											className="password-input"
											value={password}
											onChange={(e) => setPassword(e.target.value)}
											placeholder={t('password.placeholder', '비밀번호 입력')}
											onKeyPress={(e) => e.key === 'Enter' && verifyPassword()}
										/>
										<button 
											className="password-submit-button"
											onClick={verifyPassword}
										>
											{t('password.submit', '확인')}
										</button>
									</div>									{passwordError && <p className="password-error">{passwordError}</p>}
									
									{/* 개발용 대시보드 바로가기 버튼 - 서버 연결 상태에 따라 표시 */}

									<button 
										onClick={goToDashboardDirectly}
										style={{
											marginTop: '15px',
											padding: '10px 16px',
											backgroundColor: '#FF5722',
											color: 'white',
											border: 'none',
											borderRadius: '4px',
											cursor: 'pointer',
											fontWeight: 'bold',
											width: '100%'
										}}
									>
										개발용 대시보드 바로가기 (비인증 상태에서)
									</button>
					
									
									{/* 서버 연결 상태 */}
									<div className="connection-info">
										<span>서버 상태: <strong className={connectionStatus}>{connectionStatus === 'connected' ? '연결됨' : connectionStatus === 'connecting' ? '연결 중...' : '연결 안됨'}</strong></span>
										{connectionStatus !== 'connected' && (
											<button className="connection-retry-button" onClick={handleReconnect}>
												재연결 시도
											</button>
										)}
									</div>
									
									{/* 개발 도구 - 서버 연결 상태에 따라 표시 여부 결정 */}
									{connectionStatus === 'connected' && (
										<div className="dev-tools">
											<div className="dev-buttons">
												<button 
													className="dev-toggle-button"
													onClick={toggleInitialSetup}
												>
													화면 전환 ({isInitialSetup ? '로그인 화면으로' : '초기 설정 화면으로'})
												</button>
											</div>
										</div>
									)}
								</>
							)}
						</div>
					</div>
				)}

				{/* 메인 대시보드 콘텐츠 - 인증된 경우에만 표시 */}
				{isAuthenticated && (
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
								onStartInstance={handleStartEC2Instance}
								onStopInstance={handleStopEC2Instance}
								isConnected={connectionStatus === 'connected'}
								webSocketClient={webSocketClientRef.current || undefined}
							/>
							<ECSClusters 
								clusters={ecsClusters} 
								isConnected={connectionStatus === 'connected'} 
								webSocketClient={webSocketClientRef.current || undefined}
							/>
							<EKSClusters 
								clusters={eksClusters} 
								isConnected={connectionStatus === 'connected'} 
								webSocketClient={webSocketClientRef.current || undefined}
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
				)}

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
