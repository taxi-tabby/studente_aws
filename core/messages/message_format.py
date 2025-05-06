"""
TCP 메시지 형식 및 전송 기능 정의 모듈
"""
import json
import socket
import time
import uuid
import logging

# 로거 설정
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler()]
)

# TCP 서버 설정
TCP_IP = "127.0.0.1"
TCP_PORT = 20200

# TCP 클라이언트 연결 캐싱
_tcp_connection = None

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

def get_tcp_connection():
    """
    TCP 서버에 대한 연결을 가져옵니다. 연결이 없거나 끊어진 경우 새 연결을 생성합니다.
    
    Returns:
        socket.socket: TCP 소켓 연결
    """
    global _tcp_connection
    
    try:
        # 연결이 없는 경우, 새로 생성
        if _tcp_connection is None:
            logger.info(f"TCP 서버에 연결 시도 중: {TCP_IP}:{TCP_PORT}")
            _tcp_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            _tcp_connection.connect((TCP_IP, TCP_PORT))
            logger.info("TCP 서버에 성공적으로 연결됨")
        
        # 연결 상태 확인 (간단한 비차단 확인)
        _tcp_connection.setblocking(False)
        try:
            # 1바이트 읽기 시도 - 오류가 발생하면 연결은 유효함
            _tcp_connection.recv(1, socket.MSG_PEEK)
            # 데이터가 수신되면 서버가 연결을 종료했을 수 있음
            logger.warning("TCP 연결이 종료되었을 수 있습니다. 재연결 시도...")
            _tcp_connection = None
            return get_tcp_connection()
        except BlockingIOError:
            # 데이터를 읽을 수 없으면 연결이 아직 유효함
            _tcp_connection.setblocking(True)
            return _tcp_connection
        except ConnectionError:
            # 연결 오류가 발생하면 새 연결 생성
            logger.error("TCP 연결 오류 발생. 재연결 시도...")
            _tcp_connection = None
            return get_tcp_connection()
        finally:
            # 차단 모드로 다시 설정
            if _tcp_connection is not None:
                _tcp_connection.setblocking(True)
    
    except Exception as e:
        logger.error(f"TCP 연결 생성 중 오류 발생: {e}")
        # 오류 발생 시 0.5초 대기 후 재시도
        time.sleep(0.5)
        _tcp_connection = None
        return None

def send_message(message):
    """
    JSON 형식으로 메시지를 TCP 서버로 전송합니다.
    
    Args:
        message: 전송할 메시지 딕셔너리 또는 문자열
        
    Returns:
        bool: 메시지 전송 성공 여부
    """
    try:
        # 문자열이면 그대로 인코딩, 딕셔너리면 JSON으로 직렬화
        if isinstance(message, dict):
            message_str = json.dumps(message, ensure_ascii=False)
            message_type = message.get("type", "UNKNOWN")
            message_id = message.get("id", "")[:8]
            logger.debug(f"메시지 전송 시도 - 타입: {message_type}, ID: {message_id}...")
        else:
            message_str = str(message)
            logger.debug(f"문자열 메시지 전송 시도: {message_str[:50]}...")
        
        # 메시지 인코딩
        message_bytes = message_str.encode('utf-8')
        
        # 메시지 전송 (최대 3번 재시도)
        max_retries = 3
        for attempt in range(max_retries):
            try:
                sock = get_tcp_connection()
                if sock is None:
                    logger.warning(f"TCP 연결 실패 (시도 {attempt+1}/{max_retries})")
                    continue
                    
                logger.debug(f"TCP 메시지 전송 중 (시도 {attempt+1}/{max_retries})")
                sock.sendall(message_bytes)
                
                if isinstance(message, dict):
                    logger.info(f"메시지 전송 완료 - 타입: {message_type}, ID: {message_id}")
                else:
                    logger.info("문자열 메시지 전송 완료")
                return True
            
            except (ConnectionError, socket.error) as e:
                logger.error(f"TCP 메시지 전송 중 오류 발생 (시도 {attempt+1}/{max_retries}): {e}")
                # 연결 재설정
                global _tcp_connection
                if _tcp_connection is not None:
                    try:
                        _tcp_connection.close()
                    except:
                        pass
                _tcp_connection = None
                
                # 마지막 시도가 아니면 대기 후 재시도
                if attempt < max_retries - 1:
                    time.sleep(0.5)
        
        logger.error("최대 재시도 횟수 초과. 메시지 전송 실패.")
        return False
    
    except Exception as e:
        logger.error(f"메시지 전송 중 오류 발생: {e}")
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
    return send_message(message)

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