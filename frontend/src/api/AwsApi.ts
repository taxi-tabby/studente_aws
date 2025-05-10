/**
 * AWS 서비스 관련 API 기능
 */
import { WebSocketService } from '../services/WebSocketService';
import { CommandType } from '../constants/socketTypes';
import type { ServiceTypeValue, WebSocketRequestOptions } from '../types/socket';

/**
 * AWS 서비스 API 클래스
 * WebSocketService를 이용하여 AWS 관련 명령을 처리합니다.
 */
export class AwsApi {
	private webSocketService: WebSocketService;

	constructor(webSocketService: WebSocketService) {
		this.webSocketService = webSocketService;
	}

	/**
	 * 특정 서비스 데이터 새로고침 요청
	 * @param {ServiceTypeValue} service - 서비스 타입
	 * @param {WebSocketRequestOptions} options - 요청 옵션
	 * @returns {boolean} 전송 성공 여부
	 */
	public refreshService(service: ServiceTypeValue, options?: WebSocketRequestOptions): boolean {
		if (!this.webSocketService.getConnectionStatus()) {
			console.warn(`${service} 데이터 새로고침 실패: 연결되지 않음`);
			return false;
		}

		console.log(`${service} 데이터 새로고침 요청`);
		return this.webSocketService.send({
			action: CommandType.REFRESH_SERVICE,
			service,
			...options
		});
	}



	public passwordVerify(password: string, options?: WebSocketRequestOptions): boolean {
		if (!this.webSocketService.getConnectionStatus()) {
			console.warn(`비밀번호 확인 실패: 연결되지 않음`);
			return false;
		}


		return this.webSocketService.send({
			action: CommandType.PASSWORD_VERIFY,
			password: password,
			...options
		});
	}


}


