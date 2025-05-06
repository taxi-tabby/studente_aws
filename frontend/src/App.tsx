import { useState, useEffect, useRef } from 'react'
import './App.css'
import { WebSocketClient } from './utils/WebSocketClient'
import ActivityMonitor from './components/ActivityMonitor'
import EC2Instances from './components/EC2Instances'
import ECSClusters from './components/ECSClusters'
import EKSClusters from './components/EKSClusters'
import WebSocketConsole from './components/WebSocketConsole'
import type { EC2Instance, ECSCluster, EKSCluster, ActivityStatus, WebSocketMessage } from './types/aws'

function App() {
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
	const [connectionStatus, setConnectionStatus] = useState<string>('Disconnected');
	const [socketMessages, setSocketMessages] = useState<WebSocketMessage[]>([]);

	// Mock data for development if WebSocket is not connected
	const [useMockData, setUseMockData] = useState<boolean>(false);

	// Reference to WebSocketClient instance
	const webSocketClientRef = useRef<WebSocketClient | null>(null);

	// WebSocket port - 백엔드 서버 포트와 일치하도록 수정
	const WEBSOCKET_PORT = 20201; 

	// Maximum number of socket messages to store
	const MAX_MESSAGES = 500;

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
	};

	useEffect(() => {
		// 초기 화면 표시를 위해 즉시 샘플 데이터 로드
		loadMockData();
		
		// Create a WebSocket client instance
		const webSocketClient = new WebSocketClient(
			WEBSOCKET_PORT,
			handleWebSocketMessage,
			"localhost" // 호스트 명시적으로 설정
		);
		
		// Store the client in ref for later use
		webSocketClientRef.current = webSocketClient;
		
		// Connect to the WebSocket server
		webSocketClient.connect();
		setConnectionStatus('Connecting...');

		// WebSocket 연결 상태 주기적 체크
		const connectionCheck = setInterval(() => {
			// getConnectionStatus 메서드를 통해 연결 상태 확인
			if (webSocketClientRef.current && webSocketClientRef.current.getConnectionStatus()) {
				setConnectionStatus('Connected');
				clearInterval(connectionCheck);
			}
		}, 1000);

		// 서버에 연결되면 실제 데이터 요청
		const requestDataInterval = setInterval(() => {
			// getConnectionStatus 메서드를 통해 연결 상태 확인
			if (webSocketClientRef.current && webSocketClientRef.current.getConnectionStatus()) {
				// 연결되었으면 실제 데이터 요청
				// webSocketClientRef.current.send({
				// 	action: "getAll"
				// });

				clearInterval(requestDataInterval);
			}
		}, 2000);

		// Clean up the WebSocket connection on component unmount
		return () => {
			webSocketClient.disconnect();
			clearInterval(connectionCheck);
			clearInterval(requestDataInterval);
		};
	}, []);

	// Handle messages received from WebSocket
	const handleWebSocketMessage = (message: WebSocketMessage) => {
		console.log("WebSocket 메시지 수신:", message);
		setConnectionStatus('Connected');
		
		// Add the message to the console messages
		setSocketMessages(prevMessages => {
			// Add new message and limit to MAX_MESSAGES by removing old ones
			const updatedMessages = [...prevMessages, message];
			return updatedMessages.slice(Math.max(0, updatedMessages.length - MAX_MESSAGES));
		});
		
		// 서비스 타입에 따라 적절한 데이터 처리
		if (message.service === "ec2" && message.instances) {
			setEC2Instances(message.instances);
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
			
			// 활동 유형에 따라 상태 업데이트
			const activityUpdate: Partial<ActivityStatus> = {
				keyboard: activityType === "KEYBOARD_ACTIVITY" ? true : false,
				mouseMovement: activityType === "MOUSE_MOVEMENT" ? true : false,
				mouseClick: activityType === "MOUSE_CLICK" ? true : false
			};
			
			// 활동 상태 업데이트
			setActivityStatus(prev => ({
				...prev,
				...activityUpdate
			}));
			
			// 깜빡임 효과를 위해 잠시 후 상태 초기화
			setTimeout(() => {
				setActivityStatus(prev => ({
					...prev,
					keyboard: false,
					mouseMovement: false,
					mouseClick: false
				}));
			}, 1000);
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
						
						// 깜빡임 효과를 위해 잠시 후 상태 초기화
						setTimeout(() => {
							setActivityStatus(prev => ({
								...prev,
								keyboard: false,
								mouseMovement: false,
								mouseClick: false
							}));
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
			setConnectionStatus('Connecting...');
			webSocketClientRef.current.connect();
			
			// 연결 후 데이터 요청
			setTimeout(() => {
				// getConnectionStatus 메서드를 통해 연결 상태 확인
				if (webSocketClientRef.current && webSocketClientRef.current.getConnectionStatus()) {
					webSocketClientRef.current.send({
						action: "getAll"
					});
				}
			}, 2000);
		}
	};

	// 데이터 새로고침
	const handleRefreshData = () => {
		// getConnectionStatus 메서드를 통해 연결 상태 확인
		if (webSocketClientRef.current && webSocketClientRef.current.getConnectionStatus()) {
			webSocketClientRef.current.send({
				action: "getAll"
			});
		} else {
			// 연결이 안되어 있으면 샘플 데이터 새로고침
			loadMockData();
		}
	};

	// 서비스별 개별 데이터 새로고침
	const handleRefreshEC2 = () => {
		if (webSocketClientRef.current && webSocketClientRef.current.getConnectionStatus()) {
			webSocketClientRef.current.send({
				action: "getEC2Instances"
			});
		} else {
			// Mock data - empty for now
			setEC2Instances([]);
		}
	};

	const handleRefreshECS = () => {
		if (webSocketClientRef.current && webSocketClientRef.current.getConnectionStatus()) {
			webSocketClientRef.current.send({
				action: "getECSClusters"
			});
		} else {
			// Mock data - empty for now
			setECSClusters([]);
		}
	};

	const handleRefreshEKS = () => {
		if (webSocketClientRef.current && webSocketClientRef.current.getConnectionStatus()) {
			webSocketClientRef.current.send({
				action: "getEKSClusters"
			});
		} else {
			// Mock data - empty for now
			setEKSClusters([]);
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

	return (
		<>
			<div className="dashboard-container">
				<header className="dashboard-header">
					<h1>Studente AWS</h1>
					<div className="header-controls">
						<button className="refresh-button" onClick={handleRefreshData}>
							새로고침
						</button>
						<div className={`connection-status ${connectionStatus.toLowerCase().replace('...', '')}`}>
							{connectionStatus}
						</div>
						{connectionStatus === 'Disconnected' && (
							<button className="retry-button" onClick={handleReconnect}>
								재연결
							</button>
						)}
					</div>
				</header>

				<main className="dashboard-content">
					<ActivityMonitor activityStatus={activityStatus} />

					<div className="aws-services">
						<EC2Instances instances={ec2Instances} onRefresh={handleRefreshEC2} />
						<ECSClusters clusters={ecsClusters} onRefresh={handleRefreshECS} />
						<EKSClusters clusters={eksClusters} onRefresh={handleRefreshEKS} />
					</div>
					
					<div className="console-section">
						<div className="console-header">
							<h2>WebSocket Messages</h2>
							<button className="clear-console-button" onClick={clearSocketMessages}>
								Clear Console
							</button>
						</div>
						<WebSocketConsole messages={socketMessages} />
					</div>
				</main>

				<footer className="dashboard-footer">
					<p>Studente AWS &copy; {new Date().getFullYear()} by <i>rkdmf0000@gmail.com</i></p>
				</footer>
			</div>
		</>
	)
}

export default App
