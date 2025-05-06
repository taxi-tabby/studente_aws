import * as net from 'net';

export class TcpClient {
	private client: net.Socket | null = null;
	private readonly port: number = 20200;
	private readonly host: string = '127.0.0.1';
	private onMessageCallback: (message: any) => void;
	private reconnectInterval: number = 3000;
	private reconnectTimeout: NodeJS.Timeout | null = null;
	private isConnecting: boolean = false;
	private buffer: string = '';
	private connectionAttempts: number = 0;
	private maxReconnectAttempts: number = 5;
	private reconnectBackoff: boolean = true;
	private autoReconnect: boolean = true;

	constructor(onMessage: (message: any) => void) {
		this.onMessageCallback = onMessage;
	}

	public connect(): boolean {
		// 이미 연결 시도 중이면 중복 시도 방지
		if (this.isConnecting) {
			console.log('TCP client connection already in progress, ignoring connect request');
			return false;
		}

		// 이미 연결되어 있으면 중복 연결 방지
		if (this.client && !this.client.destroyed) {
			console.log('TCP client already connected, ignoring connect request');
			return true;
		}

		// 연결 대기 타이머가 있으면 중복 시도 방지
		if (this.reconnectTimeout) {
			console.log('TCP reconnection already scheduled, ignoring connect request');
			return false;
		}

		this.isConnecting = true;
		console.log(`Connecting to TCP server at ${this.host}:${this.port}...`);

		try {
			// 기존 클라이언트 정리
			this.cleanupExistingClient();
			
			this.client = new net.Socket();

			this.client.on('connect', () => {
				console.log(`TCP client connected to ${this.host}:${this.port}`);
				this.isConnecting = false;
				this.connectionAttempts = 0; // 연결 성공 시 시도 횟수 초기화
				this.cancelReconnectTimer(); // 대기 중인 재연결 타이머 취소
			});

			this.client.on('data', (data: Buffer) => {
				try {
					this.buffer += data.toString('utf8');
					this.processBuffer();
				} catch (error) {
					console.error('Error processing TCP message:', error);
				}
			});

			this.client.on('close', () => {
				console.log('TCP connection closed');
				this.handleDisconnect();
			});

			this.client.on('error', (err) => {
				console.error(`TCP client error: ${err.message}`);
				this.handleDisconnect();
			});

			this.client.connect(this.port, this.host);
			return true;
		} catch (error) {
			console.error('Failed to connect to TCP server:', error);
			this.handleDisconnect();
			return false;
		}
	}

	// 클라이언트 정리 및 리소스 해제를 위한 메서드
	private cleanupExistingClient(): void {
		if (this.client) {
			try {
				this.client.removeAllListeners();
				if (!this.client.destroyed) {
					this.client.destroy();
				}
				this.client = null;
			} catch (error) {
				console.error('Error cleaning up TCP client:', error);
			}
		}
	}

	// 연결 해제 처리를 위한 공통 메서드
	private handleDisconnect(): void {
		this.isConnecting = false;
		this.cleanupExistingClient();
		
		// 자동 재연결이 활성화된 경우에만 재연결 시도
		if (this.autoReconnect && !this.reconnectTimeout) {
			this.scheduleReconnect();
		}
	}

	private processBuffer(): void {
		// 각 메시지가 줄바꿈으로 구분된다고 가정
		const messages = this.buffer.split('\n');

		// 마지막 요소가 '\n'으로 끝나지 않으면 불완전한 메시지
		if (messages.length > 0 && this.buffer.endsWith('\n')) {
			this.buffer = ''; // 모든 메시지가 완전하면 버퍼 비우기
		} else if (messages.length > 0) {
			this.buffer = messages.pop() || ''; // 불완전한 메시지는 버퍼에 유지
		}

		messages.forEach(msg => {
			if (msg.trim() === '') return;

			console.log(`TCP message received: ${msg}`);

			let parsedData;
			try {
				parsedData = JSON.parse(msg);
			} catch (e) {
				// JSON이 아니면 문자열로 전달
				parsedData = msg;
			}

			this.onMessageCallback(parsedData);
		});
	}

	private scheduleReconnect(): void {
		// 이미 예약된 재연결이 있으면 중복 예약 방지
		if (this.reconnectTimeout) {
			console.log('Reconnect already scheduled, skipping');
			return;
		}

		this.connectionAttempts++;
		
		// 최대 재시도 횟수 확인
		if (this.connectionAttempts > this.maxReconnectAttempts) {
			console.log(`Maximum reconnection attempts (${this.maxReconnectAttempts}) reached. Giving up.`);
			return;
		}

		// 지수 백오프 적용
		let delay = this.reconnectInterval;
		if (this.reconnectBackoff) {
			delay = Math.min(30000, this.reconnectInterval * Math.pow(1.5, this.connectionAttempts - 1));
		}

		console.log(`Scheduling TCP reconnect in ${delay}ms (attempt ${this.connectionAttempts}/${this.maxReconnectAttempts})`);
		
		this.reconnectTimeout = setTimeout(() => {
			this.reconnectTimeout = null;
			// 재연결 시도할 때 중복 타이머 방지
			if (!this.isConnecting) {
				this.connect();
			}
		}, delay);
	}

	private cancelReconnectTimer(): void {
		if (this.reconnectTimeout) {
			clearTimeout(this.reconnectTimeout);
			this.reconnectTimeout = null;
			console.log('Cancelled pending reconnect timer');
		}
	}

	public disconnect(): void {
		// 자동 재연결 비활성화
		this.autoReconnect = false;
		
		// 대기 중인 재연결 타이머 취소
		this.cancelReconnectTimer();
		
		// 클라이언트 정리
		this.cleanupExistingClient();
		
		console.log('TCP client disconnected and auto-reconnect disabled');
	}

	public send(message: string | object): boolean {
		if (!this.client || this.client.destroyed) {
			console.error('Cannot send message: TCP client is not connected');
			
			// 이미 연결 시도 중이 아니면 재연결 시도
			if (!this.isConnecting && !this.reconnectTimeout) {
				console.log('Attempting to reconnect before sending message');
				this.connect();
			}
			
			return false;
		}

		try {
			const messageStr = typeof message === 'string' ? message : JSON.stringify(message);
			this.client.write(messageStr + '\n'); // 메시지 구분자로 줄바꿈 추가
			return true;
		} catch (error) {
			console.error('Failed to send TCP message:', error);
			return false;
		}
	}

	public isConnected(): boolean {
		return !!this.client && !this.client.destroyed;
	}
	
	// 자동 재연결 활성화/비활성화 메서드
	public setAutoReconnect(enable: boolean): void {
		this.autoReconnect = enable;
	}
}