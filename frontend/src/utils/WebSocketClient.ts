// WebSocket 클라이언트 인터페이스 정의
export interface IWebSocketClient {
  connect(): void;
  disconnect(): void;
  send(data: any): void;
  getConnectionStatus(): boolean;
  setAutoReconnect(enable: boolean): void;
  socket: WebSocket | null;
}

export class WebSocketClient implements IWebSocketClient {
  public socket: WebSocket | null = null;
  private reconnectTimer: number | null = null;
  private readonly url: string;
  private readonly messageHandler: (message: any) => void;
  private _isConnected: boolean = false;
  private isConnecting: boolean = false;
  private reconnectAttempts: number = 0;
  private readonly maxReconnectAttempts: number = 10;
  private readonly reconnectInterval: number = 2000;
  private reconnectBackoff: boolean = true;
  private autoReconnect: boolean = true;
  private initialDataRequested: boolean = false;
  private disconnectCallback: (() => void) | null = null; // 연결 끊김 알림을 위한 콜백

  constructor(port: number, messageHandler: (message: any) => void, hostname: string = 'localhost') {
    this.url = `ws://${hostname}:${port}/ws`;
    this.messageHandler = messageHandler;
  }

  // 연결 끊김 콜백 설정 메서드
  public setDisconnectCallback(callback: () => void): void {
    this.disconnectCallback = callback;
  }

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
        
        if (!this.initialDataRequested) {
          this.initialDataRequested = true;
        }
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
    } catch (error) {
      console.error('WebSocket 생성 실패:', error);
      this.handleDisconnect();
    }
  }

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
  }

  private handleDisconnect(): void {
    this._isConnected = false;
    this.isConnecting = false;
    this.initialDataRequested = false;
    this.cleanupExistingSocket();
    
    if (this.disconnectCallback) {
      this.disconnectCallback();
    }

    if (this.autoReconnect && !this.reconnectTimer) {
      this.scheduleReconnect();
    }
  }

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

  private cancelReconnectTimer(): void {
    if (this.reconnectTimer) {
      window.clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  public send(data: any): void {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
      console.error('WebSocket이 연결되지 않았습니다');
      
      if (!this.isConnecting && !this.reconnectTimer) {
        console.log('메시지 전송 전 재연결을 시도합니다');
        this.connect();
      }
      
      return;
    }

    try {
      let messageToSend: any;
      
      // 문자열 메시지 처리 (명령어 형식)
      if (typeof data === 'string') {
        this.socket.send(data);
        console.log('WebSocket 텍스트 명령어 전송:', data);
        return;
      }
      
      // 객체 메시지 처리
      if (typeof data === 'object' && data !== null) {
        // 표준 JSON 메시지 형식 (id, type, timestamp, content)
        if (data.type && typeof data.type === 'string') {
          messageToSend = {
            id: data.id || `req-${Date.now()}`,
            type: data.type,
            timestamp: data.timestamp || Math.floor(Date.now() / 1000),
            source: data.source || 'web-client',
            content: data.content || {}
          };
        }
        // EC2, ECS, EKS 서비스 요청 형식
        else if (data.action && typeof data.action === 'string') {
          // 특정 액션에 따른 메시지 형식 조정
          switch(data.action) {
            case 'getAll':
              messageToSend = {
                id: `req-${Date.now()}`,
                type: 'AWS_SERVICE_LIST_ALL',
                timestamp: Math.floor(Date.now() / 1000),
                source: 'web-client',
                content: {
                  region: data.region || 'ap-northeast-2'
                }
              };
              break;
              
            case 'getEC2Instances':
              messageToSend = {
                id: `req-${Date.now()}`,
                type: 'AWS_EC2_LIST',
                timestamp: Math.floor(Date.now() / 1000),
                source: 'web-client',
                content: {
                  region: data.region || 'ap-northeast-2'
                }
              };
              break;
              
            case 'getECSClusters':
              messageToSend = {
                id: `req-${Date.now()}`,
                type: 'AWS_ECS_LIST',
                timestamp: Math.floor(Date.now() / 1000),
                source: 'web-client',
                content: {
                  region: data.region || 'ap-northeast-2'
                }
              };
              break;
              
            case 'getEKSClusters':
              messageToSend = {
                id: `req-${Date.now()}`,
                type: 'AWS_EKS_LIST',
                timestamp: Math.floor(Date.now() / 1000),
                source: 'web-client',
                content: {
                  region: data.region || 'ap-northeast-2'
                }
              };
              break;
              
            case 'refresh':
              // 서비스 타입에 따라 적절한 메시지 형식 설정
              const serviceActionMap: Record<string, string> = {
                'ec2': 'AWS_EC2_LIST',
                'ecs': 'AWS_ECS_LIST', 
                'eks': 'AWS_EKS_LIST'
              };
              
              messageToSend = {
                id: `req-${Date.now()}`,
                type: serviceActionMap[data.service] || 'AWS_SERVICE_LIST_ALL',
                timestamp: Math.floor(Date.now() / 1000),
                source: 'web-client',
                content: {
                  region: data.region || 'ap-northeast-2'
                }
              };
              break;
              
            default:
              // 기본 메시지 형식
              messageToSend = {
                id: `req-${Date.now()}`,
                type: 'CLIENT_REQUEST',
                timestamp: Math.floor(Date.now() / 1000),
                source: 'web-client',
                content: data
              };
              break;
          }
        }
        else {
          // 기타 데이터는 content로 래핑
          messageToSend = {
            id: `req-${Date.now()}`,
            type: 'CLIENT_DATA',
            timestamp: Math.floor(Date.now() / 1000),
            source: 'web-client',
            content: data
          };
        }
      }
      else {
        // 원시 타입 데이터 처리
        messageToSend = {
          id: `req-${Date.now()}`,
          type: 'CLIENT_DATA',
          timestamp: Math.floor(Date.now() / 1000),
          source: 'web-client',
          content: { value: data }
        };
      }
      
      const jsonString = JSON.stringify(messageToSend);
      console.log('WebSocket 메시지 전송:', messageToSend);
      this.socket.send(jsonString);
    } catch (error) {
      console.error('WebSocket 메시지 전송 오류:', error);
    }
  }

  public refreshService(service: string): void {
    if (!this._isConnected) {
      console.warn(`${service} 데이터 새로고침 실패: 연결되지 않음`);
      return;
    }
    
    console.log(`${service} 데이터 새로고침 요청`);
    this.send({ action: 'refresh', service: service });
  }
  
  public startActivityMonitoring(): void {
    if (!this._isConnected) {
      console.warn('활동 모니터링 시작 실패: 연결되지 않음');
      return;
    }
    
    console.log('활동 모니터링 시작 요청');
    this.send({ action: 'startMonitoring' });
  }

  public disconnect(): void {
    this.autoReconnect = false;
    this.cancelReconnectTimer();
    this.cleanupExistingSocket();
    console.log('WebSocket 연결 해제 및 자동 재연결 비활성화');
  }

  public getConnectionStatus(): boolean {
    return this._isConnected && this.socket !== null && this.socket.readyState === WebSocket.OPEN;
  }
  
  public setAutoReconnect(enable: boolean): void {
    this.autoReconnect = enable;
    console.log(`WebSocket 자동 재연결 ${enable ? '활성화' : '비활성화'}`);
  }
}