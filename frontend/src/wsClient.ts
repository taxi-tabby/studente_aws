import * as WebSocket from 'ws';
import * as http from 'http';
import * as crypto from 'crypto';

export class WebSocketClient {
  private socket: WebSocket | null = null;
  private readonly url: string;
  private readonly port: number;
  private reconnectInterval: number = 2000;
  private reconnectTimeout: NodeJS.Timeout | null = null;
  private onMessageCallback: (message: any) => void;
  private isConnecting: boolean = false;
  private connectionAttempts: number = 0;
  private maxReconnectAttempts: number = 10;
  private heartbeatInterval: NodeJS.Timeout | null = null;
  private forceClosing: boolean = false;

  constructor(port: number = 20201, onMessage: (message: any) => void) {
    this.url = `ws://127.0.0.1:${port}`;
    this.port = port;
    this.onMessageCallback = onMessage;
  }

  public connect(): void {
    if (this.socket && (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING)) {
      console.log('WebSocket already connected or connecting');
      return;
    }

    if (this.isConnecting) {
      return;
    }

    this.isConnecting = true;
    this.connectionAttempts++;
    this.forceClosing = false;

    if (this.connectionAttempts > this.maxReconnectAttempts) {
      console.log(`Maximum connection attempts (${this.maxReconnectAttempts}) reached. Giving up.`);
      this.isConnecting = false;
      return;
    }

    console.log(`Attempting to connect to WebSocket server (attempt ${this.connectionAttempts}/${this.maxReconnectAttempts})...`);

    try {
      // 더 안정적인 WebSocket 연결을 위한 설정
      const key = this.generateRFC6455WebSocketKey();
      const options = {
        headers: {
          'Connection': 'Upgrade',
          'Upgrade': 'websocket',
          'Host': '127.0.0.1:' + this.port,
          'Sec-WebSocket-Version': '13',
          'Sec-WebSocket-Key': key,
          'User-Agent': 'NodeClient/1.0'
        },
        handshakeTimeout: 5000, // 핸드셰이크 타임아웃 5초
        perMessageDeflate: false, // 압축 비활성화
        followRedirects: true // 리다이렉트 따르기
      };

      this.socket = new WebSocket(this.url, options);

      this.socket.on('open', () => {
        console.log('✓ WebSocket connection established successfully');
        this.isConnecting = false;
        this.connectionAttempts = 0; // 성공적인 연결 시 시도 카운터 리셋
        
        // 기존 재연결 타이머 취소
        if (this.reconnectTimeout) {
          clearTimeout(this.reconnectTimeout);
          this.reconnectTimeout = null;
        }

        // 핑/퐁 하트비트 설정
        this.startHeartbeat();
      });

      this.socket.on('message', (data: WebSocket.Data) => {
        try {
          let message: string;
          
          if (data instanceof Buffer) {
            message = data.toString('utf8');
          } else if (typeof data === 'string') {
            message = data;
          } else {
            // 다른 유형의 데이터 처리
            message = String(data);
          }

          console.log(`WebSocket message received: ${message.substring(0, 100)}${message.length > 100 ? '...' : ''}`);
          
          let parsedData;
          try {
            parsedData = JSON.parse(message);
          } catch (e) {
            // JSON이 아닌 경우 문자열로 처리
            parsedData = message;
          }
          
          this.onMessageCallback(parsedData);
        } catch (error) {
          console.error('Error processing WebSocket message:', error);
        }
      });

      this.socket.on('pong', () => {
        // 서버로부터 퐁 응답 수신
        console.log('Received pong from server');
      });

      this.socket.on('close', (code, reason) => {
        console.log(`WebSocket connection closed with code ${code}${reason ? ': ' + reason : ''}`);
        this.isConnecting = false;
        this.socket = null;
        
        // 하트비트 중지
        this.stopHeartbeat();
        
        // 강제 종료가 아니면 재연결 시도
        if (!this.forceClosing) {
          this.scheduleReconnect();
        }
      });

      this.socket.on('error', (err) => {
        console.error(`WebSocket error: ${err.message}`);
        this.isConnecting = false;
        
        if (this.socket) {
          try {
            this.socket.terminate(); // 강제 종료
          } catch (e) {
            // 에러 무시
          }
          this.socket = null;
        }
        
        // 하트비트 중지
        this.stopHeartbeat();
        
        // 강제 종료가 아니면 재연결 시도
        if (!this.forceClosing) {
          this.scheduleReconnect();
        }
      });

    } catch (error) {
      console.error('Failed to connect to WebSocket server:', error);
      this.isConnecting = false;
      
      // 강제 종료가 아니면 재연결 시도
      if (!this.forceClosing) {
        this.scheduleReconnect();
      }
    }
  }

  private startHeartbeat(): void {
    // 이미 실행 중인 하트비트가 있으면 중지
    this.stopHeartbeat();
    
    // 30초마다 ping 보내기
    this.heartbeatInterval = setInterval(() => {
      if (this.socket && this.socket.readyState === WebSocket.OPEN) {
        try {
          this.socket.ping();
          console.log('Ping sent to server');
        } catch (e) {
          console.error('Failed to send ping:', e);
        }
      }
    }, 30000);
  }

  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  private generateRFC6455WebSocketKey(): string {
    // RFC6455 규격에 맞는 WebSocket 키 생성
    return crypto.randomBytes(16).toString('base64');
  }

  private scheduleReconnect(): void {
    if (!this.reconnectTimeout && !this.forceClosing) {
      // 지수 백오프를 사용하여 재연결
      const delay = Math.min(30000, this.reconnectInterval * Math.pow(1.5, this.connectionAttempts - 1));
      console.log(`Scheduling WebSocket reconnect in ${delay}ms (attempt ${this.connectionAttempts}/${this.maxReconnectAttempts})`);
      
      this.reconnectTimeout = setTimeout(() => {
        this.reconnectTimeout = null;
        this.connect();
      }, delay);
    }
  }

  public disconnect(): void {
    this.forceClosing = true;
    
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
    
    this.stopHeartbeat();

    if (this.socket) {
      try {
        this.socket.terminate(); // 강제 종료로 빠르게 연결 닫기
      } catch (e) {
        console.error('Error terminating WebSocket connection:', e);
      }
      this.socket = null;
    }
    
    // 연결 상태 초기화
    this.isConnecting = false;
    this.connectionAttempts = 0;
    console.log('WebSocket client disconnected');
  }

  public send(message: string | object): boolean {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
      console.error('Cannot send message: WebSocket is not connected');
      if (!this.isConnecting && !this.forceClosing) {
        this.connect(); // 연결 시도
      }
      return false;
    }

    try {
      const messageStr = typeof message === 'string' ? message : JSON.stringify(message);
      this.socket.send(messageStr);
      return true;
    } catch (error) {
      console.error('Failed to send WebSocket message:', error);
      return false;
    }
  }

  public isConnected(): boolean {
    return !!this.socket && this.socket.readyState === WebSocket.OPEN;
  }
}