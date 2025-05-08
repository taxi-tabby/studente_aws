/**
 * WebSocket 연결을 관리하는 클래스
 */
import { WS_CONFIG } from '../constants/socketTypes';

export class WebSocketConnection {
  public socket: WebSocket | null = null;
  private reconnectTimer: number | null = null;
  private readonly url: string;
  private readonly messageHandler: (message: any) => void;
  private _isConnected: boolean = false;
  private isConnecting: boolean = false;
  private reconnectAttempts: number = 0;
  private readonly maxReconnectAttempts: number = WS_CONFIG.MAX_RECONNECT_ATTEMPTS;
  private readonly reconnectInterval: number = WS_CONFIG.RECONNECT_INTERVAL;
  private reconnectBackoff: boolean = true;
  private autoReconnect: boolean = true;
  private disconnectCallback: (() => void) | null = null;
  private connectionCheckTimer: number | null = null;
  private pingInterval: number | null = null;

  /**
   * WebSocket 연결 관리자 생성
   * @param port WebSocket 서버 포트
   * @param messageHandler 메시지 수신 핸들러
   * @param hostname 서버 호스트 이름
   */
  constructor(port: number, messageHandler: (message: any) => void, hostname: string = 'localhost') {
    this.url = `ws://${hostname}:${port}/ws`;
    this.messageHandler = messageHandler;
  }

  /**
   * 연결 끊김 이벤트 콜백 설정
   * @param callback 콜백 함수
   */
  public setDisconnectCallback(callback: () => void): void {
    this.disconnectCallback = callback;
  }

  /**
   * WebSocket 연결 시도
   */
  public connect(): void {
    if (this.isConnecting || 
       (this.socket && this.socket.readyState === WebSocket.OPEN) || 
       this.reconnectTimer) {
      console.log('WebSocket 연결이 이미 진행 중이거나 완료되었습니다');
      return;
    }

    this.isConnecting = true;
    console.log(`WebSocket 연결 시도: ${this.url}`);

    try {
      this.cleanupExistingSocket();
      
      this.socket = new WebSocket(this.url);

      this.socket.onopen = () => {
        console.log('WebSocket 연결 성공');
        this._isConnected = true;
        this.isConnecting = false;
        this.reconnectAttempts = 0;
        
        if (this.reconnectTimer) {
          window.clearTimeout(this.reconnectTimer);
          this.reconnectTimer = null;
        }
        
        // 연결 상태 확인을 위한 ping 설정
        this.setupPingInterval();
      };

      this.socket.onmessage = (event) => {
        try {
          if (typeof event.data === 'string') {
            const data = JSON.parse(event.data);
            console.log('WebSocket 메시지 수신:', data);
            this.messageHandler(data);
          } else if (event.data instanceof Blob) {
            const reader = new FileReader();
            reader.onload = () => {
              try {
                if (reader.result) {
                  const data = JSON.parse(reader.result.toString());
                  console.log('WebSocket 바이너리 메시지 수신:', data);
                  this.messageHandler(data);
                }
              } catch (error) {
                console.error('바이너리 WebSocket 메시지 파싱 오류:', error);
              }
            };
            reader.readAsText(event.data);
          }
        } catch (error) {
          console.error('WebSocket 메시지 파싱 오류:', error);
        }
      };

      this.socket.onerror = (error) => {
        console.error('WebSocket 오류 발생:', error);
        this.handleDisconnect();
      };

      this.socket.onclose = (event) => {
        const reason = event.reason || '이유 없음';
        console.log(`WebSocket 연결 종료: 코드=${event.code}, 이유=${reason}`);
        
        if (event.code === 1011) {
          console.warn('서버에서 예상치 못한 오류가 발생했습니다');
        }
        
        this.handleDisconnect();
      };

      // 연결 타임아웃 설정
      this.connectionCheckTimer = window.setTimeout(() => {
        if (this.isConnecting && (!this.socket || this.socket.readyState !== WebSocket.OPEN)) {
          console.log('WebSocket 연결 시간 초과');
          this.handleDisconnect();
        }
      }, WS_CONFIG.CONNECTION_TIMEOUT);

    } catch (error) {
      console.error('WebSocket 생성 실패:', error);
      this.handleDisconnect();
    }
  }

  /**
   * Ping 간격 설정
   * 주기적으로 ping 메시지를 보내 연결을 유지
   */
  private setupPingInterval(): void {
    // 이전 인터벌 정리
    if (this.pingInterval) {
      window.clearInterval(this.pingInterval);
      this.pingInterval = null;
    }

    // 주기적으로 ping 메시지 전송하여 연결 유지
    this.pingInterval = window.setInterval(() => {
      try {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
          this.socket.send(JSON.stringify({ type: 'PING', timestamp: Date.now() }));
        } else {
          console.log('Ping 실패: 연결 끊김');
          this.handleDisconnect();
        }
      } catch (error) {
        console.error('Ping 전송 실패:', error);
        this.handleDisconnect();
      }
    }, WS_CONFIG.PING_INTERVAL);
  }

  /**
   * 기존 소켓 정리
   */
  private cleanupExistingSocket(): void {
    if (this.socket) {
      try {
        this.socket.onopen = null;
        this.socket.onmessage = null;
        this.socket.onerror = null;
        this.socket.onclose = null;
        
        if (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING) {
          this.socket.close();
        }
        this.socket = null;
      } catch (error) {
        console.error('WebSocket 정리 중 오류:', error);
      }
    }
    this._isConnected = false;

    // 타이머 정리
    if (this.connectionCheckTimer) {
      window.clearTimeout(this.connectionCheckTimer);
      this.connectionCheckTimer = null;
    }
    
    if (this.pingInterval) {
      window.clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }

  /**
   * 연결 끊김 처리
   */
  private handleDisconnect(): void {
    this._isConnected = false;
    this.isConnecting = false;
    this.cleanupExistingSocket();
    
    if (this.disconnectCallback) {
      this.disconnectCallback();
    }

    if (this.autoReconnect && !this.reconnectTimer) {
      this.scheduleReconnect();
    }
  }

  /**
   * 재연결 예약
   */
  private scheduleReconnect(): void {
    if (this.reconnectTimer) {
      return;
    }
    
    this.reconnectAttempts++;
    
    if (this.reconnectAttempts > this.maxReconnectAttempts) {
      console.log(`최대 재연결 시도 횟수(${this.maxReconnectAttempts})에 도달했습니다`);
      return;
    }
    
    let delay = this.reconnectInterval;
    if (this.reconnectBackoff) {
      // 지수 백오프 적용 (최대 30초)
      delay = Math.min(30000, this.reconnectInterval * Math.pow(1.5, this.reconnectAttempts - 1));
    }
    
    console.log(`재연결 시도 ${this.reconnectAttempts}번째 예약됨 (${delay}ms 후)`);
    
    this.reconnectTimer = window.setTimeout(() => {
      console.log('재연결 시도 중...');
      this.reconnectTimer = null;
      if (!this.isConnecting) {
        this.connect();
      }
    }, delay);
  }

  /**
   * 재연결 타이머 취소
   */
  private cancelReconnectTimer(): void {
    if (this.reconnectTimer) {
      window.clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  /**
   * 메시지 전송
   * @param data 전송할 데이터
   * @returns 전송 성공 여부
   */
  public send(data: string): boolean {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
      console.error('WebSocket이 연결되지 않았습니다');
      
      if (!this.isConnecting && !this.reconnectTimer) {
        console.log('메시지 전송 전 재연결을 시도합니다');
        this.connect();
      }
      
      return false;
    }

    try {
      this.socket.send(data);
      return true;
    } catch (error) {
      console.error('WebSocket 메시지 전송 오류:', error);
      return false;
    }
  }

  /**
   * WebSocket 연결 해제
   */
  public disconnect(): void {
    this.autoReconnect = false;
    this.cancelReconnectTimer();
    this.cleanupExistingSocket();
    console.log('WebSocket 연결 해제 및 자동 재연결 비활성화');
  }

  /**
   * 연결 상태 확인
   * @returns 연결 상태
   */
  public getConnectionStatus(): boolean {
    return this._isConnected && this.socket !== null && this.socket.readyState === WebSocket.OPEN;
  }
  
  /**
   * 자동 재연결 설정
   * @param enable 활성화 여부
   */
  public setAutoReconnect(enable: boolean): void {
    this.autoReconnect = enable;
    console.log(`WebSocket 자동 재연결 ${enable ? '활성화' : '비활성화'}`);
    
    // 자동 재연결이 활성화되고 현재 연결이 끊긴 상태이면 재연결 시도
    if (enable && !this._isConnected && !this.isConnecting && !this.reconnectTimer) {
      console.log('자동 재연결 활성화로 인한 재연결 시도');
      this.connect();
    }
  }
}