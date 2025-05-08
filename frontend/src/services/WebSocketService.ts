/**
 * WebSocket 통신을 담당하는 기본 서비스 클래스
 * 여러 모듈로 분리된 기능을 조합하여 인터페이스 제공
 */
import type { IWebSocketClient } from '../types/socket';
import { WebSocketConnection } from './WebSocketConnection';
import { WebSocketMessageFormatter } from './WebSocketMessageFormatter';
// import { WS_CONFIG } from '../constants/socketTypes';

/**
 * WebSocket 서비스 클래스
 * 클라이언트와 서버 간의 WebSocket 통신을 관리
 */
export class WebSocketService implements IWebSocketClient {
  private connection: WebSocketConnection;

  /**
   * WebSocket 서비스 생성
   * @param port WebSocket 서버 포트
   * @param messageHandler 메시지 수신 핸들러
   * @param hostname 서버 호스트 이름
   */
  constructor(port: number, messageHandler: (message: any) => void, hostname: string = 'localhost') {
    this.connection = new WebSocketConnection(port, messageHandler, hostname);
  }

  /**
   * 소켓 객체에 대한 프록시 접근자
   * IWebSocketClient 인터페이스 구현을 위한 getter
   */
  get socket(): WebSocket | null {
    return this.connection.socket;
  }

  /**
   * 연결 끊김 콜백 설정
   * @param callback 콜백 함수
   */
  public setDisconnectCallback(callback: () => void): void {
    this.connection.setDisconnectCallback(callback);
  }

  /**
   * WebSocket 서버에 연결
   */
  public connect(): void {
    this.connection.connect();
  }

  /**
   * WebSocket 연결 해제
   */
  public disconnect(): void {
    this.connection.disconnect();
  }

  /**
   * 메시지 전송
   * @param data 전송할 데이터
   * @returns 전송 성공 여부
   */
  public send(data: any): boolean {
    if (!this.connection.getConnectionStatus()) {
      if (typeof data === 'object' && data.action) {
        console.warn(`메시지 전송 실패: ${data.action} (연결 끊김)`);
      } else {
        console.warn('메시지 전송 실패: 연결 끊김');
      }
      return false;
    }

    try {
      // 메시지 포맷팅
      const messageToSend = WebSocketMessageFormatter.formatMessage(data);
      
      // 포맷팅된 메시지가 문자열이면 그대로 전송, 객체면 JSON으로 변환하여 전송
      let jsonString: string;
      if (typeof messageToSend === 'string') {
        jsonString = messageToSend;
      } else {
        jsonString = JSON.stringify(messageToSend);
        console.log('WebSocket 메시지 전송:', messageToSend);
      }
      
      // 연결 객체를 통해 메시지 전송
      return this.connection.send(jsonString);
    } catch (error) {
      console.error('WebSocket 메시지 전송 준비 중 오류:', error);
      return false;
    }
  }

  /**
   * 연결 상태 확인
   * @returns 연결 상태
   */
  public getConnectionStatus(): boolean {
    return this.connection.getConnectionStatus();
  }
  
  /**
   * 자동 재연결 설정
   * @param enable 활성화 여부
   */
  public setAutoReconnect(enable: boolean): void {
    this.connection.setAutoReconnect(enable);
  }
}