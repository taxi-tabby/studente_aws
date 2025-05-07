"""
WebSocket 메시지 형식 및 전송 기능 정의 모듈
"""
import json
import time
import uuid
import logging
import asyncio
import websockets
import threading
import queue
from collections import defaultdict

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

# 메시지 큐 및 스로틀링을 위한 설정
_message_queue = queue.Queue()
_queue_processing = False
_activity_counters = defaultdict(int)  # 각 활동 유형별 카운터
_last_send_time = {}  # 각 활동 유형별 마지막 전송 시간
_queue_lock = threading.Lock()  # 큐 처리를 위한 락

# 스로틀링 설정 (밀리초)
THROTTLE_INTERVAL_MS = {
    "KEYBOARD_ACTIVITY": 300,  # 키보드 활동은 300ms 간격으로 제한
    "MOUSE_MOVEMENT": 500,     # 마우스 이동은 500ms 간격으로 제한
    "MOUSE_CLICK": 200,        # 마우스 클릭은 200ms 간격으로 제한
    "SCREEN_CHANGE": 1000,     # 화면 변화는 1초 간격으로 제한
    "ACTIVE_WINDOW": 500,      # 활성 창 변경은 500ms 간격으로 제한
    "AUDIO_PLAYBACK": 1000,    # 오디오 재생은 1초 간격으로 제한
    "DEFAULT": 200             # 기본값은 200ms
}

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
    TIMER_START= "TIMER_START"
    TIMER_TICK = "TIMER_TICK"
    TIMER_END = "TIMER_END"
    
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

def process_message_queue():
    """메시지 큐를 처리하는 스레드 함수"""
    global _queue_processing
    
    if _queue_processing:
        return  # 이미 실행 중인 경우 중복 실행 방지
    
    with _queue_lock:
        _queue_processing = True
    
    try:
        logger.debug("메시지 큐 처리 스레드 시작")
        
        while True:
            try:
                # 큐가 비어있지 않으면 메시지 처리
                if not _message_queue.empty():
                    # 큐에서 메시지와 활동 유형 가져오기
                    message, activity_type, direct_send = _message_queue.get(block=False)
                    
                    # 직접 전송 메시지는 스로틀링 없이 바로 전송
                    if direct_send:
                        if isinstance(message, dict):
                            logger.debug(f"우선순위 메시지 직접 전송 - 타입: {message.get('type', 'UNKNOWN')}")
                        else:
                            logger.debug("우선순위 문자열 메시지 직접 전송")
                        
                        # TCP 및 WebSocket으로 전송
                        try:
                            from core.tcp_server import forward_activity_message
                            forward_activity_message(message)
                        except Exception as e:
                            logger.error(f"직접 메시지 전송 중 오류: {e}")
                            # 실패해도 계속 진행
                        
                        _message_queue.task_done()
                        continue
                    
                    # 카운터 증가 및 마지막 전송 시간 확인
                    _activity_counters[activity_type] += 1
                    current_time = int(time.time() * 1000)  # 현재 시간 (밀리초)
                    
                    # 스로틀 간격 설정 (기본값 사용 또는 활동 유형별 간격 적용)
                    throttle_interval = THROTTLE_INTERVAL_MS.get(activity_type, THROTTLE_INTERVAL_MS["DEFAULT"])
                    
                    # 마지막 전송 이후 충분한 시간이 지났는지 확인
                    if activity_type not in _last_send_time or (current_time - _last_send_time[activity_type]) >= throttle_interval:
                        count = _activity_counters[activity_type]
                        
                        # 카운터가 있는 메시지의 경우, 카운트 정보 추가
                        if count > 1 and isinstance(message, dict) and "content" in message:
                            if isinstance(message["content"], dict):
                                message["content"]["count"] = count
                            else:
                                # content가 딕셔너리가 아니면 딕셔너리로 변환
                                message["content"] = {"value": message["content"], "count": count}
                        
                        # 전송 시도
                        try:
                            from core.tcp_server import forward_activity_message
                            forward_activity_message(message)
                            
                            # 전송 시간 및 카운터 업데이트
                            _last_send_time[activity_type] = current_time
                            _activity_counters[activity_type] = 0
                            
                            logger.debug(f"활동 메시지 전송 완료 - 타입: {activity_type}, 카운트: {count}")
                        except Exception as e:
                            logger.error(f"큐 메시지 전송 중 오류: {e}")
                    
                    _message_queue.task_done()
                else:
                    # 큐가 비어있으면 잠시 대기
                    time.sleep(0.05)
            
            except queue.Empty:
                # 큐가 비어있는 경우 짧게 대기
                time.sleep(0.05)
            
            except Exception as e:
                logger.error(f"메시지 큐 처리 중 오류 발생: {e}")
                time.sleep(0.1)  # 오류 발생 시 약간 더 긴 대기
    
    finally:
        with _queue_lock:
            _queue_processing = False
        logger.debug("메시지 큐 처리 스레드 종료")

def start_queue_processor():
    """메시지 큐 처리 스레드를 시작합니다."""
    global _queue_processing
    
    with _queue_lock:
        if not _queue_processing:
            # 큐 처리 스레드 시작
            queue_thread = threading.Thread(target=process_message_queue, daemon=True, name="MessageQueueProcessor")
            queue_thread.start()
            logger.info("메시지 큐 처리 스레드가 시작되었습니다.")
            return True
    
    return False

def queue_message(message, activity_type=None, direct_send=False):
    """
    메시지를 큐에 추가합니다.
    
    Args:
        message: 추가할 메시지 (딕셔너리 또는 문자열)
        activity_type: 활동 유형, 메시지가 딕셔너리인 경우 자동 감지
        direct_send: 스로틀링 없이 즉시 전송해야 하는지 여부
        
    Returns:
        bool: 큐에 추가 성공 여부
    """
    try:
        # 활동 유형 추출 또는 사용
        if activity_type is None and isinstance(message, dict):
            content = message.get("content", {})
            if isinstance(content, dict) and "activity" in content:
                activity_type = content["activity"]
            else:
                activity_type = message.get("type", "UNKNOWN")
        
        # 큐에 메시지 추가
        _message_queue.put((message, activity_type, direct_send))
        
        # 큐 처리기 시작 (아직 실행 중이 아니면)
        start_queue_processor()
        
        return True
    
    except Exception as e:
        logger.error(f"메시지 큐 추가 중 오류 발생: {e}")
        return False

# 편의 함수: 특정 유형의 메시지를 빠르게 생성하고 전송
def send_activity_message(activity_type, details=None):
    """
    사용자 활동 관련 메시지를 생성하고 큐에 추가합니다.
    
    Args:
        activity_type: 활동 유형 (MessageType 클래스의 상수 사용)
        details: 추가 세부 정보 (선택 사항)
        
    Returns:
        bool: 메시지 큐 추가 성공 여부
    """
    content = {"activity": activity_type}
    if details:
        if isinstance(details, dict):
            content.update(details)
        else:
            content["details"] = details
            
    logger.debug(f"활동 메시지 생성 중: {activity_type}")
    message = create_message(MessageType.USER_ACTIVITY, content)
    
    # 메시지를 큐에 추가
    return queue_message(message, activity_type)

# 특정 활동 유형에 대한 편의 함수들

def send_timer_start():
    """타이머 시작 메세지를 전송합니다다."""
    logger.info("타이머 시작 메시지 큐에 추가")
    return send_activity_message(MessageType.TIMER_START)

def send_timer_tick(nowtime=None):
    """타이머 진행마다 메세지를 전송합니다"""
    logger.info("타이머 시작 메시지 큐에 추가")
    return send_activity_message(MessageType.TIMER_TICK, {"nowtime": nowtime})

def send_timer_end():
    """타이머 종료 시 메세지를 전송합니다"""
    logger.info("타이머 시작 메시지 큐에 추가")
    return send_activity_message(MessageType.TIMER_END)


def send_keyboard_activity():
    """키보드 활동 메시지를 전송합니다."""
    logger.info("키보드 활동 메시지 큐에 추가")
    return send_activity_message(MessageType.KEYBOARD_ACTIVITY)

def send_mouse_movement():
    """마우스 이동 메시지를 전송합니다."""
    logger.info("마우스 이동 메시지 큐에 추가")
    return send_activity_message(MessageType.MOUSE_MOVEMENT)

def send_mouse_click():
    """마우스 클릭 메시지를 전송합니다."""
    logger.info("마우스 클릭 메시지 큐에 추가")
    return send_activity_message(MessageType.MOUSE_CLICK)

def send_screen_change():
    """화면 변화 메시지를 전송합니다."""
    logger.info("화면 변화 메시지 큐에 추가")
    return send_activity_message(MessageType.SCREEN_CHANGE)

def send_active_window(window_name):
    """활성 창 변경 메시지를 전송합니다."""
    logger.info(f"활성 창 변경 메시지 큐에 추가: {window_name}")
    return send_activity_message(MessageType.ACTIVE_WINDOW, {"window_name": window_name})

def send_audio_playback(volume):
    """오디오 재생 메시지를 전송합니다."""
    logger.info(f"오디오 재생 메시지 큐에 추가 (볼륨: {volume})")
    return send_activity_message(MessageType.AUDIO_PLAYBACK, {"volume": volume})

# 큐 처리 스레드 자동 시작
start_queue_processor()