"""
명령어 레지스트리 모듈
클라이언트와 서버 간 통신에 사용되는 명령어 핸들러를 등록하고 관리합니다.
"""
import logging
import inspect
import asyncio
from typing import Dict, Callable, Any, Optional, Union, Awaitable

# 로거 설정
logger = logging.getLogger(__name__)

# 명령어 핸들러 등록을 위한 딕셔너리
# action_name -> handler_function 매핑
_action_handlers: Dict[str, Callable] = {}

# 메시지 타입 핸들러 등록을 위한 딕셔너리
# message_type -> handler_function 매핑
_type_handlers: Dict[str, Callable] = {}


def register_action_handler(action_name: str):
    """
    액션 기반 명령어 핸들러를 등록하는 데코레이터
    
    Args:
        action_name: 등록할 액션 이름
        
    Returns:
        Callable: 데코레이터 함수
    """
    def decorator(handler_func):
        _action_handlers[action_name] = handler_func
        logger.debug(f"액션 핸들러 등록됨: {action_name}")
        return handler_func
    return decorator


def register_type_handler(message_type: str):
    """
    메시지 타입 기반 명령어 핸들러를 등록하는 데코레이터
    
    Args:
        message_type: 등록할 메시지 타입
        
    Returns:
        Callable: 데코레이터 함수
    """
    def decorator(handler_func):
        _type_handlers[message_type] = handler_func
        logger.debug(f"메시지 타입 핸들러 등록됨: {message_type}")
        return handler_func
    return decorator


async def process_command(message: dict, client=None, region: str = None) -> Optional[dict]:
    """
    메시지를 처리하여 적절한 핸들러 함수를 호출합니다.
    
    Args:
        message: 처리할 명령어 메시지
        client: 클라이언트 소켓 또는 WebSocket 객체 (선택적)
        region: AWS 리전 (선택적)
        
    Returns:
        Optional[dict]: 핸들러 함수의 응답 또는 None
    """
    try:
        if not isinstance(message, dict):
            logger.warning(f"유효하지 않은 메시지 형식: {type(message)}")
            return {"status": "error", "message": "유효한 메시지 형식이 아닙니다."}
        
        # action 기반 명령어 처리
        if "action" in message:
            action = message.get("action")
            handler = _action_handlers.get(action)
            
            if handler:
                logger.info(f"액션 핸들러 실행: {action}")
                if region:
                    message["region"] = region  # 리전 정보가 있으면 메시지에 추가
                
                # 핸들러가 비동기 함수인지 확인
                if inspect.iscoroutinefunction(handler):
                    return await handler(message, client)
                else:
                    return handler(message, client)
            else:
                logger.warning(f"알 수 없는 액션: {action}")
                return {"status": "error", "message": f"알 수 없는 액션: {action}"}
        
        # type 기반 명령어 처리
        elif "type" in message:
            message_type = message.get("type")
            handler = _type_handlers.get(message_type)
            
            if handler:
                logger.info(f"메시지 타입 핸들러 실행: {message_type}")
                if region:
                    message["region"] = region
                
                # 핸들러가 비동기 함수인지 확인
                if inspect.iscoroutinefunction(handler):
                    return await handler(message, client)
                else:
                    return handler(message, client)
            else:
                logger.warning(f"알 수 없는 메시지 타입: {message_type}")
                return {"status": "error", "message": f"알 수 없는 메시지 타입: {message_type}"}
        
        else:
            logger.warning("메시지에 'action' 또는 'type' 키가 없음")
            return {"status": "error", "message": "메시지에 'action' 또는 'type' 키가 필요합니다."}
    
    except Exception as e:
        logger.error(f"명령어 처리 중 오류: {e}", exc_info=True)
        return {"status": "error", "message": f"명령어 처리 중 오류가 발생했습니다: {str(e)}"}


def register_command_handlers():
    """
    모든 명령어 핸들러를 등록합니다.
    command_definitions.py에서 정의된 핸들러들이 데코레이터를 통해 자동으로 등록됩니다.
    """
    # 이 함수는 명시적으로 호출될 필요가 없습니다.
    # command_definitions.py가 임포트될 때 데코레이터를 통해 자동으로 핸들러 등록이 이루어집니다.
    logger.info("명령어 핸들러 등록이 완료되었습니다.")
    logger.debug(f"등록된 액션 핸들러 수: {len(_action_handlers)}")
    logger.debug(f"등록된 메시지 타입 핸들러 수: {len(_type_handlers)}")


def get_registered_commands():
    """
    등록된 모든 명령어를 반환합니다.
    
    Returns:
        dict: 등록된 액션과 메시지 타입 명령어
    """
    return {
        "actions": list(_action_handlers.keys()),
        "types": list(_type_handlers.keys())
    }