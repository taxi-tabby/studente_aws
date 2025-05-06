"""
WebSocket 메시지 형식 및 전송 기능 정의 모듈
"""
import json
import time
import uuid
import logging
import asyncio
import websockets

# 로거 설정
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler()]
)

# WebSocket 서버 설정
WS_HOST = "127.0.0.1"
WS_PORT = 20201  # WebSocket 포트를 TCP 서버와 일치시킴
WS_URL = f"ws://{WS_HOST}:{WS_PORT}"

# WebSocket 클라이언트 연결 캐싱
_ws_connection = None

# 메시지 타입 정의
class MessageType:
    KEYBOARD_ACTIVITY = "KEYBOARD_ACTIVITY"
    MOUSE_MOVEMENT = "MOUSE_MOVEMENT"
    MOUSE_CLICK = "MOUSE_CLICK"
    SCREEN_CHANGE = "SCREEN_CHANGE"
    ACTIVE_WINDOW = "ACTIVE_WINDOW"
    AUDIO_PLAYBACK = "AUDIO_PLAYBACK"
    USER_ACTIVITY = "USER_ACTIVITY"
    SYSTEM_STATUS = "SYSTEM_STATUS"
    
    # AWS 서비스 관련
    AWS_EC2_LIST = "AWS_EC2_LIST"
    AWS_ECS_LIST = "AWS_ECS_LIST"
    AWS_EKS_LIST = "AWS_EKS_LIST"
    AWS_SERVICE_STATUS = "AWS_SERVICE_STATUS"

def create_message(message_type, content, source="activity_monitor"):
    """
    표준화된 메시지 형식으로 메시지를 생성합니다.
    
    Args:
        message_type: 메시지 유형 (MessageType 클래스의 상수 사용)
        content: 메시지 내용 (문자열 또는 딕셔너리)
        source: 메시지 소스 (기본값: "activity_monitor")
        
    Returns:
        dict: 형식화된 메시지 딕셔너리
    """
    msg = {
        "id": str(uuid.uuid4()),
        "type": message_type,
        "timestamp": int(time.time()),
        "source": source,
        "content": content
    }
    logger.debug(f"메시지 생성: {message_type} - ID: {msg['id'][:8]}...")
    return msg

async def get_ws_connection():
    """
    WebSocket 서버에 대한 연결을 가져옵니다. 연결이 없거나 끊어진 경우 새 연결을 생성합니다.
    
    Returns:
        websockets.WebSocketClientProtocol: WebSocket 연결
    """
    global _ws_connection
    
    try:
        # 연결이 없거나 닫혀있는 경우, 새로 생성
        if _ws_connection is None or _ws_connection.closed:
            logger.info(f"WebSocket 서버에 연결 시도 중: {WS_URL}")
            _ws_connection = await websockets.connect(WS_URL)
            logger.info("WebSocket 서버에 성공적으로 연결됨")
        
        return _ws_connection
    
    except Exception as e:
        logger.error(f"WebSocket 연결 생성 중 오류 발생: {e}")
        _ws_connection = None
        return None

async def send_message_async(message):
    """
    JSON 형식으로 메시지를 WebSocket 서버로 비동기 전송합니다.
    
    Args:
        message: 전송할 메시지 딕셔너리 또는 문자열
        
    Returns:
        bool: 메시지 전송 성공 여부
    """
    try:
        # 문자열이면 그대로 사용, 딕셔너리면 JSON으로 직렬화
        if isinstance(message, dict):
            message_str = json.dumps(message, ensure_ascii=False)
            message_type = message.get("type", "UNKNOWN")
            message_id = message.get("id", "")[:8]
            logger.debug(f"WebSocket 메시지 전송 시도 - 타입: {message_type}, ID: {message_id}...")
        else:
            message_str = str(message)
            logger.debug(f"WebSocket 문자열 메시지 전송 시도: {message_str[:50]}...")
        
        # 메시지 전송 (최대 3번 재시도)
        max_retries = 3
        for attempt in range(max_retries):
            try:
                ws = await get_ws_connection()
                if ws is None:
                    logger.warning(f"WebSocket 연결 실패 (시도 {attempt+1}/{max_retries})")
                    await asyncio.sleep(0.5)
                    continue
                    
                logger.debug(f"WebSocket 메시지 전송 중 (시도 {attempt+1}/{max_retries})")
                await ws.send(message_str)
                
                if isinstance(message, dict):
                    logger.info(f"메시지 전송 완료 - 타입: {message_type}, ID: {message_id}")
                else:
                    logger.info("문자열 메시지 전송 완료")
                return True
            
            except websockets.exceptions.ConnectionClosed as e:
                logger.error(f"WebSocket 연결이 닫혔습니다 (시도 {attempt+1}/{max_retries}): {e}")
                # 연결 재설정
                global _ws_connection
                _ws_connection = None
                
                # 마지막 시도가 아니면 대기 후 재시도
                if attempt < max_retries - 1:
                    await asyncio.sleep(0.5)
            
            except Exception as e:
                logger.error(f"WebSocket 메시지 전송 중 오류 발생 (시도 {attempt+1}/{max_retries}): {e}")
                # 연결 재설정
                _ws_connection = None
                
                # 마지막 시도가 아니면 대기 후 재시도
                if attempt < max_retries - 1:
                    await asyncio.sleep(0.5)
        
        logger.error("최대 재시도 횟수 초과. WebSocket 메시지 전송 실패.")
        return False
    
    except Exception as e:
        logger.error(f"WebSocket 메시지 전송 중 오류 발생: {e}")
        return False

def send_message(message):
    """
    동기 방식으로 WebSocket 메시지를 전송하는 래퍼 함수
    
    Args:
        message: 전송할 메시지 딕셔너리 또는 문자열
        
    Returns:
        bool: 메시지 전송 성공 여부
    """
    try:
        # 새로운 이벤트 루프 생성
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        # 비동기 함수 실행
        result = loop.run_until_complete(send_message_async(message))
        loop.close()
        return result
    except Exception as e:
        logger.error(f"동기적 WebSocket 메시지 전송 중 오류 발생: {e}")
        return False

# 편의 함수: 특정 유형의 메시지를 빠르게 생성하고 전송
def send_activity_message(activity_type, details=None):
    """
    사용자 활동 관련 메시지를 생성하고 전송합니다.
    
    Args:
        activity_type: 활동 유형 (MessageType 클래스의 상수 사용)
        details: 추가 세부 정보 (선택 사항)
        
    Returns:
        bool: 메시지 전송 성공 여부
    """
    content = {"activity": activity_type}
    if details:
        if isinstance(details, dict):
            content.update(details)
        else:
            content["details"] = details
            
    logger.debug(f"활동 메시지 생성 중: {activity_type}")
    message = create_message(MessageType.USER_ACTIVITY, content)
    
    # WebSocket을 통한 메시지 전송
    ws_result = send_message(message)
    
    # TCP 서버를 통한 메시지 전송도 시도
    tcp_result = False
    try:
        from core.tcp_server import send_to_tcp_clients, forward_activity_message
        tcp_result = forward_activity_message(message)
        if tcp_result:
            logger.debug(f"TCP 서버를 통한 {activity_type} 메시지 전송 성공")
        else:
            logger.warning(f"TCP 서버를 통한 {activity_type} 메시지 전송 실패")
    except Exception as e:
        logger.error(f"TCP 서버 메시지 전송 중 오류: {e}")
    
    return ws_result or tcp_result  # 하나라도 성공하면 True 반환

# 특정 활동 유형에 대한 편의 함수들
def send_keyboard_activity():
    """키보드 활동 메시지를 전송합니다."""
    logger.info("키보드 활동 메시지 전송")
    return send_activity_message(MessageType.KEYBOARD_ACTIVITY)

def send_mouse_movement():
    """마우스 이동 메시지를 전송합니다."""
    logger.info("마우스 이동 메시지 전송")
    return send_activity_message(MessageType.MOUSE_MOVEMENT)

def send_mouse_click():
    """마우스 클릭 메시지를 전송합니다."""
    logger.info("마우스 클릭 메시지 전송")
    return send_activity_message(MessageType.MOUSE_CLICK)

def send_screen_change():
    """화면 변화 메시지를 전송합니다."""
    logger.info("화면 변화 메시지 전송")
    return send_activity_message(MessageType.SCREEN_CHANGE)

def send_active_window(window_name):
    """활성 창 변경 메시지를 전송합니다."""
    logger.info(f"활성 창 변경 메시지 전송: {window_name}")
    return send_activity_message(MessageType.ACTIVE_WINDOW, {"window_name": window_name})

def send_audio_playback(volume):
    """오디오 재생 메시지를 전송합니다."""
    logger.info(f"오디오 재생 메시지 전송 (볼륨: {volume})")
    return send_activity_message(MessageType.AUDIO_PLAYBACK, {"volume": volume})