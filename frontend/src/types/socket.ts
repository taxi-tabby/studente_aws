/**
 * WebSocket 클라이언트 인터페이스 정의
 */

// 서비스 타입 값
export type ServiceTypeValue = 'ec2' | 'ecs' | 'eks' | 'activity' | 'system';

// 기본 WebSocket 클라이언트 인터페이스
export interface IWebSocketClient {
  connect(): void;
  disconnect(): void;
  send(data: any): boolean;
  getConnectionStatus(): boolean;
  setAutoReconnect(enable: boolean): void;
  socket: WebSocket | null;
  setDisconnectCallback(callback: () => void): void;
}

// WebSocket 메시지 인터페이스 확장
export interface WebSocketMessage {
  id?: string;
  type?: string;
  action?: string;
  service?: string;
  timestamp?: number;
  source?: string;
  content?: any;
  status?: string;
  message?: string;
  data?: any;
  instances?: any[];
  clusters?: any[];
  self?: boolean;
}

// WebSocket 요청 옵션 인터페이스
export interface WebSocketRequestOptions {
  region?: string;
}

// AWS EC2 관련 명령 인터페이스
export interface EC2CommandOptions extends WebSocketRequestOptions {
  instanceId: string;
}