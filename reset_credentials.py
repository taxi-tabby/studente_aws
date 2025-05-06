"""
AWS 자격 증명 초기화 도구
"""
import os
import sys
import logging
import tkinter as tk
from tkinter import messagebox, ttk

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("aws_credential_reset.log", encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)

def reset_aws_credentials():
    """AWS 자격 증명 파일을 초기화합니다."""
    credentials_file = os.path.join(os.path.expanduser("~"), ".aws_monitor_credentials")
    
    try:
        # 자격 증명 파일이 있는지 확인
        if not os.path.exists(credentials_file):
            return False, "자격 증명 파일이 존재하지 않습니다. 초기화가 필요하지 않습니다."
        
        # 자격 증명 파일 삭제
        os.remove(credentials_file)
        logger.info("AWS 자격 증명 파일을 성공적으로 삭제했습니다.")
        return True, "AWS 자격 증명이 성공적으로 초기화되었습니다."
    except Exception as e:
        error_msg = f"자격 증명 초기화 중 오류 발생: {str(e)}"
        logger.error(error_msg)
        return False, error_msg

def main():
    # GUI 설정
    root = tk.Tk()
    root.title("AWS 자격 증명 초기화")
    root.geometry("460x240")
    root.resizable(False, False)
    
    # 화면 중앙에 위치
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width - 460) // 2
    y = (screen_height - 240) // 2
    root.geometry(f"460x240+{x}+{y}")
    
    # 스타일 설정
    style = ttk.Style(root)
    style.configure("TLabel", font=("Arial", 12))
    style.configure("TButton", font=("Arial", 12))
    style.configure("Title.TLabel", font=("Arial", 14, "bold"))
    style.configure("Status.TLabel", font=("Arial", 12))
    
    # 프레임 생성
    frame = ttk.Frame(root, padding=20)
    frame.pack(fill=tk.BOTH, expand=True)
    
    # 제목
    ttk.Label(frame, text="AWS 자격 증명 초기화", style="Title.TLabel").pack(pady=(0, 20))
    
    # 설명 텍스트
    description = ("이 도구는 저장된 AWS 자격 증명을 초기화합니다.\n"
                   "초기화하면 다음번 프로그램 실행 시 새로운 자격 증명 입력이 필요합니다.\n\n"
                   "계속하시겠습니까?")
    ttk.Label(frame, text=description, justify=tk.CENTER, wraplength=400).pack(pady=(0, 20))
    
    # 상태 표시 레이블
    status_var = tk.StringVar()
    status_label = ttk.Label(frame, textvariable=status_var, style="Status.TLabel", foreground="blue")
    status_label.pack(pady=(0, 20))
    
    # 버튼 프레임
    button_frame = ttk.Frame(frame)
    button_frame.pack(fill=tk.X)
    
    # 초기화 이벤트 처리
    def on_reset_credentials():
        # 초기화 전 확인 메시지
        if messagebox.askyesno("확인", "정말로 AWS 자격 증명을 초기화하시겠습니까?"):
            # 비활성화
            reset_button.config(state="disabled")
            cancel_button.config(state="disabled")
            
            # 초기화 처리
            success, message = reset_aws_credentials()
            
            # 결과 표시
            if success:
                status_var.set(message)
                status_label.config(foreground="green")
                messagebox.showinfo("완료", message)
                # 2초 후 창 닫기
                root.after(2000, root.destroy)
            else:
                status_var.set(message)
                status_label.config(foreground="red")
                messagebox.showerror("오류", message)
                reset_button.config(state="normal")
                cancel_button.config(state="normal")
    
    # 초기화 버튼
    reset_button = ttk.Button(button_frame, text="초기화", command=on_reset_credentials)
    reset_button.pack(side=tk.LEFT, padx=(50, 10))
    
    # 취소 버튼
    cancel_button = ttk.Button(button_frame, text="취소", command=root.destroy)
    cancel_button.pack(side=tk.RIGHT, padx=(10, 50))
    
    # 실행
    root.mainloop()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())