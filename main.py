"""
AWS 서비스 관리 및 사용자 활동 모니터링 애플리케이션의 메인 실행 파일
"""
import time
import sys
import logging
import tkinter as tk
from tkinter import messagebox

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

def main():
    """애플리케이션의 메인 함수"""
    logger.info("AWS 서비스 관리 및 사용자 활동 모니터링 애플리케이션을 시작합니다...")
    
    # 중복 실행 체크
    if activity_monitor.is_already_running():
        # GUI로 중복 실행 메시지 표시
        root = tk.Tk()
        root.withdraw()  # 메인 윈도우 숨기기
        messagebox.showerror("오류", "프로그램이 이미 실행 중입니다!")
        root.destroy()
        logger.warning("프로그램이 이미 실행 중입니다. 종료합니다.")
        return
    
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
    
    # TCP 서버 시작
    tcp_server.run_server()
    logger.info(f"TCP 서버가 포트 {config.get('tcp_server', 'port', 20200)}에서 시작되었습니다.")
    
    # 사용자 활동 모니터링 시작
    activity_monitor.start_monitoring()
    
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