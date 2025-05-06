"""
사용자 활동(키보드, 마우스, 화면 변화, 소리 재생 등) 모니터링 모듈
"""
import threading
import time
import os
import tempfile
import socket
import numpy as np
import pyautogui
import cv2
import pyaudio
import ctypes
import logging
from pynput import keyboard, mouse
from win32gui import GetForegroundWindow, GetWindowText
from core.messages import message_format
from core.config.config_loader import config
from core.service_manager import service_manager

# 로거 설정
logger = logging.getLogger(__name__)

# 설정에서 값 로드
def _get_setting(key, default_value):
    """설정에서 특정 키에 대한 값을 가져옵니다."""
    return config.get("activity_monitor", key, default_value)

# 중복 실행 방지용 임시 파일 및 포트
LOCK_FILE = os.path.join(tempfile.gettempdir(), "aws_study_activity_monitor.lock")
LOCK_PORT = 38675  # 랜덤하게 선택된 포트 번호
PROCESS_NAME = "STUDY_AWS_MANAGER"  # 프로세스 이름 설정

# 디바운싱을 위한 마지막 이벤트 시간 저장 변수
_last_keyboard_event = 0
_last_mouse_movement = 0
_last_mouse_click = 0

# 오디오 형식 상수 정의
AUDIO_FORMAT = pyaudio.paInt16

def set_process_name():
    """프로세스 이름을 설정합니다."""
    try:
        # Windows에서 프로세스 이름 변경
        if hasattr(ctypes, 'windll'):
            try:
                ctypes.windll.kernel32.SetConsoleTitleW(PROCESS_NAME)
                logger.info(f"프로세스 이름이 '{PROCESS_NAME}'으로 설정되었습니다.")
            except Exception as e:
                logger.error(f"Windows 프로세스 이름 설정 중 오류 발생: {e}")
        # Linux/Unix에서 프로세스 이름 변경 (미지원)
        else:
            logger.warning("현재 플랫폼에서는 프로세스 이름을 변경할 수 없습니다.")
    except Exception as e:
        logger.error(f"프로세스 이름 설정 중 오류 발생: {e}")

def is_already_running():
    """프로그램이 이미 실행 중인지 확인합니다.
    
    Returns:
        bool: 이미 실행 중이면 True, 아니면 False
    """
    # 소켓 잠금 시도
    try:
        lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        lock_socket.bind(('localhost', LOCK_PORT))
        lock_socket.listen(1)
        
        # 소켓 참조를 유지하기 위해 전역 변수에 저장
        global _lock_socket
        _lock_socket = lock_socket
        logger.debug("잠금 포트 점유 성공 - 첫 번째 인스턴스로 실행 중")
        return False
    except socket.error:
        # 포트가 이미 사용 중이면 프로그램이 실행 중
        logger.warning("잠금 포트가 이미 점유됨 - 이미 다른 인스턴스가 실행 중")
        return True

def update_user_activity():
    """사용자 활동 시간 업데이트"""
    service_manager.update_activity_time()
    logger.debug("사용자 활동 시간 업데이트됨")

def monitor_keyboard():
    """키보드 활동을 모니터링합니다."""
    # 설정에서 키보드 모니터링 활성화 여부 확인
    if not _get_setting("keyboard", {}).get("enabled", True):
        logger.info("키보드 활동 모니터링이 비활성화되어 있습니다.")
        return
    
    # 디바운스 시간(밀리초) 설정
    debounce_ms = _get_setting("keyboard", {}).get("debounce_ms", 500)
    logger.info(f"키보드 활동 모니터링 시작됨 (디바운스: {debounce_ms}ms)")
    
    def on_press(key):
        global _last_keyboard_event
        current_time = time.time() * 1000  # 현재 시간(밀리초)
        
        # 디바운싱: 마지막 이벤트 이후 일정 시간이 지났을 때만 처리
        if (current_time - _last_keyboard_event) > debounce_ms:
            logger.debug(f"키보드 이벤트 감지: {key} - 메시지 전송 시도")
            result = message_format.send_keyboard_activity()
            if result:
                logger.debug("키보드 활동 메시지 전송 성공")
            else:
                logger.warning("키보드 활동 메시지 전송 실패")
            update_user_activity()
            _last_keyboard_event = current_time
        else:
            logger.debug(f"키보드 이벤트 무시됨 (디바운스 중): {current_time - _last_keyboard_event}ms")

    with keyboard.Listener(on_press=on_press) as listener:
        logger.info("키보드 리스너 시작됨")
        listener.join()

def monitor_mouse():
    """마우스 활동을 모니터링합니다."""
    # 설정에서 마우스 모니터링 활성화 여부 확인
    if not _get_setting("mouse", {}).get("enabled", True):
        logger.info("마우스 활동 모니터링이 비활성화되어 있습니다.")
        return
    
    # 디바운스 시간(밀리초) 설정
    movement_debounce_ms = _get_setting("mouse", {}).get("movement_debounce_ms", 1000)
    click_debounce_ms = _get_setting("mouse", {}).get("click_debounce_ms", 500)
    logger.info(f"마우스 활동 모니터링 시작됨 (이동 디바운스: {movement_debounce_ms}ms, 클릭 디바운스: {click_debounce_ms}ms)")

    def on_move(x, y):
        global _last_mouse_movement
        current_time = time.time() * 1000  # 현재 시간(밀리초)
        
        # 디바운싱: 마지막 이벤트 이후 일정 시간이 지났을 때만 처리
        if (current_time - _last_mouse_movement) > movement_debounce_ms:
            logger.debug(f"마우스 이동 감지: ({x},{y}) - 메시지 전송 시도")
            result = message_format.send_mouse_movement()
            if result:
                logger.debug("마우스 이동 메시지 전송 성공")
            else:
                logger.warning("마우스 이동 메시지 전송 실패")
            update_user_activity()
            _last_mouse_movement = current_time
        else:
            logger.debug(f"마우스 이동 무시됨 (디바운스 중): {current_time - _last_mouse_movement}ms")

    def on_click(x, y, button, pressed):
        global _last_mouse_click
        current_time = time.time() * 1000  # 현재 시간(밀리초)
        
        # 버튼이 눌렸을 때만, 디바운싱 적용
        if pressed and (current_time - _last_mouse_click) > click_debounce_ms:
            logger.debug(f"마우스 클릭 감지: ({x},{y}, {button}) - 메시지 전송 시도")
            result = message_format.send_mouse_click()
            if result:
                logger.debug("마우스 클릭 메시지 전송 성공")
            else:
                logger.warning("마우스 클릭 메시지 전송 실패")
            update_user_activity()
            _last_mouse_click = current_time
        elif pressed:
            logger.debug(f"마우스 클릭 무시됨 (디바운스 중): {current_time - _last_mouse_click}ms")

    with mouse.Listener(on_move=on_move, on_click=on_click) as listener:
        logger.info("마우스 리스너 시작됨")
        listener.join()

def monitor_screen_changes():
    """화면 변화를 모니터링합니다."""
    # 설정에서 화면 모니터링 활성화 여부 확인
    if not _get_setting("screen", {}).get("enabled", True):
        logger.info("화면 변화 모니터링이 비활성화되어 있습니다.")
        return
    
    # 설정에서 캡처 간격 및 유사도 임계값 로드
    capture_interval = _get_setting("screen", {}).get("capture_interval_sec", 2)
    threshold = _get_setting("screen", {}).get("change_threshold", 0.8)
    logger.info(f"화면 변화 모니터링 시작됨 (간격: {capture_interval}초, 임계값: {threshold})")
    
    prev_screenshot = None
    cycle_count = 0
    
    while True:
        try:
            # 현재 화면 캡처
            screenshot = pyautogui.screenshot()
            screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)
            
            # 이전 화면과 비교
            if prev_screenshot is not None:
                # 이미지 크기를 맞추기
                if prev_screenshot.shape != screenshot.shape:
                    prev_screenshot = cv2.resize(prev_screenshot, (screenshot.shape[1], screenshot.shape[0]))
                
                # 구조적 유사성 계산
                similarity = cv2.matchTemplate(prev_screenshot, screenshot, cv2.TM_CCOEFF_NORMED)[0][0]
                
                # 정기적으로 화면 감지 상태 기록 (20회마다)
                cycle_count += 1
                if cycle_count % 20 == 0:
                    logger.debug(f"화면 유사성 검사: {similarity:.4f} (임계값: {threshold})")
                    cycle_count = 0
                
                # 유사성이 임계값보다 낮으면 화면 변화로 간주
                if similarity < threshold:
                    logger.debug(f"화면 변화 감지 (유사성: {similarity:.4f}) - 메시지 전송 시도")
                    result = message_format.send_screen_change()
                    if result:
                        logger.debug("화면 변화 메시지 전송 성공")
                    else:
                        logger.warning("화면 변화 메시지 전송 실패")
                    update_user_activity()
            
            # 현재 화면을 이전 화면으로 저장
            prev_screenshot = screenshot
            
            # 현재 활성 창 이름 가져오기
            active_window = GetWindowText(GetForegroundWindow())
            if active_window:
                logger.debug(f"활성 창 감지: {active_window} - 메시지 전송 시도")
                result = message_format.send_active_window(active_window)
                if result:
                    logger.debug("활성 창 메시지 전송 성공")
                else:
                    logger.warning("활성 창 메시지 전송 실패")
                update_user_activity()
                
            # 대기
            time.sleep(capture_interval)
            
        except Exception as e:
            logger.error(f"화면 모니터링 중 오류 발생: {e}")
            time.sleep(capture_interval)

def monitor_audio():
    """오디오 재생 여부를 모니터링합니다."""
    # 설정에서 오디오 모니터링 활성화 여부 확인
    if not _get_setting("audio", {}).get("enabled", True):
        logger.info("오디오 재생 모니터링이 비활성화되어 있습니다.")
        return
    
    # 설정에서 오디오 관련 설정 로드
    rate = _get_setting("audio", {}).get("sample_rate", 44100)
    channels = _get_setting("audio", {}).get("channels", 1)
    chunk = _get_setting("audio", {}).get("chunk_size", 1024)
    threshold = _get_setting("audio", {}).get("threshold", 500)
    interval_ms = _get_setting("audio", {}).get("check_interval_ms", 100)
    
    logger.info(f"오디오 모니터링 시작됨 (샘플레이트: {rate}, 채널: {channels}, 청크크기: {chunk}, 임계값: {threshold})")
    p = pyaudio.PyAudio()
    
    try:
        stream = p.open(format=AUDIO_FORMAT,
                        channels=channels,
                        rate=rate,
                        input=True,
                        frames_per_buffer=chunk)
        logger.debug("오디오 스트림 열기 성공")
        
        cycle_count = 0
        
        while True:
            try:
                # 오디오 데이터 읽기
                data = np.frombuffer(stream.read(chunk, exception_on_overflow=False), dtype=np.int16)
                
                # 볼륨 레벨 계산
                volume = np.abs(data).mean()
                
                # 정기적으로 오디오 감지 상태 기록 (50회마다)
                cycle_count += 1
                if cycle_count % 50 == 0:
                    logger.debug(f"오디오 볼륨 레벨: {volume} (임계값: {threshold})")
                    cycle_count = 0
                
                # 볼륨 레벨이 임계값보다 높으면 소리 재생으로 간주
                if volume > threshold:
                    logger.debug(f"오디오 재생 감지 (볼륨: {volume}) - 메시지 전송 시도")
                    result = message_format.send_audio_playback(int(volume))
                    if result:
                        logger.debug("오디오 재생 메시지 전송 성공")
                    else:
                        logger.warning("오디오 재생 메시지 전송 실패")
                    update_user_activity()
                
                time.sleep(interval_ms / 1000)  # 밀리초를 초로 변환
                
            except Exception as e:
                logger.error(f"오디오 모니터링 중 오류 발생: {e}")
                time.sleep(1)
                
    except Exception as e:
        logger.error(f"오디오 스트림 열기 실패: {e}")
    
    finally:
        if 'stream' in locals():
            stream.stop_stream()
            stream.close()
        p.terminate()

def start_monitoring():
    """키보드, 마우스, 화면, 오디오 활동 모니터링을 시작합니다."""
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[logging.StreamHandler()]
    )
    
    logger.info("활동 모니터링 시작 중...")
    
    # 중복 실행 확인
    if is_already_running():
        logger.warning("프로그램이 이미 실행 중입니다. 중복 실행이 방지되었습니다.")
        return False
    
    # 프로세스 이름 설정
    set_process_name()
    
    # 사용자 활동 시간 초기화
    update_user_activity()
    
    # 키보드 및 마우스 활동 모니터링 시작
    threading.Thread(target=monitor_keyboard, daemon=True, name="KeyboardMonitor").start()
    threading.Thread(target=monitor_mouse, daemon=True, name="MouseMonitor").start()
    
    # 화면 변화 모니터링 시작
    threading.Thread(target=monitor_screen_changes, daemon=True, name="ScreenMonitor").start()
    
    # 오디오 재생 모니터링 시작
    threading.Thread(target=monitor_audio, daemon=True, name="AudioMonitor").start()
    
    logger.info("==== 사용자 활동 모니터링이 모든 채널에서 시작되었습니다 ====")
    return True