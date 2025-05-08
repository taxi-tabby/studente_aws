/**
 * WebSocket 클라이언트 통합 모듈
 * 이 파일은 하위 호환성을 위해 유지되며, 리팩토링된 모듈들을 다시 통합합니다.
 */
import { WebSocketService } from '../services/WebSocketService';
import { AwsApi } from '../api/AwsApi';
import { ActivityApi } from '../api/ActivityApi';
import { CommandType, ServiceType, MessageType } from '../constants/socketTypes';
import type { IWebSocketClient, ServiceTypeValue } from '../types/socket';

// 타입 및 상수 재익스포트
export { CommandType, ServiceType, MessageType };

// WebSocket 클라이언트 클래스
export class WebSocketClient implements IWebSocketClient {
  public socket: WebSocket | null = null;
  private webSocketService: WebSocketService;
  private awsApi: AwsApi;
  private activityApi: ActivityApi;

  constructor(port: number, messageHandler: (message: any) => void, hostname: string = 'localhost') {
    // 기본 WebSocket 서비스 초기화
    this.webSocketService = new WebSocketService(port, messageHandler, hostname);
    
    // 서비스 위임을 통한 socket 참조 연결
    Object.defineProperty(this, 'socket', {
      get: () => this.webSocketService.socket
    });
    
    // API 객체 초기화
    this.awsApi = new AwsApi(this.webSocketService);
    this.activityApi = new ActivityApi(this.webSocketService);
  }

  // IWebSocketClient 인터페이스 구현 (WebSocketService에 위임)
  
  public setDisconnectCallback(callback: () => void): void {
    this.webSocketService.setDisconnectCallback(callback);
  }

  public connect(): void {
    this.webSocketService.connect();
  }

  public disconnect(): void {
    this.webSocketService.disconnect();
  }

  public send(data: any): boolean {
    return this.webSocketService.send(data);
  }

  public getConnectionStatus(): boolean {
    return this.webSocketService.getConnectionStatus();
  }
  
  public setAutoReconnect(enable: boolean): void {
    this.webSocketService.setAutoReconnect(enable);
  }

  // 서버에 구현된 API 메서드만 유지
  
  /**
   * 테스트 명령 전송
   * @returns {boolean} 전송 성공 여부
   */
  public sendTest(): boolean {
    return this.activityApi.sendTest();
  }

  /**
   * 특정 서비스 데이터 새로고침 요청
   * @param {ServiceTypeValue} service - 서비스 타입
   * @param {string} region - AWS 리전 (선택 사항)
   * @returns {boolean} 전송 성공 여부
   */
  public refreshService(service: ServiceTypeValue, region?: string): boolean {
    return this.awsApi.refreshService(service, { region });
  }
}