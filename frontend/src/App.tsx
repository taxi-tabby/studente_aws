import { useState, useEffect, useRef } from 'react'
import './App.css'
import { WebSocketClient } from './utils/WebSocketClient'
import ActivityMonitor from './components/ActivityMonitor'
import EC2Instances from './components/EC2Instances'
import ECSClusters from './components/ECSClusters'
import EKSClusters from './components/EKSClusters'
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

	// Mock data for development if WebSocket is not connected
	const [useMockData, setUseMockData] = useState<boolean>(false);

	// Reference to WebSocketClient instance
	const webSocketClientRef = useRef<WebSocketClient | null>(null);

	// WebSocket port - 백엔드 서버 포트와 일치하도록 수정
	const WEBSOCKET_PORT = 20201; 

	// 초기 화면 로딩을 위한 샘플 데이터 설정
	const loadMockData = () => {
		// Mock EC2 data
		setEC2Instances([
			{
				id: 'i-12345678',
				name: 'Web Server',
				state: 'running',
				type: 't3.micro',
				zone: 'us-east-1a'
			},
			{
				id: 'i-87654321',
				name: 'Database Server',
				state: 'stopped',
				type: 't3.large',
				zone: 'us-east-1b'
			},
			{
				id: 'i-11223344',
				name: 'API Server',
				state: 'pending',
				type: 't3.medium',
				zone: 'us-east-1c'
			}
		]);

		// Mock ECS data
		setECSClusters([
			{
				name: 'Production Cluster',
				status: 'active',
				activeServices: 5,
				runningTasks: 12,
				pendingTasks: 0
			},
			{
				name: 'Development Cluster',
				status: 'active',
				activeServices: 3,
				runningTasks: 4,
				pendingTasks: 2
			}
		]);

		// Mock EKS data
		setEKSClusters([
			{
				name: 'Main-EKS-Cluster',
				status: 'active',
				version: '1.27',
				endpoint: 'https://A1B2C3D4E5F6G7H8I9J0.gr7.us-east-1.eks.amazonaws.com'
			}
		]);

		// Mock activity data
		setActivityStatus({
			keyboard: true,
			mouseMovement: true,
			mouseClick: false,
			screen: true,
			audio: false,
			activeWindow: 'Visual Studio Code'
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
					setActivityStatus(prev => ({...prev, ...content.activity}));
				}
			}
		}
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
			handleUseMockData();
		}
	};

	// Load mock data if button is clicked
	const handleUseMockData = () => {
		setUseMockData(true);
		loadMockData();
	};

	return (
		<>
			<div className="dashboard-container">
				<header className="dashboard-header">
					<h1>AWS Monitoring Dashboard</h1>
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
						<EC2Instances instances={ec2Instances} />
						<ECSClusters clusters={ecsClusters} />
						<EKSClusters clusters={eksClusters} />
					</div>
				</main>

				<footer className="dashboard-footer">
					<p>AWS Monitor &copy; {new Date().getFullYear()}</p>
				</footer>
			</div>
		</>
	)
}

export default App
