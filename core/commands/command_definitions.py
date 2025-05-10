"""
명령어 정의 모듈
클라이언트와 서버 간 통신에 사용되는 모든 명령어와 핸들러를 정의합니다.
"""
import logging
import asyncio
import os
import json
from typing import Dict, Any, Optional, Callable, Awaitable
from functools import wraps
from core.commands.command_registry import register_action_handler, register_type_handler, register_handler
from core.messages import message_format
from core import aws_services
import bcrypt
import secrets
import string
import hashlib
import hmac
import base64
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization

# 로거 설정
logger = logging.getLogger(__name__)

# 클라이언트 브로드캐스트 함수 참조를 위한 변수
# 순환 참조를 방지하기 위해 런타임에 설정됨
_ws_broadcast_func = None
_tcp_send_func = None

def set_broadcast_functions(ws_broadcast_func, tcp_send_func):
    """
    클라이언트 브로드캐스트 함수 참조를 설정합니다.
    
    Args:
        ws_broadcast_func: WebSocket 브로드캐스트 함수
        tcp_send_func: TCP 클라이언트 메시지 전송 함수
    """
    global _ws_broadcast_func, _tcp_send_func
    _ws_broadcast_func = ws_broadcast_func
    _tcp_send_func = tcp_send_func
    logger.info("브로드캐스트 함수가 설정되었습니다.")

async def broadcast_to_clients(message, exclude_client=None):
    """
    연결된 모든 클라이언트에게 메시지를 전송합니다.
    
    Args:
        message: 전송할 메시지
        exclude_client: 제외할 클라이언트 (요청을 보낸 클라이언트)
        
    Returns:
        bool: 전송 성공 여부
    """
    success = False
    
    # WebSocket 브로드캐스트
    if _ws_broadcast_func:
        try:
            await _ws_broadcast_func(message, exclude_client)
            success = True
        except Exception as e:
            logger.error(f"WebSocket 브로드캐스트 중 오류: {e}")
    
    # TCP 메시지 전송
    if _tcp_send_func:
        try:
            _tcp_send_func(message, exclude_client)
            success = True
        except Exception as e:
            logger.error(f"TCP 메시지 전송 중 오류: {e}")
            
    return success

def shared_response_handler(handler_func):
    """
    핸들러 응답에 'share' 플래그가 있는지 확인하고, 있을 경우 모든 클라이언트에게 메시지를 전송하는 데코레이터입니다.
    
    Args:
        handler_func: 처리할 핸들러 함수
        
    Returns:
        wrapper: 핸들러 함수의 래퍼
    """
    @wraps(handler_func)
    async def wrapper(data: dict, client=None) -> dict:
        # 원래 핸들러 함수 호출
        response = await handler_func(data, client)
        
        # 공유 플래그가 있는지 확인
        if isinstance(response, dict) and response.get("share") is True:
            # 브로드캐스트할 메시지 생성 (요청한 클라이언트 제외)
            broadcast_response = response.copy()
            broadcast_response.pop("share", None)
            # 다른 클라이언트를 위한 메시지는 self: false로 설정
            broadcast_response["self"] = False
            
            # 모든 클라이언트에게 메시지 전송 (요청한 클라이언트 제외)
            logger.info(f"공유 플래그가 있는 응답을 다른 클라이언트에게 전송: {broadcast_response}")
            await broadcast_to_clients(broadcast_response, exclude_client=client)
        
        # 요청한 클라이언트에게는 self: true 설정
        if isinstance(response, dict):
            response["self"] = True
        
        return response
    
    return wrapper

# ===== 테스트 명령어 핸들러 =====
@register_action_handler("test")
@shared_response_handler
async def handle_test(data: dict, client=None) -> dict:
    """테스트 요청 처리"""
    logger.info("테스트 요청 수신")
    
    # share 플래그를 추가하여 모든 클라이언트에게 공유
    return {
        "service": "test",
        "status": "success",
        "message": "테스트 메시지입니다.",
        "content": {
            "data": "dummy text"
        },
        "dummy_key": "dummy key",
        "share": True  # 공유 플래그 추가
    }

@register_action_handler("create_password")
@shared_response_handler
async def handle_password_create(data: dict, client=None) -> dict:
    """비밀번호 생성 요청 처리"""
    logger.info("비밀번호 생성 요청 수신")
    
    try:
        # 클라이언트로부터 받은 초기 비밀번호
        content = data.get("content", {})
        client_password = content.get("password")
        
        if not client_password:
            return {
                "status": "error", 
                "message": "비밀번호가 제공되지 않았습니다."
            }
            
        
        # 1. AWS 인증 정보 파일 경로
        from core import aws_auth
        credentials_file = aws_auth.aws_auth.credentials_file
        
        # 2. 기존 credentials 파일 로드 또는 새로 생성
        credentials = {}
        try:
            if os.path.exists(credentials_file):
                with open(credentials_file, "r", encoding="utf-8") as f:
                    credentials = json.load(f)
            # 이미 비밀번호가 설정되어 있는지 확인
            if credentials.get('password_hash'):
                return {
                "status": "error", 
                "message": "비밀번호가 이미 설정되어 있습니다. 재설정이 불가능합니다."
                }
            logger.info("저장된 AWS 자격 증명을 로드했습니다.")
        except Exception as e:
            logger.warning(f"자격 증명 로드 중 오류 발생: {e}, 새 파일을 생성합니다.")
        
        # 3. 비밀번호 bcrypt 해싱
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(client_password.encode('utf-8'), salt).decode('utf-8')
        
        # 4. 해시된 비밀번호를 credentials에 저장
        credentials['password_hash'] = hashed_password
        
        # 5. 파일에 저장
        try:
            with open(credentials_file, "w", encoding="utf-8") as f:
                json.dump(credentials, f)
                
            logger.info("비밀번호가 AWS 자격 증명 파일에 안전하게 저장되었습니다.")
        except Exception as e:
            logger.error(f"비밀번호 저장 중 오류 발생: {e}")
            return {
            "status": "error", 
            "message": f"비밀번호 저장 중 오류가 발생했습니다: {str(e)}"
            }
        
        # 6. 인증 토큰 생성 (세션용)
        auth_token = secrets.token_hex(32)
        
        # 7. 클라이언트에 성공 응답
        return {
            "status": "success",
            "message": "비밀번호가 설정되었습니다.",
            "content": {
                "success": True,
                "authKey": auth_token
            },
            "share": False  # 보안 정보이므로 공유하지 않음
        }
            
    except Exception as e:
        logger.error(f"비밀번호 생성 중 오류: {str(e)}", exc_info=True)
        return {"status": "error", "message": f"비밀번호 생성 중 오류가 발생했습니다: {str(e)}"}

@register_action_handler("verify_password")
@shared_response_handler
async def handle_verify_password(data: dict, client=None) -> dict:
    """비밀번호 검증 요청 처리"""
    logger.info("비밀번호 검증 요청 수신")
    
    try:
        # 클라이언트로부터 받은 비밀번호
        content = data.get("content", {})
        client_password = content.get("password")
        

        if not client_password:
            return {
                "status": "error", 
                "message": "비밀번호가 제공되지 않았습니다."
            }
            
            

        
        # AWS 인증 정보 파일 경로
        from core import aws_auth
        credentials_file = aws_auth.aws_auth.credentials_file
        
        # 저장된 비밀번호 해시 로드
        if not os.path.exists(credentials_file):
            return {
                "status": "error",
                "message": "자격 증명 파일을 찾을 수 없습니다. 비밀번호 설정이 필요합니다.",
                "content": {"require_setup": True}
            }
            
            
        try:
            with open(credentials_file, "r", encoding="utf-8") as f:
                credentials = json.load(f)
                
            # 저장된 비밀번호 해시 가져오기
            stored_hash = credentials.get('password_hash')
            if not stored_hash:
                return {
                    "status": "error",
                    "message": "저장된 비밀번호가 없습니다. 비밀번호 설정이 필요합니다.",
                    "content": {"require_setup": True}
                }
                
            # 비밀번호 검증
            if bcrypt.checkpw(client_password.encode('utf-8'), stored_hash.encode('utf-8')):
                # 인증 성공
                auth_token = secrets.token_hex(32)
                
                return {
                    "status": "success",
                    "message": "비밀번호가 확인되었습니다.",
                    "content": {
                        "success": True,
                        "authKey": auth_token
                    },
                    "share": False  # 보안 정보이므로 공유하지 않음
                }
            else:
                # 인증 실패
                return {
                    "status": "error",
                    "message": "잘못된 비밀번호입니다.",
                    "content": {"success": False}
                }
                
        except Exception as e:
            logger.error(f"비밀번호 검증 중 파일 처리 오류: {e}", exc_info=True)
            return {
                "status": "error", 
                "message": f"자격 증명 파일 처리 중 오류가 발생했습니다: {str(e)}"
            }
            
    except Exception as e:
        logger.error(f"비밀번호 검증 중 오류: {str(e)}", exc_info=True)
        return {"status": "error", "message": f"비밀번호 검증 중 오류가 발생했습니다: {str(e)}"}
    
    
    
    

@register_action_handler("refresh_service")
@shared_response_handler
async def handle_refresh(data: dict, client=None) -> dict:
    """특정 서비스 데이터 새로고침 요청 처리"""
    if "service" not in data:
        return {"status": "error", "message": "서비스 이름이 필요합니다."}
    
    service = data.get("service")
    region = None
    logger.info(f"{service.upper()} 서비스 갱신 요청 - 리전: {region}")
    
    try:
        response = None
        
        if service == "ec2":
            response = {
                "service": "aws",
                "type": "REFRESH_EC2",
                "content": {
                    "type": "ec2",
                    "instances": aws_services.list_ec2_instances(region),
                    "region": region,
                }
            }
        elif service == "ecs":
            response = {
                "service": "aws",
                "type": "REFRESH_ECS",
                "content": {
                    "activity": "REFRESH",
                    "type": "ecs",
                    "clusters": aws_services.list_ecs_clusters(region),
                    "region": region,
                }
            }
        elif service == "eks":
            response = {
                "service": "aws",
                "type": "REFRESH_EKS",
                "content": {
                    "activity": "REFRESH",
                    "type": "eks",
                    "clusters": aws_services.list_eks_clusters(region),
                    "region": region,
                }
            }
        else:
            return {"status": "error", "message": f"알 수 없는 서비스: {service}"}
        
        if response:
            await broadcast_to_clients(response, exclude_client=client)
            return response
        
    except Exception as e:
        logger.error(f"{service.upper()} 데이터 조회 중 오류: {e}", exc_info=True)
        return {"status": "error", "message": f"{service.upper()} 데이터 조회 중 오류가 발생했습니다: {str(e)}"}