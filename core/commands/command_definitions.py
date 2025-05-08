"""
명령어 정의 모듈
클라이언트와 서버 간 통신에 사용되는 모든 명령어와 핸들러를 정의합니다.
"""
import logging
import asyncio
from typing import Dict, Any, Optional, Callable, Awaitable
from functools import wraps
from core.commands.command_registry import register_action_handler, register_type_handler, register_handler
from core.messages import message_format
from core import aws_services

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
        "action": "test",
        "service": "test",
        "status": "success",
        "message": "테스트 메시지입니다.",
        "share": True  # 공유 플래그 추가
    }

# ===== 활동 모니터링 명령어 핸들러 =====
@register_action_handler("startMonitoring")
@shared_response_handler
async def handle_start_monitoring(data: dict, client=None) -> dict:
    """활동 모니터링 시작 요청 처리"""
    logger.info("활동 모니터링 시작 요청 수신")
    
    try:
        # 활동 모니터링 모듈 로드
        from core import activity_monitor
        
        # 활동 모니터링 시작
        if not hasattr(activity_monitor, 'is_monitoring_active') or not activity_monitor.is_monitoring_active():
            # 이미 실행 중인 프로세스가 있으면 강제 종료 후 시작
            if activity_monitor.is_already_running():
                activity_monitor.find_and_kill_lock_process()
                await asyncio.sleep(3)  # 완전히 종료될 시간 제공
                
            result = activity_monitor.start_monitoring()
            success = result
        else:
            logger.info("활동 모니터링이 이미 실행 중입니다.")
            success = True
        
        # 결과 메시지 생성 및 전송
        activity_response = {
            "service": "activity",
            "status": "started" if success else "error",
            "message": "활동 모니터링이 시작되었습니다." if success else "활동 모니터링 시작에 실패했습니다."
        }
        
        await broadcast_to_clients(activity_response, exclude_client=client)
        return {"status": "success", "message": "모니터링이 시작되었습니다.", "share": True} if success else {"status": "error", "message": "모니터링 시작에 실패했습니다."}
        
    except Exception as e:
        logger.error(f"활동 모니터링 시작 중 오류: {e}", exc_info=True)
        return {"status": "error", "message": f"활동 모니터링 시작 중 오류가 발생했습니다: {str(e)}"}

# ===== AWS EC2 명령어 핸들러 =====
@register_handler("startInstance", "action")
@register_handler("AWS_EC2_START_INSTANCE", "type")
@shared_response_handler
async def handle_start_instance(data: dict, client=None) -> dict:
    """EC2 인스턴스 시작 요청 처리"""
    # 메시지 형식에 따라 인스턴스 ID 추출
    if "instanceId" in data:
        instance_id = data.get("instanceId")
    elif "content" in data and "instanceId" in data["content"]:
        instance_id = data["content"]["instanceId"]
    else:
        return {"status": "error", "message": "인스턴스 ID가 필요합니다."}
    
    region = data.get("region", None)
    logger.info(f"EC2 인스턴스 시작 요청: {instance_id}, 리전: {region}")
    
    # EC2 인스턴스 시작
    success = aws_services.start_ec2_instance(instance_id, region)
    
    if success:
        # 성공 시 최신 EC2 인스턴스 정보 조회
        instances = aws_services.list_ec2_instances(region)
        return {
            "service": "ec2",
            "instances": instances,
            "status": "updated",
            "message": f"인스턴스 {instance_id}가 시작되었습니다.",
            "share": True  # 공유 플래그 추가
        }
    else:
        return {"status": "error", "message": f"인스턴스 {instance_id} 시작 실패"}

@register_handler("stopInstance", "action")
@register_handler("AWS_EC2_STOP_INSTANCE", "type")
@shared_response_handler
async def handle_stop_instance(data: dict, client=None) -> dict:
    """EC2 인스턴스 중지 요청 처리"""
    # 메시지 형식에 따라 인스턴스 ID 추출
    if "instanceId" in data:
        instance_id = data.get("instanceId")
    elif "content" in data and "instanceId" in data["content"]:
        instance_id = data["content"]["instanceId"]
    else:
        return {"status": "error", "message": "인스턴스 ID가 필요합니다."}
    
    region = data.get("region", None)
    logger.info(f"EC2 인스턴스 중지 요청: {instance_id}, 리전: {region}")
    
    # EC2 인스턴스 중지
    success = aws_services.stop_ec2_instance(instance_id, region)
    
    if success:
        # 성공 시 최신 EC2 인스턴스 정보 조회
        instances = aws_services.list_ec2_instances(region)
        return {
            "service": "ec2",
            "instances": instances,
            "status": "updated",
            "message": f"인스턴스 {instance_id}가 중지되었습니다.",
            "share": True  # 공유 플래그 추가
        }
    else:
        return {"status": "error", "message": f"인스턴스 {instance_id} 중지 실패"}

# ===== 데이터 조회 명령어 핸들러 =====
@register_action_handler("getAll")
@shared_response_handler
async def handle_get_all(data: dict, client=None) -> dict:
    """모든 AWS 서비스 데이터 요청 처리"""
    region = None
    logger.info(f"모든 AWS 서비스 데이터 요청 - 리전: {region}")
    
    try:
        # EC2 인스턴스 목록
        instances = aws_services.list_ec2_instances(region)
        ec2_response = {
            "service": "ec2",
            "instances": instances
        }
        await broadcast_to_clients(ec2_response, exclude_client=client)
        
        # ECS 클러스터 목록
        clusters = aws_services.list_ecs_clusters(region)
        ecs_response = {
            "service": "ecs",
            "clusters": clusters
        }
        await broadcast_to_clients(ecs_response, exclude_client=client)
        
        # EKS 클러스터 목록
        eks_clusters = aws_services.list_eks_clusters(region)
        eks_response = {
            "service": "eks",
            "clusters": eks_clusters
        }
        await broadcast_to_clients(eks_response, exclude_client=client)
        
        # 활동 로그
        activity_response = {
            "service": "activity",
            "message": "모든 AWS 서비스 데이터가 로드되었습니다."
        }
        await broadcast_to_clients(activity_response, exclude_client=client)
        
        return {"status": "success", "message": "모든 데이터를 요청했습니다.", "share": True}
        
    except Exception as e:
        logger.error(f"AWS 데이터 조회 중 오류: {e}", exc_info=True)
        return {"status": "error", "message": f"AWS 데이터 조회 중 오류가 발생했습니다: {str(e)}"}

@register_action_handler("refresh")
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
            instances = aws_services.list_ec2_instances(region)
            response = {
                "service": "ec2",
                "instances": instances
            }
        elif service == "ecs":
            clusters = aws_services.list_ecs_clusters(region)
            response = {
                "service": "ecs",
                "clusters": clusters
            }
        elif service == "eks":
            clusters = aws_services.list_eks_clusters(region)
            response = {
                "service": "eks",
                "clusters": clusters
            }
        elif service == "activity":
            response = {
                "service": "activity",
                "status": "refresh",
                "message": "활동 모니터링 데이터가 갱신되었습니다."
            }
        else:
            return {"status": "error", "message": f"알 수 없는 서비스: {service}"}
        
        if response:
            await broadcast_to_clients(response, exclude_client=client)
            return {"status": "success", "message": f"{service.upper()} 데이터가 갱신되었습니다.", "share": True}
        
    except Exception as e:
        logger.error(f"{service.upper()} 데이터 조회 중 오류: {e}", exc_info=True)
        return {"status": "error", "message": f"{service.upper()} 데이터 조회 중 오류가 발생했습니다: {str(e)}"}

# ===== 활동 모니터링 메시지 핸들러 =====
for activity_type in [
    message_format.MessageType.KEYBOARD_ACTIVITY,
    message_format.MessageType.MOUSE_MOVEMENT,
    message_format.MessageType.MOUSE_CLICK,
    message_format.MessageType.SCREEN_CHANGE,
    message_format.MessageType.ACTIVE_WINDOW,
    message_format.MessageType.AUDIO_PLAYBACK,
    message_format.MessageType.USER_ACTIVITY
]:
    # 각 활동 유형에 대한 핸들러 등록 (action 기반으로 통합)
    @register_action_handler(activity_type)
    @shared_response_handler
    async def handle_activity_message(data: dict, client=None) -> dict:
        """활동 모니터링 관련 메시지 처리"""
        await broadcast_to_clients(data, exclude_client=client)
        return {"status": "success", "message": "활동 메시지가 전송되었습니다.", "share": True}

# AWS EC2 목록 요청 처리 (action 기반으로 통합)
@register_action_handler(message_format.MessageType.AWS_EC2_LIST)
@shared_response_handler
async def handle_aws_ec2_list(data: dict, client=None) -> dict:
    """EC2 인스턴스 목록 요청 처리"""
    region = None
    
    instances = aws_services.list_ec2_instances(region)
    response = message_format.create_message(
        message_format.MessageType.AWS_EC2_LIST, 
        {"instances": instances}
    )
    # 응답에 action 키를 추가하여 일관성 유지
    if "type" in response and "action" not in response:
        response["action"] = response["type"]
        
    await broadcast_to_clients(response, exclude_client=client)
    return {"status": "success", "share": True}