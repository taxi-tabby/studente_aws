import * as express from 'express';
import * as path from 'path';
import * as http from 'http';
import * as net from 'net';
import * as WebSocket from 'ws';
import * as fs from 'fs';

// Create Express server
const app = express();
const port = 3000;
const tcpPort = 20200;
const wsPort = 20201; // WebSocket 서버 포트 업데이트
const tcpHost = '127.0.0.1';

// Add JSON support for API
app.use(express.json());

// Serve static files from webview directory
app.use(express.static(path.join(__dirname, '..', 'webview')));

// Serve HTML development version
app.get('/', (req, res) => {
	// Read the dashboard HTML from the webview folder or generate it
	let html = fs.readFileSync(path.join(__dirname, '..', 'webview', 'dashboard-dev.html'), 'utf8');
	if (!html) {
		html = `<!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <link href="dashboard.css" rel="stylesheet">
      <title>AWS Dashboard (Development)</title>
    </head>
    <body>
      <div class="container">
        <h1>AWS Services Dashboard</h1>
        
        <div class="dashboard-section">
          <h2>EC2 Instances</h2>
          <button class="refresh-btn" data-service="ec2">Refresh EC2</button>
          <div id="ec2-instances" class="service-container">
            <p>Loading EC2 instances...</p>
          </div>
        </div>
        
        <div class="dashboard-section">
          <h2>ECS Clusters</h2>
          <button class="refresh-btn" data-service="ecs">Refresh ECS</button>
          <div id="ecs-clusters" class="service-container">
            <p>Loading ECS clusters...</p>
          </div>
        </div>
        
        <div class="dashboard-section">
          <h2>EKS Clusters</h2>
          <button class="refresh-btn" data-service="eks">Refresh EKS</button>
          <div id="eks-clusters" class="service-container">
            <p>Loading EKS clusters...</p>
          </div>
        </div>
        
        <div class="dashboard-section">
          <h2>Activity Log</h2>
          <div id="activity-log" class="log-container">
            <p>No activity yet</p>
          </div>
        </div>
      </div>
      
      <script src="dashboard.js"></script>
    </body>
    </html>`;
	}

	res.send(html);
});

// TCP client that connects to the TCP server
let tcpClient: net.Socket | null = null;
let tcpBuffer = '';
let isTcpConnected = false;
let isConnecting = false;  // 연결 시도 중인지 추적하는 플래그
let reconnectTimer: NodeJS.Timeout | null = null;  // 재연결 타이머 추적

// WebSocket server to communicate with browser clients
const server = http.createServer(app);
const wss = new WebSocket.Server({ server });
const wsClients: WebSocket[] = [];

// Connect to TCP server
function connectToTcpServer() {
	// 이미 연결 중이거나 타이머가 실행 중이면 중복 연결 방지
	if (isConnecting || isTcpConnected) {
		console.log('TCP connection already in progress or already connected, skipping connection attempt');
		return;
	}

	// 기존 타이머 정리
	if (reconnectTimer) {
		clearTimeout(reconnectTimer);
		reconnectTimer = null;
	}

	isConnecting = true;
	console.log(`Connecting to TCP server at ${tcpHost}:${tcpPort}...`);

	// 기존 클라이언트 정리
	if (tcpClient) {
		tcpClient.removeAllListeners();
		tcpClient.destroy();
		tcpClient = null;
	}

	tcpClient = new net.Socket();

	tcpClient.on('connect', () => {
		console.log('\x1b[32m%s\x1b[0m', `✓ Connected to TCP server at ${tcpHost}:${tcpPort}`);
		isTcpConnected = true;
		isConnecting = false;

		// Notify all WebSocket clients about connection status change
		broadcastToWebSocketClients(JSON.stringify({
			type: 'connection',
			status: 'connected'
		}));
	});

	tcpClient.on('data', (data) => {
		const receivedStr = data.toString('utf8');
		console.log('\x1b[36m%s\x1b[0m', `← Received from TCP server: ${receivedStr}`);

		// Add to buffer and process messages
		tcpBuffer += receivedStr;
		processTcpMessages();
	});

	tcpClient.on('error', (err) => {
		console.log('\x1b[31m%s\x1b[0m', `✗ TCP client error: ${err.message}`);
		isTcpConnected = false;
		isConnecting = false;

		// Notify WebSocket clients
		broadcastToWebSocketClients(JSON.stringify({
			type: 'connection',
			status: 'error',
			message: `TCP connection error: ${err.message}`
		}));

		// 재연결 시도 예약 (중복 방지 추가)
		scheduleReconnect();
	});

	tcpClient.on('close', () => {
		console.log('\x1b[33m%s\x1b[0m', '! TCP connection closed');
		isTcpConnected = false;
		isConnecting = false;

		// Notify WebSocket clients
		broadcastToWebSocketClients(JSON.stringify({
			type: 'connection',
			status: 'disconnected'
		}));

		// 재연결 시도 예약 (중복 방지 추가)
		scheduleReconnect();
	});

	tcpClient.connect(tcpPort, tcpHost);
}

// 재연결 타이머를 한 번만 설정하는 함수
function scheduleReconnect() {
	if (reconnectTimer) {
		console.log('Reconnection already scheduled, skipping');
		return;
	}
	
	console.log('Scheduling TCP reconnect in 5000ms');
	reconnectTimer = setTimeout(() => {
		reconnectTimer = null;
		connectToTcpServer();
	}, 5000);
}

// Process TCP messages and broadcast to WebSocket clients
function processTcpMessages() {
	// Split by newline to get complete messages
	const messages = tcpBuffer.split('\n');

	// Handle incomplete messages
	if (messages.length > 0 && tcpBuffer.endsWith('\n')) {
		tcpBuffer = '';
	} else if (messages.length > 0) {
		tcpBuffer = messages.pop() || '';
	}

	// Process each complete message
	messages.forEach(msg => {
		if (msg.trim() === '') return;

		try {
			console.log('\x1b[36m%s\x1b[0m', `← Processing message: ${msg}`);

			// Parse the message and forward it to WebSocket clients
			const parsedMessage = JSON.parse(msg);

			// Log message details
			console.log('\x1b[32m%s\x1b[0m', '====== TCP 서버 응답 메시지 ======');
			console.log(JSON.stringify(parsedMessage, null, 2));
			console.log('\x1b[32m%s\x1b[0m', '================================');

			// Broadcast the message to all WebSocket clients
			broadcastToWebSocketClients(msg);

		} catch (e) {
			console.error('\x1b[31m%s\x1b[0m', `! Error processing TCP message: ${e}`);
		}
	});
}

// Broadcast message to all WebSocket clients
function broadcastToWebSocketClients(message: string) {
	const disconnectedClients: WebSocket[] = [];

	wsClients.forEach((client, index) => {
		if (client.readyState === WebSocket.OPEN) {
			client.send(message);
		} else {
			disconnectedClients.push(client);
		}
	});

	// Remove disconnected clients
	disconnectedClients.forEach(client => {
		const index = wsClients.indexOf(client);
		if (index !== -1) {
			wsClients.splice(index, 1);
			console.log(`WebSocket client disconnected (${wsClients.length} connected)`);
		}
	});
}

// WebSocket server event handlers
wss.on('connection', (ws) => {
	console.log(`WebSocket client connected (${wsClients.length + 1} connected)`);
	wsClients.push(ws);

	// Send connection status to the newly connected client
	ws.send(JSON.stringify({
		type: 'connection',
		status: isTcpConnected ? 'connected' : 'disconnected'
	}));

	// Handle WebSocket messages from browser
	ws.on('message', (message) => {
		try {
			const msgString = message.toString();
			console.log('\x1b[35m%s\x1b[0m', `← Received from WebSocket client: ${msgString}`);

			// Check if message is valid JSON
			const parsedMsg = JSON.parse(msgString);

			// Forward message to TCP server if connected
			if (isTcpConnected && tcpClient) {
				console.log('\x1b[35m%s\x1b[0m', `→ Forwarding to TCP server: ${msgString}`);
				tcpClient.write(msgString + '\n');
			} else {
				// Send error message back to WebSocket client if TCP server not connected
				ws.send(JSON.stringify({
					type: 'error',
					message: 'TCP server not connected'
				}));
			}
		} catch (e) {
			console.error('\x1b[31m%s\x1b[0m', `! Error processing WebSocket message: ${e}`);
			ws.send(JSON.stringify({
				type: 'error',
				message: `Error processing message: ${e}`
			}));
		}
	});

	ws.on('close', () => {
		const index = wsClients.indexOf(ws);
		if (index !== -1) {
			wsClients.splice(index, 1);
			console.log(`WebSocket client disconnected (${wsClients.length} connected)`);
		}
	});

	ws.on('error', (error) => {
		console.error('\x1b[31m%s\x1b[0m', `! WebSocket client error: ${error}`);
	});
});

// Connect to TCP server on startup
connectToTcpServer();

// Start the server
server.listen(port, () => {
	console.log(`HTTP server running at http://localhost:${port}`);
});

// Add console dashboard for monitoring
console.log('\n=============================================');
console.log('AWS Dashboard Development Server');
console.log('=============================================');
console.log('- Web UI:       http://localhost:3000');
console.log(`- TCP Client:   connected to ${tcpHost}:${tcpPort}`);
console.log(`- WebSocket:    running on ws://localhost:${wsPort}`);
console.log('=============================================\n');