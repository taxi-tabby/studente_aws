"""
AWS 인증 관리 모듈
"""
import os
import json
import logging
import tkinter as tk
from tkinter import ttk, messagebox
import boto3
from botocore.exceptions import ClientError
import threading

# 로거 설정
logger = logging.getLogger(__name__)

class AWSAuth:
    """AWS 인증 관리 클래스"""
    
    def __init__(self):
        """초기화"""
        self.credentials_file = os.path.join(os.path.expanduser("~"), ".aws_monitor_credentials")
        self.session = None
        self.credentials = {
            'aws_access_key_id': '',
            'aws_secret_access_key': '',
            'region_name': None
        }
        self.load_credentials()
    
    def load_credentials(self):
        """저장된 자격 증명 로드"""
        try:
            if os.path.exists(self.credentials_file):
                with open(self.credentials_file, "r", encoding="utf-8") as f:
                    self.credentials = json.load(f)
                logger.info("저장된 AWS 자격 증명을 로드했습니다.")
                # 저장된 자격 증명으로 세션 생성
                self.create_session()
                return True
        except Exception as e:
            logger.error(f"자격 증명 로드 중 오류 발생: {e}")
        
        logger.info("저장된 AWS 자격 증명이 없습니다.")
        return False
    
    def save_credentials(self):
        """자격 증명 저장"""
        try:
            with open(self.credentials_file, "w", encoding="utf-8") as f:
                json.dump(self.credentials, f)
            logger.info("AWS 자격 증명이 저장되었습니다.")
            return True
        except Exception as e:
            logger.error(f"자격 증명 저장 중 오류 발생: {e}")
            return False
    
    def create_session(self):
        """AWS 세션 생성"""
        try:
            # 리전 관련 파라미터는 None이 아닐 때만 포함시킵니다
            session_kwargs = {
                'aws_access_key_id': self.credentials['aws_access_key_id'],
                'aws_secret_access_key': self.credentials['aws_secret_access_key']
            }
            
            # 리전이 지정된 경우에만 포함
            if self.credentials.get('region_name'):
                session_kwargs['region_name'] = self.credentials['region_name']
            
            self.session = boto3.Session(**session_kwargs)
            logger.info("AWS 세션이 생성되었습니다.")
            return True
        except Exception as e:
            logger.error(f"AWS 세션 생성 중 오류 발생: {e}")
            self.session = None
            return False
    
    def validate_credentials(self, access_key, secret_key, region=None):
        """AWS 자격 증명 유효성 검사
        
        Args:
            access_key (str): AWS Access Key ID
            secret_key (str): AWS Secret Access Key
            region (str, optional): AWS 리전 (선택 사항)
            
        Returns:
            bool: 자격 증명 유효성 여부
        """
        # 입력값 기본 검증
        if not access_key or not secret_key:
            logger.error("AWS 자격 증명이 비어있습니다.")
            return False
            
        # 기본적인 형식 검증
        if not access_key.startswith('AK') or len(access_key) < 16:
            logger.error("AWS Access Key ID 형식이 올바르지 않습니다.")
            return False
            
        if len(secret_key) < 16:
            logger.error("AWS Secret Access Key 형식이 올바르지 않습니다.")
            return False
            
        try:
            # 네트워크 연결 상태 확인
            logger.info("AWS API 엔드포인트 연결 확인 중...")
            try:
                import socket
                # STS 엔드포인트 직접 사용
                sts_endpoint = "sts.amazonaws.com"
                logger.debug(f"{sts_endpoint}에 연결 시도 중...")
                socket.create_connection((sts_endpoint, 443), timeout=5)
                logger.info(f"{sts_endpoint} 연결 확인: 성공")
            except Exception as e:
                logger.error(f"AWS API 엔드포인트 연결 실패: {str(e)}")
                return False
                
            # 임시 세션으로 STS 호출하여 자격 증명 확인
            logger.info("AWS 자격 증명 검증을 시작합니다.")
            
            # 리전 관련 파라미터는 None이 아닐 때만 포함시킵니다
            session_kwargs = {
                'aws_access_key_id': access_key,
                'aws_secret_access_key': secret_key
            }
            
            if region:
                session_kwargs['region_name'] = region
            else:
                # 기본 리전 설정 - 글로벌 STS 서비스 사용을 위해
                session_kwargs['region_name'] = 'us-east-1'
                logger.debug("기본 리전 (us-east-1)을 사용합니다.")
                
            temp_session = boto3.Session(**session_kwargs)
            logger.debug("임시 세션 생성 완료")
            
            # STS 클라이언트에 타임아웃 설정
            logger.debug("STS 클라이언트 생성 중...")
            sts_client = temp_session.client('sts', 
                config=boto3.session.Config(
                    connect_timeout=10,  # 연결 타임아웃 10초
                    read_timeout=15      # 읽기 타임아웃 15초
                )
            )
            
            logger.info("STS 서비스에 자격 증명 확인 요청 중...")
            response = sts_client.get_caller_identity()
            
            # 응답 확인
            account_id = response.get('Account')
            user_id = response.get('UserId')
            arn = response.get('Arn')
            
            logger.info(f"AWS 자격 증명이 유효합니다. 계정: {account_id}, 사용자: {user_id}")
            logger.debug(f"인증된 사용자 ARN: {arn}")
            return True
            
        except ClientError as e:
            error_code = getattr(e, 'response', {}).get('Error', {}).get('Code', '')
            error_msg = getattr(e, 'response', {}).get('Error', {}).get('Message', '')
            
            if error_code == 'InvalidClientTokenId':
                logger.error(f"액세스 키가 유효하지 않습니다: {error_msg}")
                return False
            elif error_code == 'SignatureDoesNotMatch':
                logger.error(f"시크릿 키가 액세스 키와 일치하지 않습니다: {error_msg}")
                return False
            elif error_code == 'ExpiredToken':
                logger.error(f"자격 증명이 만료되었습니다: {error_msg}")
                return False
            elif error_code == 'AccessDenied':
                logger.error(f"권한이 없습니다: {error_msg}")
                return False
            else:
                logger.error(f"AWS 자격 증명 검증 실패: {error_code} - {error_msg}")
                
            # 전체 오류 정보 로깅
            logger.debug(f"AWS 자격 증명 검증 상세 오류: {str(e)}")
            return False
        except ConnectionError as e:
            logger.error(f"AWS 서비스 연결 실패: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"AWS 자격 증명 검증 중 예상치 못한 오류 발생: {str(e)}")
            logger.exception("상세 오류 정보:")
            return False
    
    def is_authenticated(self):
        """현재 인증 상태 확인
        
        Returns:
            bool: 인증 여부
        """
        if not self.session:
            return False
        
        try:
            sts_client = self.session.client('sts')
            sts_client.get_caller_identity()
            return True
        except:
            return False
    
    def show_auth_dialog(self, parent=None):
        """AWS 인증 다이얼로그 표시
        
        Args:
            parent (tk.Tk): 부모 윈도우
            
        Returns:
            bool: 인증 성공 여부
        """
        # 이미 인증되어 있으면 바로 True 반환
        if self.is_authenticated():
            return True
            
        # 결과를 저장할 변수
        auth_result = [False]
        auth_data = {'access_key': '', 'secret_key': '', 'save': True}

        # 메인 스레드에서 실행하는 함수
        def run_auth_ui():
            nonlocal parent
            
            # 창 생성
            root_created = False
            if not parent:
                root = tk.Tk()
                root.title("AWS 인증")
                root_created = True
            else:
                root = parent
                
            dialog = tk.Toplevel(root)
            dialog.title("AWS 인증")
            dialog.geometry("960x520")
            dialog.resizable(False, False)
            dialog.grab_set()  # 모달 다이얼로그로 설정
            
            # 중앙에 위치
            dialog.update_idletasks()
            width = dialog.winfo_width()
            height = dialog.winfo_height()
            x = (dialog.winfo_screenwidth() // 2) - (width // 2)
            y = (dialog.winfo_screenheight() // 2) - (height // 2)
            dialog.geometry(f"{width}x{height}+{x}+{y}")
            
            # 스타일 설정
            style = ttk.Style(dialog)
            style.configure("TLabel", font=("Arial", 12))
            style.configure("TButton", font=("Arial", 12))
            style.configure("TEntry", font=("Arial", 12))
            
            # 제목
            ttk.Label(dialog, text="AWS 자격 증명 입력", font=("Arial", 14, "bold")).grid(
                row=0, column=0, columnspan=2, pady=(20, 25), padx=15, sticky="w"
            )
            
            # Access Key ID
            ttk.Label(dialog, text="Access Key ID:").grid(
                row=1, column=0, padx=15, pady=8, sticky="w"
            )
            access_key_var = tk.StringVar(value=self.credentials.get('aws_access_key_id', ''))
            access_key_entry = ttk.Entry(dialog, width=45, textvariable=access_key_var)
            access_key_entry.grid(row=1, column=1, padx=15, pady=8)
            
            # Secret Access Key
            ttk.Label(dialog, text="Secret Access Key:").grid(
                row=2, column=0, padx=15, pady=8, sticky="w"
            )
            secret_key_var = tk.StringVar(value=self.credentials.get('aws_secret_access_key', ''))
            secret_key_entry = ttk.Entry(dialog, width=45, textvariable=secret_key_var, show="*")
            secret_key_entry.grid(row=2, column=1, padx=15, pady=8)
            
            # 자격 증명 저장 체크박스
            save_var = tk.BooleanVar(value=True)
            save_check = ttk.Checkbutton(dialog, text="자격 증명 저장", variable=save_var)
            save_check.grid(row=3, column=0, columnspan=2, padx=10, pady=(10, 0), sticky="w")
            
            # 상태 표시 레이블
            status_var = tk.StringVar()
            status_label = ttk.Label(dialog, textvariable=status_var, foreground="red")
            status_label.grid(row=4, column=0, columnspan=2, padx=10, pady=(5, 10))
            
            # 진행 표시줄
            progress_bar = ttk.Progressbar(dialog, orient="horizontal", 
                                         length=400, mode="indeterminate")
            progress_bar.grid(row=5, column=0, columnspan=2, padx=10, pady=(5, 10))
            progress_bar.grid_remove()  # 처음에는 숨겨둠
            
            # 인증 결과 확인 버튼 클릭 이벤트
            def on_check_auth():
                # 입력값 검증
                access_key = access_key_var.get().strip()
                secret_key = secret_key_var.get().strip()
                
                if not access_key or not secret_key:
                    status_var.set("Access Key와 Secret Key를 입력하세요.")
                    return
                
                # 버튼 비활성화
                auth_button.config(state="disabled")
                cancel_button.config(state="disabled")
                
                # 상태 업데이트
                status_var.set("인증 시도 중...")
                status_label.config(foreground="blue")
                
                # 진행 표시줄 보이기
                progress_bar.grid()
                progress_bar.start(10)
                
                # 인증 정보 저장
                auth_data['access_key'] = access_key
                auth_data['secret_key'] = secret_key
                auth_data['save'] = save_var.get()
                
                # 다이얼로그 닫기
                dialog.destroy()
            
            # 버튼 프레임
            button_frame = ttk.Frame(dialog)
            button_frame.grid(row=6, column=0, columnspan=2, pady=(15, 15))
            
            # 인증 확인 버튼
            auth_button = ttk.Button(button_frame, text="인증", command=on_check_auth)
            auth_button.pack(side=tk.LEFT, padx=5)
            
            # 취소 버튼 - 그냥 창만 닫음
            cancel_button = ttk.Button(button_frame, text="취소", command=dialog.destroy)
            cancel_button.pack(side=tk.LEFT, padx=5)
            
            # 처음 포커스 설정
            if not access_key_var.get():
                access_key_entry.focus()
            elif not secret_key_var.get():
                secret_key_entry.focus()
            else:
                auth_button.focus()
                
            # Enter 키로 인증 버튼 클릭 이벤트 연결
            dialog.bind("<Return>", lambda e: on_check_auth())
            
            # 모달 다이얼로그로 표시
            dialog.transient(root)
            dialog.wait_window()
            
            # 임시 root 창 닫기
            if root_created and root.winfo_exists():
                root.destroy()
        
        # 메인 스레드에서 GUI 실행
        if threading.current_thread() is threading.main_thread():
            # 이미 메인 스레드라면 직접 실행
            run_auth_ui()
        else:
            # 작업 스레드에서 호출된 경우 메인 스레드로 전달할 방법이 필요
            # 여기서는 간단히 오류 로깅으로 처리
            logger.error("AWS 인증 다이얼로그는 메인 스레드에서만 호출할 수 있습니다.")
            return False
            
        # 사용자가 입력한 인증 정보로 검증 시도
        if auth_data['access_key'] and auth_data['secret_key']:
            try:
                if self.validate_credentials(auth_data['access_key'], auth_data['secret_key']):
                    # 자격 증명 저장
                    self.credentials = {
                        'aws_access_key_id': auth_data['access_key'],
                        'aws_secret_access_key': auth_data['secret_key'],
                        'region_name': None  # 필요 시 리전 추가
                    }
                    
                    # 세션 생성
                    if self.create_session():
                        if auth_data['save']:
                            self.save_credentials()
                        auth_result[0] = True
                else:
                    # 자격 증명 검증 실패
                    if parent:
                        messagebox.showerror("인증 오류", "AWS 자격 증명 검증에 실패했습니다.\n로그를 확인하세요.")
            except Exception as e:
                logger.error(f"인증 처리 중 오류 발생: {str(e)}")
                if parent:
                    messagebox.showerror("오류", f"인증 처리 중 오류가 발생했습니다: {str(e)}")
                    
        return auth_result[0]
    
    def get_session(self, region_name=None):
        """AWS 세션 반환
        
        Args:
            region_name (str, optional): 특정 리전에 대한 세션이 필요한 경우 지정
            
        Returns:
            boto3.Session: AWS 세션
        """
        if not self.session:
            if not self.show_auth_dialog():
                return None
        
        if region_name and region_name != self.credentials.get('region_name'):
            try:
                # 특정 리전에 대한 새 세션 생성
                return boto3.Session(
                    aws_access_key_id=self.credentials['aws_access_key_id'],
                    aws_secret_access_key=self.credentials['aws_secret_access_key'],
                    region_name=region_name
                )
            except Exception as e:
                logger.error(f"특정 리전({region_name})에 대한 세션 생성 중 오류 발생: {e}")
                return None
        
        return self.session

# 전역 인스턴스
aws_auth = AWSAuth()