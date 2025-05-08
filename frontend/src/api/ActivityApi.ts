/**
 * 활동 모니터링 관련 API 기능
 */
import { WebSocketService } from '../services/WebSocketService';
import { CommandType } from '../constants/socketTypes';

/**
 * 활동 모니터링 API 클래스
 * WebSocketService를 이용하여 활동 모니터링 관련 명령을 처리합니다.
 */
export class ActivityApi {
  private webSocketService: WebSocketService;

  constructor(webSocketService: WebSocketService) {
    this.webSocketService = webSocketService;
  }

  /**
   * 테스트 명령 전송
   * @returns {boolean} 전송 성공 여부
   */
  public sendTest(): boolean {
    return this.webSocketService.send({
      action: CommandType.TEST
    });
  }
}