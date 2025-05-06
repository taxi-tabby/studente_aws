"""
UDP 서버 및 AWS 서비스 명령어 처리 모듈
"""
import socket
import threading
import json
from core import aws_services
from core.messages import message_format

# UDP 서버 설정
UDP_IP = "127.0.0.1"
UDP_PORT = 20200

# 웹 대시보드 설정
DASHBOARD_IP = "127.0.0.1"
DASHBOARD_PORT = 20201

# 대시보드 메시지 전송을 위한 소켓
dashboard_socket = None

def send_to_dashboard(message):
    """웹 대시보드로 이벤트 메시지를 전송합니다."""
    global dashboard_socket
    
    try:
        if dashboard_socket is None:
            dashboard_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            
        # 메시지가 문자열이 아닌 경우 JSON으로 변환
        if isinstance(message, dict):
            message = json.dumps(message, ensure_ascii=False)
            
        # 대시보드로 메시지 전송
        dashboard_socket.sendto(message.encode('utf-8'), (DASHBOARD_IP, DASHBOARD_PORT))
        print(f"대시보드로 메시지 전송됨: {message}")
        return True
    except Exception as e:
        print(f"대시보드 메시지 전송 중 오류 발생: {e}")
        return False

def start_udp_server():
    """UDP 서버를 실행하여 클라이언트 요청을 처리합니다."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    print(f"UDP 서버가 {UDP_IP}:{UDP_PORT}에서 시작되었습니다.")

    while True:
        data, addr = sock.recvfrom(4096)  # 버퍼 크기 증가
        try:
            # JSON 메시지 파싱 시도
            try:
                message = json.loads(data.decode('utf-8'))
                # 표준 메시지 형식인 경우
                if isinstance(message, dict) and "type" in message:
                    process_structured_message(message, sock, addr)
                    continue
            except json.JSONDecodeError:
                # JSON이 아닌 경우, 기존 문자열 명령어로 처리
                pass
                
            # 이전 형식의 문자열 명령어 처리 (하위 호환성 유지)
            command = data.decode().strip()
            process_legacy_command(command, sock, addr)
            
        except Exception as e:
            print(f"메시지 처리 중 오류 발생: {e}")
            error_response = message_format.create_message(
                "ERROR", 
                {"error": str(e), "message": "메시지 처리 중 오류가 발생했습니다."}
            )
            sock.sendto(json.dumps(error_response, ensure_ascii=False).encode(), addr)

def process_structured_message(message, sock, addr):
    """구조화된 JSON 메시지를 처리합니다."""
    response = None
    message_type = message.get("type")
    content = message.get("content", {})
    
    # AWS 서비스 명령어 처리
    if message_type == message_format.MessageType.AWS_EC2_LIST:
        instances = aws_services.list_ec2_instances()
        response = message_format.create_message(
            message_format.MessageType.AWS_EC2_LIST, 
            {"instances": instances}
        )
    
    elif message_type == message_format.MessageType.AWS_ECS_LIST:
        clusters = aws_services.list_ecs_clusters()
        response = message_format.create_message(
            message_format.MessageType.AWS_ECS_LIST, 
            {"clusters": clusters}
        )
    
    elif message_type == message_format.MessageType.AWS_EKS_LIST:
        clusters = aws_services.list_eks_clusters()
        response = message_format.create_message(
            message_format.MessageType.AWS_EKS_LIST, 
            {"clusters": clusters}
        )
    
    elif message_type == message_format.MessageType.AWS_SERVICE_STATUS:
        action = content.get("action")
        service_type = content.get("service_type")
        
        if service_type == "EC2":
            instance_id = content.get("instance_id")
            region = content.get("region")
            
            if action == "START":
                result = aws_services.start_ec2_instance(instance_id, region)
                response = message_format.create_message(
                    message_format.MessageType.AWS_SERVICE_STATUS, 
                    {"result": result, "service_type": "EC2", "action": "START"}
                )
            
            elif action == "STOP":
                result = aws_services.stop_ec2_instance(instance_id, region)
                response = message_format.create_message(
                    message_format.MessageType.AWS_SERVICE_STATUS, 
                    {"result": result, "service_type": "EC2", "action": "STOP"}
                )
        
        elif service_type == "ECS":
            cluster_name = content.get("cluster_name")
            service_name = content.get("service_name")
            region = content.get("region")
            
            if action == "START":
                result = aws_services.start_ecs_service(cluster_name, service_name, region)
                response = message_format.create_message(
                    message_format.MessageType.AWS_SERVICE_STATUS, 
                    {"result": result, "service_type": "ECS", "action": "START"}
                )
            
            elif action == "STOP":
                result = aws_services.stop_ecs_service(cluster_name, service_name, region)
                response = message_format.create_message(
                    message_format.MessageType.AWS_SERVICE_STATUS, 
                    {"result": result, "service_type": "ECS", "action": "STOP"}
                )
        
        elif service_type == "EKS":
            cluster_name = content.get("cluster_name")
            nodegroup_name = content.get("nodegroup_name")
            region = content.get("region")
            desired_size = content.get("desired_size", 0)
            
            result = aws_services.scale_eks_nodegroup(cluster_name, nodegroup_name, region, desired_size)
            response = message_format.create_message(
                message_format.MessageType.AWS_SERVICE_STATUS, 
                {"result": result, "service_type": "EKS", "action": "SCALE"}
            )
    
    # 사용자 활동 메시지는 처리 없이 로그만 남김
    elif message_type == message_format.MessageType.USER_ACTIVITY:
        activity_type = content.get("activity")
        print(f"사용자 활동 감지: {activity_type}")
        send_to_dashboard({"type": "USER_ACTIVITY", "activity": activity_type})
        # 응답이 필요하지 않음
        return
    
    # 알 수 없는 메시지 유형
    else:
        response = message_format.create_message(
            "ERROR", 
            {"error": f"알 수 없는 메시지 유형: {message_type}"}
        )
    
    # 응답 전송
    if response:
        sock.sendto(json.dumps(response, ensure_ascii=False).encode(), addr)
        send_to_dashboard(response)

def process_legacy_command(command, sock, addr):
    """이전 형식의 문자열 명령어를 처리합니다 (하위 호환성)."""
    if command == "LIST_ALL_SERVICES":
        services = aws_services.list_all_services()
        response = json.dumps(services, ensure_ascii=False)
        sock.sendto(response.encode(), addr)
        send_to_dashboard({"type": "LIST_ALL_SERVICES", "services": services})
    
    elif command == "LIST_EC2":
        instances = aws_services.list_ec2_instances()
        response = json.dumps(instances, ensure_ascii=False)
        sock.sendto(response.encode(), addr)
        send_to_dashboard({"type": "LIST_EC2", "instances": instances})
    
    elif command == "LIST_ECS":
        clusters = aws_services.list_ecs_clusters()
        response = json.dumps(clusters, ensure_ascii=False)
        sock.sendto(response.encode(), addr)
        send_to_dashboard({"type": "LIST_ECS", "clusters": clusters})
    
    elif command == "LIST_EKS":
        clusters = aws_services.list_eks_clusters()
        response = json.dumps(clusters, ensure_ascii=False)
        sock.sendto(response.encode(), addr)
        send_to_dashboard({"type": "LIST_EKS", "clusters": clusters})
    
    elif command.startswith("START_EC2:"):
        parts = command.split(":", 2)
        if len(parts) == 3:
            instance_id = parts[1]
            region = parts[2]
            result = aws_services.start_ec2_instance(instance_id, region)
            sock.sendto(result.encode(), addr)
            send_to_dashboard({"type": "START_EC2", "instance_id": instance_id, "region": region, "result": result})
    
    elif command.startswith("STOP_EC2:"):
        parts = command.split(":", 2)
        if len(parts) == 3:
            instance_id = parts[1]
            region = parts[2]
            result = aws_services.stop_ec2_instance(instance_id, region)
            sock.sendto(result.encode(), addr)
            send_to_dashboard({"type": "STOP_EC2", "instance_id": instance_id, "region": region, "result": result})
    
    elif command.startswith("START_ECS:"):
        parts = command.split(":", 3)
        if len(parts) == 4:
            cluster_name = parts[1]
            service_name = parts[2]
            region = parts[3]
            result = aws_services.start_ecs_service(cluster_name, service_name, region)
            sock.sendto(result.encode(), addr)
            send_to_dashboard({"type": "START_ECS", "cluster_name": cluster_name, "service_name": service_name, "region": region, "result": result})
    
    elif command.startswith("STOP_ECS:"):
        parts = command.split(":", 3)
        if len(parts) == 4:
            cluster_name = parts[1]
            service_name = parts[2]
            region = parts[3]
            result = aws_services.stop_ecs_service(cluster_name, service_name, region)
            sock.sendto(result.encode(), addr)
            send_to_dashboard({"type": "STOP_ECS", "cluster_name": cluster_name, "service_name": service_name, "region": region, "result": result})
    
    elif command.startswith("SCALE_EKS:"):
        parts = command.split(":", 4)
        if len(parts) == 5:
            cluster_name = parts[1]
            nodegroup_name = parts[2]
            region = parts[3]
            desired_size = int(parts[4])
            result = aws_services.scale_eks_nodegroup(cluster_name, nodegroup_name, region, desired_size)
            sock.sendto(result.encode(), addr)
            send_to_dashboard({"type": "SCALE_EKS", "cluster_name": cluster_name, "nodegroup_name": nodegroup_name, "region": region, "desired_size": desired_size, "result": result})
    
    else:
        # 활동 모니터링에서 보낸 메시지는 로그만 남김
        if (command.startswith("Keyboard") or 
            command.startswith("Mouse") or
            command.startswith("Screen") or
            command.startswith("Active window") or
            command.startswith("Audio playback")):
            print(f"사용자 활동 감지: {command}")
            send_to_dashboard({"type": "USER_ACTIVITY", "activity": command})
        else:
            sock.sendto("명령어가 올바르지 않습니다.".encode(), addr)

def run_server():
    """UDP 서버를 별도의 스레드에서 실행합니다."""
    server_thread = threading.Thread(target=start_udp_server, daemon=True)
    server_thread.start()
    return server_thread