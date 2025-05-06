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
import psutil
import signal
import subprocess
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
LOCK_PORT = 28675  # 랜덤하게 선택된 포트 번호
PROCESS_NAME = "STUDY_AWS_MANAGER"  # 프로세스 이름 설정

# 디바운싱을 위한 마지막 이벤트 시간 저장 변수
_last_keyboard_event = 0
_last_mouse_movement = 0
_last_mouse_click = 0

# 오디오 형식 상수 정의
AUDIO_FORMAT = pyaudio.paInt16

# 모니터링 스레드와 상태 추적
_monitoring_active = False
_monitoring_threads = []
_lock_socket = None  # 소켓 참조 저장용

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

    # 전역 키보드 리스너 생성 - suppress=True로 다른 애플리케이션에서도 키 이벤트가 발생하도록 설정
    listener = keyboard.Listener(on_press=on_press, suppress=False)
    listener.daemon = True  # 데몬 스레드로 설정하여 메인 프로그램이 종료되면 같이 종료되도록 함
    listener.start()
    
    logger.info("키보드 리스너가 백그라운드에서 시작되었습니다")
    
    # 리스너가 종료될 때까지 대기하는 대신, 함수를 종료하여 다른 작업을 계속할 수 있게 함
    # 리스너는 백그라운드에서 계속 실행됨

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

    # 마우스 리스너 생성 및 백그라운드에서 시작
    listener = mouse.Listener(on_move=on_move, on_click=on_click)
    listener.daemon = True  # 데몬 스레드로 설정
    listener.start()
    
    logger.info("마우스 리스너가 백그라운드에서 시작되었습니다")
    # 여기에서 함수를 종료하여 리스너가 백그라운드에서 계속 실행되게 함

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
    global _monitoring_active, _monitoring_threads
    
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[logging.StreamHandler()]
    )
    
    logger.info("활동 모니터링 시작 중...")
    
    # 이미 실행 중인 경우 중지 후 재시작
    if is_already_running():
        logger.warning("활동 모니터링이 이미 실행 중입니다. 중지 후 재시작합니다.")
        
        # 이미 실행 중인 모니터링을 중지하기 위해 현재 프로세스 내에서 모니터링 중지
        stop_monitoring()
        
        # 실행 중인 다른 프로세스의 포트 해제를 위해 프로세스 강제 종료 시도
        killed = find_and_kill_lock_process()
        if killed:
            logger.info("기존 활동 모니터링 프로세스를 종료했습니다.")
            time.sleep(2)  # 프로세스가 완전히 종료될 때까지 대기
        
        # 그래도 이미 실행 중인 상태인지 확인
        if is_already_running():
            logger.error("기존 활동 모니터링 프로세스를 중지할 수 없습니다.")
            return False
    logger.info("활동 모니터링이 시작됩니다.")
    # 모니터링 활성 상태로 설정
    _monitoring_active = True
    
    # 프로세스 이름 설정
    set_process_name()
    
    # 사용자 활동 시간 초기화
    update_user_activity()
    
    # 클라이언트 연결 확인 메시지 전송
    from core.tcp_server import send_to_tcp_clients, broadcast_to_ws_clients
    connection_msg = {
        "service": "activity",
        "status": "init",
        "message": "활동 모니터링이 초기화되었습니다."
    }
    send_result = send_to_tcp_clients(connection_msg)
    logger.info(f"TCP 클라이언트 연결 확인: {'성공' if send_result else '실패 또는 클라이언트 없음'}")
    
    # WebSocket 클라이언트에게 메시지 전송 - 임시 이벤트 루프 대신 TCP 서버의 forward_activity_message 사용
    try:
        from core.tcp_server import forward_activity_message
        forward_activity_message(connection_msg)
        logger.info("WebSocket 클라이언트에게 초기화 메시지 전송 완료")
    except Exception as e:
        logger.error(f"WebSocket 메시지 전송 중 오류: {e}")
    
    # 키보드 및 마우스 활동 모니터링 시작
    keyboard_thread = threading.Thread(target=monitor_keyboard, daemon=True, name="KeyboardMonitor")
    mouse_thread = threading.Thread(target=monitor_mouse, daemon=True, name="MouseMonitor")
    screen_thread = threading.Thread(target=monitor_screen_changes, daemon=True, name="ScreenMonitor")
    audio_thread = threading.Thread(target=monitor_audio, daemon=True, name="AudioMonitor")
    
    # 스레드 시작
    keyboard_thread.start()
    mouse_thread.start()
    screen_thread.start()
    audio_thread.start()
    
    # 스레드 추적을 위해 목록에 저장

    _monitoring_threads = [keyboard_thread, mouse_thread, screen_thread, audio_thread]
    
    # 활동 모니터링 시작 메시지 전송
    start_msg = {
        "service": "activity",
        "status": "started",
        "message": "사용자 활동 모니터링이 시작되었습니다."
    }
    send_to_tcp_clients(start_msg)
    
    # WebSocket 클라이언트에게 시작 메시지 전송 - 임시 이벤트 루프 대신 TCP 서버의 forward_activity_message 사용
    try:
        forward_activity_message(start_msg)
    except Exception as e:
        logger.error(f"WebSocket 시작 메시지 전송 중 오류: {e}")
    
    logger.info("==== 사용자 활동 모니터링이 모든 채널에서 시작되었습니다 ====")
    return True

def is_monitoring_active():
    """현재 모니터링이 활성화되어 있는지 확인합니다.
    
    Returns:
        bool: 모니터링이 활성화되어 있으면 True, 아니면 False
    """
    global _monitoring_active
    return _monitoring_active

def stop_monitoring():
    """실행 중인 모니터링을 중지합니다.
    
    Returns:
        bool: 중지에 성공하면 True, 실패하면 False
    """
    global _monitoring_active, _lock_socket, _monitoring_threads
    
    if not is_monitoring_active():
        logger.info("모니터링이 이미 중지되어 있습니다.")
        return False
    
    logger.info("활동 모니터링을 중지합니다...")
    
    # 잠금 포트 해제
    if _lock_socket:
        try:
            _lock_socket.close()
            _lock_socket = None
            logger.debug("잠금 포트가 해제되었습니다.")
        except Exception as e:
            logger.error(f"잠금 포트 해제 중 오류 발생: {e}")
    
    # 스레드 종료는 daemon=True로 설정되어 있어 자동으로 처리됨
    # 하지만 모니터링 상태를 비활성으로 설정
    _monitoring_active = False
    _monitoring_threads = []
    
    # 클라이언트에게 모니터링 중지 메시지 전송
    try:
        from core.tcp_server import send_to_tcp_clients, broadcast_to_ws_clients
        stop_msg = {
            "service": "activity",
            "status": "stopped",
            "message": "사용자 활동 모니터링이 중지되었습니다."
        }
        send_to_tcp_clients(stop_msg)
        
        # WebSocket 클라이언트에게 중지 메시지 전송
        import asyncio
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        new_loop.run_until_complete(broadcast_to_ws_clients(stop_msg))
        new_loop.close()
        logger.info("모든 클라이언트에게 중지 메시지를 전송했습니다.")
    except Exception as e:
        logger.error(f"중지 메시지 전송 중 오류 발생: {e}")
    
    logger.info("==== 사용자 활동 모니터링이 중지되었습니다 ====")
    return True

def find_and_kill_lock_process():
    """
    기존 활동 모니터링 프로세스를 검색하고 종료합니다.
    
    Returns:
        bool: 성공적으로 프로세스를 종료했으면 True, 아니면 False
    """
    try:
        # 지정된 포트를 사용 중인 프로세스 찾기 (Windows용)
        netstat_command = f"netstat -ano | findstr :{LOCK_PORT}"
        logger.info(f"잠금 포트를 사용 중인 프로세스 검색 중: {LOCK_PORT}")
        
        try:
            # netstat 명령 실행
            result = subprocess.check_output(netstat_command, shell=True).decode('utf-8')
            
            # PID 추출
            pids = []
            for line in result.strip().split("\n"):
                # TCP 연결 정보 줄에서 마지막 숫자(PID)를 추출
                parts = line.strip().split()
                if len(parts) >= 5 and f":{LOCK_PORT}" in parts[1]:
                    try:
                        pid = int(parts[-1])
                        if pid not in pids:
                            pids.append(pid)
                    except ValueError:
                        continue
            
            if not pids:
                logger.warning(f"포트 {LOCK_PORT}를 사용 중인 프로세스를 찾을 수 없습니다.")
                
                # 포트가 사용 중이지만 PID를 찾을 수 없는 경우, netsh 명령으로 포트를 강제로 해제
                try:
                    logger.info(f"포트 {LOCK_PORT}를 강제로 해제합니다.")
                    os.system(f"netsh int ipv4 delete excludedportrange protocol=tcp startport={LOCK_PORT} numberofports=1")
                    time.sleep(1)
                    # 포트 강제 해제 후 대기
                    return True
                except Exception as e:
                    logger.error(f"포트 강제 해제 중 오류: {e}")
                
                return False
                
            logger.info(f"잠금 포트를 사용 중인 프로세스 발견: PID {pids}")
            
            # 모든 발견된 프로세스 종료 시도
            success = False
            for pid in pids:
                try:
                    # Windows에서는 taskkill을 먼저 시도 (더 강력함)
                    if os.name == 'nt':
                        try:
                            logger.info(f"taskkill로 프로세스 강제 종료 시도: PID {pid}")
                            subprocess.call(f'taskkill /F /PID {pid}', shell=True)
                            logger.info(f"taskkill로 프로세스 종료 명령 전송 완료: PID {pid}")
                            success = True
                        except Exception as e:
                            logger.error(f"taskkill로 프로세스 종료 중 오류 발생 (PID: {pid}): {e}")
                    
                    # 만약 taskkill이 실패했거나 Windows가 아닌 경우 psutil 시도
                    if not success or os.name != 'nt':
                        try:
                            process = psutil.Process(pid)
                            process_name = process.name()
                            logger.info(f"프로세스 정보: {process_name} (PID: {pid})")
                            
                            # 강제 종료 바로 시도
                            process.kill()
                            logger.info(f"프로세스 강제 종료 성공: {process_name} (PID: {pid})")
                            success = True
                        except psutil.NoSuchProcess:
                            logger.warning(f"PID {pid}에 해당하는 프로세스가 이미 종료되었습니다.")
                            success = True
                        except Exception as e:
                            logger.error(f"psutil로 프로세스 종료 시도 중 오류 발생 (PID: {pid}): {e}")
                
                except Exception as e:
                    logger.error(f"프로세스 종료 처리 중 오류 발생 (PID: {pid}): {e}")
            
            # 포트가 해제될 때까지 더 오래 대기 (10초)
            logger.info("프로세스 종료 후 포트 해제를 위해 10초간 대기...")
            time.sleep(10)
            
            # 포트가 아직도 사용 중인지 확인
            try:
                test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                test_socket.bind(('localhost', LOCK_PORT))
                test_socket.close()
                logger.info("포트가 성공적으로 해제되었습니다.")
                return True
            except socket.error:
                logger.warning("포트가 여전히 사용 중입니다. 강제 해제를 시도합니다.")
                try:
                    # Windows에서 netsh 명령으로 포트 강제 해제
                    os.system(f"netsh int ipv4 delete excludedportrange protocol=tcp startport={LOCK_PORT} numberofports=1")
                    time.sleep(2)
                    return True
                except Exception as e:
                    logger.error(f"포트 강제 해제 중 오류: {e}")
                    return False
            
            return success
                
        except subprocess.CalledProcessError:
            logger.info(f"포트 {LOCK_PORT}를 사용 중인 프로세스가 없습니다.")
            return True  # 프로세스가 없으면 성공으로 처리
            
    except Exception as e:
        logger.error(f"프로세스 검색 및 종료 중 오류 발생: {e}")
        return False