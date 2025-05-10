/**
 * WebSocket 메시지 포맷팅을 담당하는 유틸리티 클래스
 */
import { CommandType, MessageType, WS_CONFIG } from '../constants/socketTypes';

export class WebSocketMessageFormatter {
	/**
	 * 요청 메시지 생성
	 * @param data 요청 데이터
	 * @returns 포맷팅된 메시지
	 */
	public static formatMessage(data: any): any {
		// 문자열 메시지는 그대로 반환
		if (typeof data === 'string') {
			return data;
		}

		let messageToSend: any;

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
			// 액션 기반 요청 처리
			else if (data.action && typeof data.action === 'string') {
				messageToSend = this.formatActionBasedMessage(data);
			} else {
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

		return messageToSend;
	}

	/**
	 * 액션 기반 메시지 포맷팅
	 * @param data 요청 데이터
	 * @returns 포맷팅된 메시지
	 */
	private static formatActionBasedMessage(data: any): any {
		let messageToSend: any;

		// command_definitions.py에서 주석처리 되지 않은 명령어만 처리
		switch (data.action) {
			case CommandType.TEST:
				messageToSend = {
					id: `req-${Date.now()}`,
					type: 'test',
					timestamp: Math.floor(Date.now() / 1000),
					source: 'web-client'
				};
				break;

			case CommandType.REFRESH_SERVICE:
				// 서비스 타입에 따라 적절한 메시지 형식 설정
				// Removed serviceActionMap as it's not used

				messageToSend = {
					id: `req-${Date.now()}`,
					type: 'refresh_service',
					action: 'refresh_service',
					timestamp: Math.floor(Date.now() / 1000),
					source: 'web-client',
					service: data.service,
					content: {
						service: data.service,
						region: data.region
					}
				};
				break;

			default:
				// 기본 메시지 형식
				messageToSend = {
					id: `req-${Date.now()}`,
					type: 'CLIENT_REQUEST',
					action: data.action,
					timestamp: Math.floor(Date.now() / 1000),
					source: 'web-client',
					content: data
				};
				break;
		}

		return messageToSend;
	}
}