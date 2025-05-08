"""
명령어 레지스트리 모듈
클라이언트와 서버 간 통신에 사용되는 명령어 핸들러를 등록하고 관리합니다.
"""
import logging
import inspect
import asyncio
import time
from typing import Dict, Callable, Any, Optional, Union, Awaitable

# 로거 설정
logger = logging.getLogger(__name__)

# 통합된 명령어 핸들러 등록을 위한 딕셔너리
# command_key -> handler_function 매핑
_command_handlers: Dict[str, Callable] = {}

# 브로드캐스트 함수 참조
_broadcast_func = None

def set_broadcast_function(broadcast_func):
    """
    브로드캐스트 함수 참조를 설정합니다.
    """
    global _broadcast_func
    _broadcast_func = broadcast_func
    logger.debug("브로드캐스트 함수가 설정되었습니다.")

def register_action_handler(action_name: str):
    """
    명령어 핸들러를 등록하는 데코레이터
    
    Args:
        action_name: 등록할 액션 이름
        
    Returns:
        Callable: 데코레이터 함수
    """
    def decorator(handler_func):
        _command_handlers[action_name] = handler_func
        logger.debug(f"핸들러 등록됨: {action_name}")
        return handler_func
    return decorator

# 이전 코드와의 호환성을 위한 별칭
def register_handler(command_key: str, handler_type=None):
    """
    명령어 핸들러를 등록하는 데코레이터 (두 번째 매개변수는 이전 버전과의 호환성을 위해 유지)
    
    Args:
        command_key: 등록할 명령어 키 (액션 또는 타입 이름)
        handler_type: 핸들러 타입 (무시됨, 호환성을 위해 유지)
        
    Returns:
        Callable: 데코레이터 함수
    """
    return register_action_handler(command_key)

register_type_handler = register_action_handler

async def process_command(message: dict, client=None, region: str = None, client_id=None) -> Optional[dict]:
    """
    메시지를 처리하여 적절한 핸들러 함수를 호출합니다.
    
    Args:
        message: 처리할 명령어 메시지
        client: 클라이언트 소켓 또는 WebSocket 객체 (선택적)
        region: AWS 리전 (선택적)
        client_id: 요청을 보낸 클라이언트의 ID (선택적)
        
    Returns:
        Optional[dict]: 핸들러 함수의 응답 또는 None
    """
    try:
        if not isinstance(message, dict):
            logger.warning(f"유효하지 않은 메시지 형식: {type(message)}")
            return {"status": "error", "message": "유효한 메시지 형식이 아닙니다.", "self": True}
        
        # 명령어 키 추출 (action 또는 type)
        command_key = None
        if "action" in message:
            command_key = message.get("action")
        elif "type" in message:
            # type을 action으로 변환하여 처리
            command_key = message.get("type")
            # 메시지에 action 키를 추가하여 일관성 유지
            message["action"] = command_key
        else:
            logger.warning("메시지에 'action' 또는 'type' 키가 없음")
            return {"status": "error", "message": "메시지에 'action' 또는 'type' 키가 필요합니다.", "self": True}
        
        # 핸들러 탐색 및 실행
        handler = _command_handlers.get(command_key)
        if handler:
            logger.info(f"핸들러 실행: {command_key}")
            if region:
                message["region"] = region  # 리전 정보가 있으면 메시지에 추가
            
            # 핸들러가 비동기 함수인지 확인
            if inspect.iscoroutinefunction(handler):
                response = await handler(message, client)
            else:
                response = handler(message, client)
            
            # 응답이 없는 경우
            if not response:
                return {"status": "success", "self": True}
            
            # 응답에 self 플래그 추가 - 요청한 클라이언트에게 가는 응답은 항상 self: true
            if isinstance(response, dict):
                response["self"] = True
                
                response["timestamp"] = int(time.time())
                
                # 공유 플래그가 있으면 브로드캐스트 실행
                if "share" in response and response["share"] and _broadcast_func:
                    # 공유용 메시지 생성 (self 플래그를 false로 설정, client_id 추가)
                    shared_message = response.copy()
                    shared_message.pop("share", None)
                    # 다른 클라이언트에게 가는 메시지는 self: false로 설정
                    shared_message["self"] = False
                    
                    if client_id:
                        shared_message["from_client_id"] = client_id
                        
                    # 브로드캐스트 실행
                    try:
                        await _broadcast_func(shared_message)
                        logger.debug(f"메시지 브로드캐스트 완료: {command_key}")
                    except Exception as e:
                        logger.error(f"메시지 브로드캐스트 중 오류 발생: {e}")
            
            return response
        else:
            logger.warning(f"알 수 없는 명령어: {command_key}")
            return {"status": "error", "message": f"알 수 없는 명령어: {command_key}", "self": True}
    
    except Exception as e:
        logger.error(f"명령어 처리 중 오류: {e}", exc_info=True)
        return {"status": "error", "message": f"명령어 처리 중 오류가 발생했습니다: {str(e)}", "self": True}

def register_command_handlers():
    """
    모든 명령어 핸들러를 등록합니다.
    command_definitions.py에서 정의된 핸들러들이 데코레이터를 통해 자동으로 등록됩니다.
    """
    # 이 함수는 명시적으로 호출될 필요가 없습니다.
    # command_definitions.py가 임포트될 때 데코레이터를 통해 자동으로 핸들러 등록이 이루어집니다.
    logger.info("명령어 핸들러 등록이 완료되었습니다.")
    logger.debug(f"등록된 명령어 핸들러 수: {len(_command_handlers)}")

def get_registered_commands():
    """
    등록된 모든 명령어를 반환합니다.
    
    Returns:
        dict: 등록된 모든 명령어 목록
    """
    return {
        "actions": list(_command_handlers.keys())
    }