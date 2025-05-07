"""
명령어 정의 모듈
클라이언트와 서버 간 통신에 사용되는 모든 명령어와 핸들러를 정의합니다.
"""
import logging
import asyncio
from typing import Dict, Any, Optional
from core.commands.command_registry import register_action_handler, register_type_handler
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

async def broadcast_to_clients(message):
    """
    연결된 모든 클라이언트에게 메시지를 전송합니다.
    
    Args:
        message: 전송할 메시지
        
    Returns:
        bool: 전송 성공 여부
    """
    success = False
    
    # WebSocket 브로드캐스트
    if _ws_broadcast_func:
        try:
            await _ws_broadcast_func(message)
            success = True
        except Exception as e:
            logger.error(f"WebSocket 브로드캐스트 중 오류: {e}")
    
    # TCP 메시지 전송
    if _tcp_send_func:
        try:
            _tcp_send_func(message)
            success = True
        except Exception as e:
            logger.error(f"TCP 메시지 전송 중 오류: {e}")
            
    return success

# ===== 테스트 명령어 핸들러 =====
@register_action_handler("test")
async def handle_test(data: dict, client=None) -> dict:
    """테스트 요청 처리"""
    logger.info("테스트 요청 수신")
    
    test_message = {
        "type": "test",
        "service": "test",
        "status": "success",
        "message": "테스트 메시지입니다."
    }
    
    await broadcast_to_clients(test_message)
    return {"status": "success", "message": "테스트 메시지가 전송되었습니다."}

@register_type_handler("test")
async def handle_test_type(data: dict, client=None) -> dict:
    """테스트 메시지 타입 처리"""
    return await handle_test(data, client)

# ===== 활동 모니터링 명령어 핸들러 =====
@register_action_handler("startMonitoring")
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
        
        await broadcast_to_clients(activity_response)
        return {"status": "success", "message": "모니터링이 시작되었습니다."} if success else {"status": "error", "message": "모니터링 시작에 실패했습니다."}
        
    except Exception as e:
        logger.error(f"활동 모니터링 시작 중 오류: {e}", exc_info=True)
        return {"status": "error", "message": f"활동 모니터링 시작 중 오류가 발생했습니다: {str(e)}"}

# ===== AWS EC2 명령어 핸들러 =====
@register_action_handler("startInstance")
async def handle_start_instance(data: dict, client=None) -> dict:
    """EC2 인스턴스 시작 요청 처리"""
    if "instanceId" not in data:
        return {"status": "error", "message": "인스턴스 ID가 필요합니다."}
    
    instance_id = data.get("instanceId")
    region = None
    logger.info(f"EC2 인스턴스 시작 요청: {instance_id}, 리전: {region}")
    
    # EC2 인스턴스 시작
    success = aws_services.start_ec2_instance(instance_id, region)
    
    if success:
        # 성공 시 최신 EC2 인스턴스 정보 조회 및 전송
        instances = aws_services.list_ec2_instances(region)
        ec2_response = {
            "service": "ec2",
            "instances": instances,
            "status": "updated",
            "message": f"인스턴스 {instance_id}가 시작되었습니다."
        }
        await broadcast_to_clients(ec2_response)
        return {"status": "success", "message": f"인스턴스 {instance_id}가 시작되었습니다."}
    else:
        return {"status": "error", "message": f"인스턴스 {instance_id} 시작 실패"}

@register_action_handler("stopInstance")
async def handle_stop_instance(data: dict, client=None) -> dict:
    """EC2 인스턴스 중지 요청 처리"""
    if "instanceId" not in data:
        return {"status": "error", "message": "인스턴스 ID가 필요합니다."}
    
    instance_id = data.get("instanceId")
    region = None
    logger.info(f"EC2 인스턴스 중지 요청: {instance_id}, 리전: {region}")
    
    # EC2 인스턴스 중지
    success = aws_services.stop_ec2_instance(instance_id, region)
    
    if success:
        # 성공 시 최신 EC2 인스턴스 정보 조회 및 전송
        instances = aws_services.list_ec2_instances(region)
        ec2_response = {
            "service": "ec2",
            "instances": instances,
            "status": "updated",
            "message": f"인스턴스 {instance_id}가 중지되었습니다."
        }
        await broadcast_to_clients(ec2_response)
        return {"status": "success", "message": f"인스턴스 {instance_id}가 중지되었습니다."}
    else:
        return {"status": "error", "message": f"인스턴스 {instance_id} 중지 실패"}

@register_type_handler("AWS_EC2_START_INSTANCE")
async def handle_ec2_start_instance_type(data: dict, client=None) -> dict:
    """EC2 인스턴스 시작 메시지 타입 처리"""
    if "content" in data and "instanceId" in data["content"]:
        # 메시지 타입 형식을 액션 형식으로 변환
        action_data = {
            "action": "startInstance",
            "instanceId": data["content"]["instanceId"],
            "region": data.get("region", aws_services.DEFAULT_REGION)
        }
        return await handle_start_instance(action_data, client)
    else:
        return {"status": "error", "message": "인스턴스 ID가 필요합니다."}

@register_type_handler("AWS_EC2_STOP_INSTANCE")
async def handle_ec2_stop_instance_type(data: dict, client=None) -> dict:
    """EC2 인스턴스 중지 메시지 타입 처리"""
    if "content" in data and "instanceId" in data["content"]:
        # 메시지 타입 형식을 액션 형식으로 변환
        action_data = {
            "action": "stopInstance",
            "instanceId": data["content"]["instanceId"],
            "region": data.get("region", aws_services.DEFAULT_REGION)
        }
        return await handle_stop_instance(action_data, client)
    else:
        return {"status": "error", "message": "인스턴스 ID가 필요합니다."}

# ===== 데이터 조회 명령어 핸들러 =====
@register_action_handler("getAll")
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
        await broadcast_to_clients(ec2_response)
        
        # ECS 클러스터 목록
        clusters = aws_services.list_ecs_clusters(region)
        ecs_response = {
            "service": "ecs",
            "clusters": clusters
        }
        await broadcast_to_clients(ecs_response)
        
        # EKS 클러스터 목록
        eks_clusters = aws_services.list_eks_clusters(region)
        eks_response = {
            "service": "eks",
            "clusters": eks_clusters
        }
        await broadcast_to_clients(eks_response)
        
        # 활동 로그
        activity_response = {
            "service": "activity",
            "message": "모든 AWS 서비스 데이터가 로드되었습니다."
        }
        await broadcast_to_clients(activity_response)
        
        return {"status": "success", "message": "모든 데이터를 요청했습니다."}
        
    except Exception as e:
        logger.error(f"AWS 데이터 조회 중 오류: {e}", exc_info=True)
        return {"status": "error", "message": f"AWS 데이터 조회 중 오류가 발생했습니다: {str(e)}"}

@register_action_handler("refresh")
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
            await broadcast_to_clients(response)
            return {"status": "success", "message": f"{service.upper()} 데이터가 갱신되었습니다."}
        
    except Exception as e:
        logger.error(f"{service.upper()} 데이터 조회 중 오류: {e}", exc_info=True)
        return {"status": "error", "message": f"{service.upper()} 데이터 조회 중 오류가 발생했습니다: {str(e)}"}

# ===== 활동 모니터링 메시지 타입 핸들러 =====
for activity_type in [
    message_format.MessageType.KEYBOARD_ACTIVITY,
    message_format.MessageType.MOUSE_MOVEMENT,
    message_format.MessageType.MOUSE_CLICK,
    message_format.MessageType.SCREEN_CHANGE,
    message_format.MessageType.ACTIVE_WINDOW,
    message_format.MessageType.AUDIO_PLAYBACK,
    message_format.MessageType.USER_ACTIVITY
]:
    # 각 활동 유형에 대한 핸들러 등록
    @register_type_handler(activity_type)
    async def handle_activity_message(data: dict, client=None) -> dict:
        """활동 모니터링 관련 메시지 처리"""
        await broadcast_to_clients(data)
        return {"status": "success", "message": "활동 메시지가 전송되었습니다."}

# AWS EC2 목록 요청 처리
@register_type_handler(message_format.MessageType.AWS_EC2_LIST)
async def handle_aws_ec2_list(data: dict, client=None) -> dict:
    """EC2 인스턴스 목록 요청 처리"""
    region = None
    
    instances = aws_services.list_ec2_instances(region)
    response = message_format.create_message(
        message_format.MessageType.AWS_EC2_LIST, 
        {"instances": instances}
    )
    await broadcast_to_clients(response)
    return response