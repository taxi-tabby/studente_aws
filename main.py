"""
AWS 서비스 관리 및 사용자 활동 모니터링 애플리케이션의 메인 실행 파일
"""
import time
import sys
import logging
import tkinter as tk
from tkinter import messagebox
import threading

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("aws_monitor.log", encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)

# 모듈 임포트
from core import activity_monitor
from core import tcp_server
from core.aws_auth import aws_auth
from core.config.config_loader import config

def start_activity_monitoring_async():
    """활동 모니터링을 별도 스레드에서 시작합니다."""
    # 최대 3번까지 재시도
    for attempt in range(3):
        try:
            logger.info(f"활동 모니터링 시작 시도 중... (시도 {attempt+1}/3)")
            if activity_monitor.start_monitoring():
                logger.info("활동 모니터링이 성공적으로 시작되었습니다.")
                return True
            else:
                logger.warning(f"활동 모니터링 시작 실패. {attempt+1}번 째 시도.")
                time.sleep(3)  # 3초 대기 후 재시도
        except Exception as e:
            logger.error(f"활동 모니터링 시작 중 오류 발생: {e}")
            time.sleep(3)
    
    logger.error("활동 모니터링을 시작할 수 없습니다. 최대 재시도 횟수를 초과했습니다.")
    return False

def main():
    """애플리케이션의 메인 함수"""
    logger.info("AWS 서비스 관리 및 사용자 활동 모니터링 애플리케이션을 시작합니다...")
    
    # 중복 실행 체크는 모니터링 시작시 처리하도록 변경
    # if activity_monitor.is_already_running():
    #     # GUI로 중복 실행 메시지 표시
    #     root = tk.Tk()
    #     root.withdraw()  # 메인 윈도우 숨기기
    #     messagebox.showerror("오류", "프로그램이 이미 실행 중입니다!")
    #     root.destroy()
    #     logger.warning("프로그램이 이미 실행 중입니다. 종료합니다.")
    #     return
    
    # AWS 인증 처리
    logger.info("AWS 인증을 시작합니다...")
    if not aws_auth.show_auth_dialog():  # authenticate() 대신 show_auth_dialog() 사용
        logger.error("AWS 인증에 실패했습니다. 프로그램을 종료합니다.")
        # GUI로 인증 실패 메시지 표시
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("인증 실패", "AWS 인증에 실패했습니다. 프로그램을 종료합니다.")
        root.destroy()
        sys.exit(1)
    
    logger.info("AWS 인증이 성공적으로 완료되었습니다.")
    
    # 이벤트 루프와 WebSocket 서버 초기화를 위한 별도 함수
    def initialize_event_loop_and_websocket():
        import asyncio
        from core import tcp_server
        
        # 이벤트 루프 생성 및 설정
        logger.info("이벤트 루프 생성 및 WebSocket 서버 초기화 중...")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # 웹소켓 서버 초기화 및 실행
        try:
            asyncio.run_coroutine_threadsafe(tcp_server.start_websocket_server(), loop)
            logger.info(f"WebSocket 서버가 포트 {tcp_server.WS_PORT}에서 시작되었습니다.")
        except Exception as e:
            logger.error(f"WebSocket 서버 시작 중 오류 발생: {e}")
            import traceback
            logger.error(f"에러 상세 정보: {traceback.format_exc()}")
            
        # 이벤트 루프 실행
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            logger.info("키보드 인터럽트로 이벤트 루프 종료")
        except Exception as e:
            logger.error(f"이벤트 루프 실행 중 오류 발생: {e}")
        finally:
            loop.close()
            logger.info("이벤트 루프가 종료되었습니다.")
    
    # WebSocket 서버 시작 (별도 스레드에서)
    ws_thread = threading.Thread(target=initialize_event_loop_and_websocket)
    ws_thread.daemon = True
    ws_thread.start()
    
    # TCP 서버 시작 (별도 스레드에서)
    tcp_thread = threading.Thread(target=tcp_server.start_tcp_server)
    tcp_thread.daemon = True
    tcp_thread.start()
    logger.info(f"TCP 서버가 포트 {tcp_server.TCP_PORT}에서 시작되었습니다.")
    
    # 사용자 활동 모니터링 시작 (별도 스레드에서)
    activity_thread = threading.Thread(target=start_activity_monitoring_async)
    activity_thread.daemon = True
    activity_thread.start()
    
    # 프로그램이 계속 실행되도록 유지
    logger.info("모든 서비스가 시작되었습니다. 프로그램을 종료하려면 Ctrl+C를 누르세요.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("프로그램을 종료합니다...")
    except Exception as e:
        logger.error(f"예기치 않은 오류가 발생했습니다: {e}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())