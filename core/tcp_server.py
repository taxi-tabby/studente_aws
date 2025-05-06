"""
TCP 및 WebSocket 서버와 AWS 서비스 명령어 처리 모듈
"""
import socket
import threading
import json
import select
import asyncio
import websockets
import logging
import traceback
from core import aws_services
from core.messages import message_format
from core.config.config_loader import config_loader, config

# 로거 설정
logger = logging.getLogger(__name__)
# 로그 레벨 설정 (INFO 또는 DEBUG)
logger.setLevel(logging.DEBUG)

# 서버 설정
SERVER_IP = "127.0.0.1"
WS_PORT = 20201  # WebSocket 서버 포트 (TCP와 다른 포트 사용)
TCP_PORT = 20200  # TCP 서버 포트

# 클라이언트 연결 목록
ws_clients = set()
tcp_clients = []

# AWS 리전 설정
aws_regions = config.settings.get("aws", {}).get("regions", ["ap-northeast-2"])
DEFAULT_REGION = aws_regions[0] if aws_regions else "ap-northeast-2"

# 활동 모니터링 메시지 처리를 위한 글로벌 이벤트 루프
event_loop = None

# WebSocket 메시지 브로드캐스트
async def broadcast_to_ws_clients(message):
    """연결된 모든 WebSocket 클라이언트에게 메시지를 전송합니다."""
    if not ws_clients:  # 클라이언트가 없으면 반환
        logger.debug("연결된 WebSocket 클라이언트가 없습니다.")
        return
        
    # 메시지가 문자열이 아닌 경우 JSON으로 변환
    if isinstance(message, dict):
        message_str = json.dumps(message, ensure_ascii=False)
        message_type = message.get("type", "UNKNOWN")
        message_id = message.get("id", "")[:8] if "id" in message else "NO_ID"
        logger.debug(f"WebSocket 브로드캐스트 시작 - 타입: {message_type}, ID: {message_id}")
    else:
        message_str = str(message)
        logger.debug(f"WebSocket 문자열 메시지 브로드캐스트 시작: {message_str[:50]}...")
        
    disconnected_clients = set()
    success_count = 0
    for client in ws_clients:
        try:
            await client.send(message_str)
            success_count += 1
        except websockets.exceptions.ConnectionClosed:
            disconnected_clients.add(client)
            logger.warning(f"WebSocket 연결이 닫힘: {client.remote_address}")
        except Exception as e:
            logger.error(f"WebSocket 메시지 전송 중 오류 발생: {e}")
            disconnected_clients.add(client)
            
    # 연결이 끊어진 클라이언트 제거
    for client in disconnected_clients:
        ws_clients.remove(client)
        logger.info(f"연결이 끊어진 WebSocket 클라이언트를 제거했습니다: {client.remote_address if hasattr(client, 'remote_address') else 'Unknown'}")
    
    if isinstance(message, dict):
        logger.info(f"WebSocket 브로드캐스트 완료 - 타입: {message_type}, {success_count}/{len(ws_clients)} 클라이언트 성공")
    else:
        logger.info(f"WebSocket 문자열 메시지 브로드캐스트 완료: {success_count}/{len(ws_clients)} 클라이언트 성공")

# 활동 모니터링 메시지 전달 함수
def forward_activity_message(message):
    """활동 모니터링 메시지를 모든 클라이언트에게 전달합니다."""
    global event_loop
    
    try:
        # 메시지가 dict 형태인지 확인
        if isinstance(message, dict):
            message_type = message.get("type", "UNKNOWN")
            content_type = message.get("content", {}).get("activity", "UNKNOWN") if isinstance(message.get("content"), dict) else "UNKNOWN"
            message_id = message.get("id", "")[:8] if "id" in message else "NO_ID"
            
            logger.info(f"활동 모니터링 메시지 전달 시작 - 타입: {message_type}, 활동: {content_type}, ID: {message_id}")
            
            # TCP 클라이언트에게 메시지 전송
            tcp_success = send_to_tcp_clients(message)
            if tcp_success:
                logger.debug("TCP 클라이언트 전송 성공")
            else:
                logger.warning("TCP 클라이언트 전송 실패 또는 클라이언트 없음")
            
            # WebSocket 클라이언트에게 메시지 전송
            ws_success = False
            if event_loop and event_loop.is_running():
                future = asyncio.run_coroutine_threadsafe(broadcast_to_ws_clients(message), event_loop)
                try:
                    future.result(timeout=3.0)  # 3초 타임아웃으로 결과 기다림
                    ws_success = True
                    logger.debug("기존 이벤트 루프를 통해 활동 메시지 전송됨")
                except asyncio.TimeoutError:
                    logger.warning("WebSocket 메시지 전송 타임아웃")
                except Exception as e:
                    logger.error(f"WebSocket 메시지 전송 중 오류: {e}")
            else:
                # 임시 이벤트 루프 생성하여 메시지 전송
                try:
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    new_loop.run_until_complete(broadcast_to_ws_clients(message))
                    new_loop.close()
                    ws_success = True
                    logger.debug("임시 이벤트 루프를 통해 활동 메시지 전송됨")
                except Exception as e:
                    logger.error(f"임시 이벤트 루프 생성 중 오류: {e}")
                
            # 전송 결과 로그
            if tcp_success or ws_success:
                logger.info(f"활동 모니터링 메시지 전달 완료 - 타입: {message_type}, 활동: {content_type}, ID: {message_id}")
                return True
            else:
                logger.warning(f"활동 모니터링 메시지 전달 실패 - 타입: {message_type}, 활동: {content_type}")
                return False
    except Exception as e:
        logger.error(f"활동 모니터링 메시지 전달 중 오류 발생: {e}")
        logger.debug(f"에러 상세 정보: {traceback.format_exc()}")
    
    return False

# WebSocket 핸들러
async def handle_websocket(websocket, path):
    """WebSocket 연결을 처리합니다."""
    logger.info(f"WebSocket 클라이언트 연결됨: {websocket.remote_address}")
    
    # 클라이언트를 집합에 추가
    ws_clients.add(websocket)
    logger.debug(f"현재 WebSocket 클라이언트 수: {len(ws_clients)}")
    
    try:
        async for message in websocket:
            logger.debug(f"WebSocket 메시지 수신: {message[:100]}...")
            
            try:
                # JSON 메시지 파싱 시도
                data = json.loads(message)
                
                # 메시지 처리
                logger.info(f"WebSocket 메시지 처리 중 - 액션: {data.get('action', 'UNKNOWN')}")
                response = await process_ws_message(data)
                if response:
                    await websocket.send(json.dumps(response, ensure_ascii=False))
                    logger.debug("WebSocket 응답 전송 완료")
                    
            except json.JSONDecodeError:
                # JSON이 아닌 경우, 텍스트 메시지로 처리
                logger.warning(f"JSON 파싱 실패: {message[:50]}...")
                await websocket.send(json.dumps({
                    "status": "error", 
                    "message": "유효한 JSON 형식이 아닙니다."
                }, ensure_ascii=False))
                
            except Exception as e:
                logger.error(f"WebSocket 메시지 처리 중 오류 발생: {e}")
                logger.debug(f"에러 상세 정보: {traceback.format_exc()}")
                await websocket.send(json.dumps({
                    "status": "error",
                    "message": f"메시지 처리 중 오류가 발생했습니다: {str(e)}"
                }, ensure_ascii=False))
                
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"WebSocket 클라이언트 연결 종료됨: {websocket.remote_address}")
        
    except Exception as e:
        logger.error(f"WebSocket 핸들러 오류: {e}")
        logger.debug(f"에러 상세 정보: {traceback.format_exc()}")
        
    finally:
        # 클라이언트 집합에서 제거
        if websocket in ws_clients:
            ws_clients.remove(websocket)
            logger.info(f"WebSocket 클라이언트 연결 해제됨: {websocket.remote_address}")
            logger.debug(f"현재 WebSocket 클라이언트 수: {len(ws_clients)}")

async def process_ws_message(data):
    """WebSocket 메시지를 처리하고 응답을 생성합니다."""    
    response = None
    region = data.get("region", DEFAULT_REGION)
    
    if isinstance(data, dict):
        # 'action' 키가 있는 새로운 메시지 형식
        if "action" in data:
            action = data.get("action")
            logger.info(f"WebSocket 액션 처리: {action}")
            
            # 활동 모니터링 시작 명령 처리
            if action == "startMonitoring":
                logger.info("활동 모니터링 시작 요청 수신")
                activity_response = {
                    "service": "activity",
                    "status": "started",
                    "message": "활동 모니터링이 시작되었습니다."
                }
                await broadcast_to_ws_clients(activity_response)
                return {"status": "success", "message": "모니터링이 시작되었습니다."}
            
            # getAll 명령어 처리
            if action == "getAll":
                logger.info(f"모든 AWS 서비스 데이터 요청 - 리전: {region}")
                # EC2 인스턴스 목록
                try:
                    instances = aws_services.list_ec2_instances(region)
                    ec2_response = {
                        "service": "ec2",
                        "instances": instances
                    }
                    await broadcast_to_ws_clients(ec2_response)
                    logger.info(f"EC2 인스턴스 {len(instances)}개 전송됨")
                except Exception as e:
                    logger.error(f"EC2 데이터 조회 중 오류 발생: {e}")
                
                # ECS 클러스터 목록
                try:
                    clusters = aws_services.list_ecs_clusters(region)
                    ecs_response = {
                        "service": "ecs",
                        "clusters": clusters
                    }
                    await broadcast_to_ws_clients(ecs_response)
                    logger.info(f"ECS 클러스터 {len(clusters)}개 전송됨")
                except Exception as e:
                    logger.error(f"ECS 데이터 조회 중 오류 발생: {e}")
                
                # EKS 클러스터 목록
                try:
                    eks_clusters = aws_services.list_eks_clusters(region)
                    eks_response = {
                        "service": "eks",
                        "clusters": eks_clusters
                    }
                    await broadcast_to_ws_clients(eks_response)
                    logger.info(f"EKS 클러스터 {len(eks_clusters)}개 전송됨")
                except Exception as e:
                    logger.error(f"EKS 데이터 조회 중 오류 발생: {e}")
                
                # 활동 로그
                activity_response = {
                    "service": "activity",
                    "message": "모든 AWS 서비스 데이터가 로드되었습니다."
                }
                await broadcast_to_ws_clients(activity_response)
                logger.info("모든 서비스 데이터 로드 완료 메시지 전송됨")
                return {"status": "success", "message": "모든 데이터를 요청했습니다."}
                
            # 특정 서비스 갱신 명령어 처리
            elif action == "refresh" and "service" in data:
                service = data.get("service")
                logger.info(f"{service.upper()} 서비스 갱신 요청 - 리전: {region}")
                
                if service == "ec2":
                    instances = aws_services.list_ec2_instances(region)
                    response = {
                        "service": "ec2",
                        "instances": instances
                    }
                    await broadcast_to_ws_clients(response)
                    logger.info(f"EC2 인스턴스 {len(instances)}개 전송됨")
                    return {"status": "success", "message": "EC2 데이터가 갱신되었습니다."}
                
                elif service == "ecs":
                    clusters = aws_services.list_ecs_clusters(region)
                    response = {
                        "service": "ecs",
                        "clusters": clusters
                    }
                    await broadcast_to_ws_clients(response)
                    logger.info(f"ECS 클러스터 {len(clusters)}개 전송됨")
                    return {"status": "success", "message": "ECS 데이터가 갱신되었습니다."}
                
                elif service == "eks":
                    clusters = aws_services.list_eks_clusters(region)
                    response = {
                        "service": "eks",
                        "clusters": clusters
                    }
                    await broadcast_to_ws_clients(response)
                    logger.info(f"EKS 클러스터 {len(clusters)}개 전송됨")
                    return {"status": "success", "message": "EKS 데이터가 갱신되었습니다."}
                    
                elif service == "activity":
                    activity_response = {
                        "service": "activity",
                        "status": "refresh",
                        "message": "활동 모니터링 데이터가 갱신되었습니다."
                    }
                    await broadcast_to_ws_clients(activity_response)
                    logger.info("활동 모니터링 데이터 갱신 메시지 전송됨")
                    return {"status": "success", "message": "활동 모니터링 데이터가 갱신되었습니다."}
        
        # 'type' 키가 있는 메시지 형식 (기존 형식 지원)
        elif "type" in data:
            message_type = data.get("type")
            content = data.get("content", {})
            logger.info(f"타입 기반 메시지 처리: {message_type}")
            
            # 활동 모니터링 관련 메시지 처리
            if message_type in [message_format.MessageType.KEYBOARD_ACTIVITY,
                              message_format.MessageType.MOUSE_MOVEMENT,
                              message_format.MessageType.MOUSE_CLICK,
                              message_format.MessageType.SCREEN_CHANGE,
                              message_format.MessageType.ACTIVE_WINDOW,
                              message_format.MessageType.AUDIO_PLAYBACK,
                              message_format.MessageType.USER_ACTIVITY]:
                # 활동 메시지는 모든 클라이언트에게 브로드캐스트
                await broadcast_to_ws_clients(data)
                logger.info(f"활동 모니터링 메시지 브로드캐스트: {message_type}")
                return {"status": "success", "message": "활동 메시지가 전송되었습니다."}
            
            # AWS 서비스 관련 명령어 처리
            if message_type == message_format.MessageType.AWS_EC2_LIST:
                instances = aws_services.list_ec2_instances(region)
                response = message_format.create_message(
                    message_format.MessageType.AWS_EC2_LIST, 
                    {"instances": instances}
                )
                await broadcast_to_ws_clients(response)
                logger.info(f"EC2 인스턴스 목록 브로드캐스트: {len(instances)}개")
                return response
            
            # ...기존 type에 따른 처리 로직...
    
    logger.warning(f"알 수 없는 메시지 형식: {data}")
    return {"status": "error", "message": "알 수 없는 메시지 형식입니다."}

def send_to_tcp_clients(message):
    """연결된 모든 TCP 클라이언트로 메시지를 전송합니다."""    
    global tcp_clients
    
    if not tcp_clients:
        logger.debug("연결된 TCP 클라이언트가 없습니다.")
        return False
    
    # 메시지가 문자열이 아닌 경우 JSON으로 변환
    if isinstance(message, dict):
        message_str = json.dumps(message, ensure_ascii=False)
        message_type = message.get("type", "UNKNOWN")
        message_id = message.get("id", "")[:8] if "id" in message else "NO_ID"
        logger.debug(f"TCP 메시지 전송 시작 - 타입: {message_type}, ID: {message_id}")
    else:
        message_str = str(message)
        logger.debug(f"TCP 문자열 메시지 전송 시작: {message_str[:50]}...")
    
    message_bytes = message_str.encode('utf-8')
    
    # 연결된 모든 TCP 클라이언트에게 메시지 전송
    disconnected_clients = []
    success_count = 0
    for client in tcp_clients:
        try:
            client.sendall(message_bytes)
            success_count += 1
        except Exception as e:
            logger.error(f"TCP 클라이언트 메시지 전송 중 오류 발생: {e}")
            disconnected_clients.append(client)
    
    # 연결이 끊어진 클라이언트 제거
    for client in disconnected_clients:
        try:
            client.close()
            tcp_clients.remove(client)
            logger.info("연결이 끊어진 TCP 클라이언트를 제거했습니다.")
        except:
            logger.warning("TCP 클라이언트 제거 중 오류 발생")
    
    if isinstance(message, dict):
        logger.info(f"TCP 메시지 전송 완료 - 타입: {message_type}, {success_count}/{len(tcp_clients)} 클라이언트 성공")
    else:
        logger.info(f"TCP 문자열 메시지 전송 완료: {success_count}/{len(tcp_clients)} 클라이언트 성공")
    
    return success_count > 0

def handle_tcp_client(client_socket, client_address):
    """TCP 클라이언트 연결을 처리하는 함수"""
    logger.info(f"TCP 클라이언트 연결됨: {client_address}")
    
    while True:
        try:
            # 데이터 수신 대기 (비차단 방식)
            ready = select.select([client_socket], [], [], 0.1)
            if ready[0]:
                data = b''
                while True:
                    chunk = client_socket.recv(4096)
                    if not chunk:
                        # 연결 종료
                        break
                    data += chunk
                    if len(chunk) < 4096:  # 더 이상 데이터가 없는 경우
                        break
                
                if not data:  # 빈 데이터면 연결 종료
                    logger.debug("TCP 클라이언트로부터 빈 데이터 수신. 연결 종료.")
                    break
                
                # 데이터 처리
                try:
                    # JSON 메시지 파싱 시도
                    try:
                        message = json.loads(data.decode('utf-8'))
                        logger.debug(f"TCP JSON 메시지 수신: {json.dumps(message, ensure_ascii=False)[:200]}...")
                        
                        # 표준 메시지 형식인 경우
                        if isinstance(message, dict):
                            # 활동 모니터링 메시지 처리
                            if "type" in message and message.get("type") in [
                                message_format.MessageType.KEYBOARD_ACTIVITY,
                                message_format.MessageType.MOUSE_MOVEMENT,
                                message_format.MessageType.MOUSE_CLICK,
                                message_format.MessageType.SCREEN_CHANGE,
                                message_format.MessageType.ACTIVE_WINDOW,
                                message_format.MessageType.AUDIO_PLAYBACK,
                                message_format.MessageType.USER_ACTIVITY
                            ]:
                                message_type = message.get("type")
                                content_type = message.get("content", {}).get("activity", "UNKNOWN") if isinstance(message.get("content"), dict) else "UNKNOWN"
                                logger.info(f"활동 메시지 수신됨: {message_type}, 활동: {content_type}")
                                
                                # 활동 모니터링 메시지는 WebSocket 클라이언트에게 전달
                                result = forward_activity_message(message)
                                if result:
                                    logger.info(f"활동 메시지 전달 성공: {message_type}, 활동: {content_type}")
                                else:
                                    logger.warning(f"활동 메시지 전달 실패: {message_type}, 활동: {content_type}")
                                continue
                            
                            # 기존 처리 로직
                            logger.info(f"구조화된 메시지 처리 시작: {message.get('action', 'UNKNOWN')}")
                            process_structured_message(message, client_socket)
                            continue
                    except json.JSONDecodeError as e:
                        # JSON이 아닌 경우, 기존 문자열 명령어로 처리
                        logger.warning(f"JSON 파싱 실패: {str(e)} - 문자열로 처리")
                        
                    # 이전 형식의 문자열 명령어 처리 (하위 호환성 유지)
                    command = data.decode().strip()
                    logger.debug(f"문자열 명령어 수신됨: {command}")
                    process_legacy_command(command, client_socket)
                    
                except Exception as e:
                    logger.error(f"TCP 메시지 처리 중 오류 발생: {e}")
                    logger.debug(f"에러 상세 정보: {traceback.format_exc()}")
                    error_response = message_format.create_message(
                        "ERROR", 
                        {"error": str(e), "message": "메시지 처리 중 오류가 발생했습니다."}
                    )
                    response_json = json.dumps(error_response, ensure_ascii=False).encode()
                    client_socket.sendall(response_json)
                    logger.debug("오류 응답 전송됨")
        
        except Exception as e:
            logger.error(f"TCP 클라이언트 처리 중 오류 발생: {e}")
            logger.debug(f"에러 상세 정보: {traceback.format_exc()}")
            break
    
    # 연결 종료
    logger.info(f"TCP 클라이언트 연결 종료: {client_address}")
    try:
        client_socket.close()
        if client_socket in tcp_clients:
            tcp_clients.remove(client_socket)
            logger.debug(f"TCP 클라이언트 목록에서 제거됨. 남은 클라이언트 수: {len(tcp_clients)}")
    except:
        logger.warning("TCP 클라이언트 연결 종료 중 오류 발생")

def process_structured_message(message, client_socket):
    """구조화된 JSON 메시지를 처리합니다."""    
    response = None
    region = message.get("region", DEFAULT_REGION)
    
    if isinstance(message, dict) and "action" in message:
        action = message.get("action")
        logger.info(f"구조화된 액션 처리: {action}")
        
        # 활동 모니터링 시작 명령 처리
        if action == "startMonitoring":
            logger.info("TCP 클라이언트로부터 활동 모니터링 시작 요청 수신")
            
            # 활동 모니터링 시작 코드 호출 - 블로킹 방지를 위해 별도 스레드로 처리
            def start_monitoring_thread():
                from core import activity_monitor
                try:
                    # 활동 모니터링 모듈 시작 시도
                    if not hasattr(activity_monitor, 'is_monitoring_active') or not activity_monitor.is_monitoring_active():
                        # 이미 실행 중인 프로세스가 있으면 강제 종료 후 시작
                        if activity_monitor.is_already_running():
                            logger.warning("이미 실행 중인 활동 모니터링 프로세스를 종료합니다.")
                            activity_monitor.find_and_kill_lock_process()
                            time.sleep(3)  # 완전히 종료될 시간 제공
                            
                        result = activity_monitor.start_monitoring()
                        if result:
                            logger.info("활동 모니터링이 성공적으로 시작되었습니다.")
                            success = True
                        else:
                            logger.warning("활동 모니터링 시작에 실패했습니다.")
                            success = False
                    else:
                        logger.info("활동 모니터링이 이미 실행 중입니다.")
                        success = True
                    
                    # 성공 여부에 따른 응답 메시지 생성
                    if success:
                        activity_response = {
                            "service": "activity",
                            "status": "started",
                            "message": "활동 모니터링이 시작되었습니다."
                        }
                    else:
                        activity_response = {
                            "service": "activity",
                            "status": "error",
                            "message": "활동 모니터링 시작에 실패했습니다."
                        }
                    
                    # TCP 클라이언트에 응답 전송
                    try:
                        client_socket.sendall(json.dumps(activity_response, ensure_ascii=False).encode())
                        logger.info("TCP 클라이언트에 활동 모니터링 시작 응답을 전송했습니다.")
                    except Exception as e:
                        logger.error(f"TCP 응답 전송 중 오류: {e}")
                    
                    # WebSocket 클라이언트에게도 브로드캐스트
                    try:
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        new_loop.run_until_complete(broadcast_to_ws_clients(activity_response))
                        new_loop.close()
                        logger.info("모든 WebSocket 클라이언트에 활동 모니터링 시작 메시지를 브로드캐스트했습니다.")
                    except Exception as e:
                        logger.error(f"WebSocket 브로드캐스트 중 오류 발생: {e}")
                        
                except Exception as e:
                    logger.error(f"활동 모니터링 시작 스레드에서 오류 발생: {e}")
                    logger.debug(f"에러 상세 정보: {traceback.format_exc()}")
                    try:
                        error_response = {
                            "service": "activity",
                            "status": "error",
                            "message": f"활동 모니터링 시작 중 오류 발생: {str(e)}"
                        }
                        client_socket.sendall(json.dumps(error_response, ensure_ascii=False).encode())
                    except:
                        pass
            
            # 스레드를 시작하여 비동기적으로 처리
            monitor_thread = threading.Thread(target=start_monitoring_thread)
            monitor_thread.daemon = True
            monitor_thread.start()
            
            # 임시 응답을 즉시 반환하여 클라이언트가 기다리지 않도록 함
            temp_response = {
                "service": "activity",
                "status": "processing",
                "message": "활동 모니터링 시작 처리 중..."
            }
            try:
                client_socket.sendall(json.dumps(temp_response, ensure_ascii=False).encode())
                logger.debug("임시 응답이 TCP 클라이언트에 전송되었습니다.")
            except Exception as e:
                logger.error(f"임시 응답 전송 중 오류: {e}")
            
            return
        
        # getAll 명령어 처리
        elif action == "getAll":
            logger.info(f"모든 AWS 서비스 데이터 요청 (TCP) - 리전: {region}")
            # EC2 인스턴스 목록
            try:
                instances = aws_services.list_ec2_instances(region)
                ec2_response = {
                    "service": "ec2",
                    "instances": instances
                }
                client_socket.sendall(json.dumps(ec2_response, ensure_ascii=False).encode())
                logger.info(f"EC2 인스턴스 {len(instances)}개 전송됨 (TCP)")
                
                # 비동기 방식으로 WebSocket 클라이언트에게 브로드캐스트
                try:
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    new_loop.run_until_complete(broadcast_to_ws_clients(ec2_response))
                    new_loop.close()
                    logger.debug("EC2 인스턴스 데이터 WebSocket 브로드캐스트 완료")
                except Exception as e:
                    logger.error(f"EC2 응답 브로드캐스트 중 오류: {e}")
            except Exception as e:
                logger.error(f"EC2 데이터 조회 중 오류 발생: {e}")
            
            # ECS 클러스터 목록
            try:
                clusters = aws_services.list_ecs_clusters(region)
                ecs_response = {
                    "service": "ecs",
                    "clusters": clusters
                }
                client_socket.sendall(json.dumps(ecs_response, ensure_ascii=False).encode())
                logger.info(f"ECS 클러스터 {len(clusters)}개 전송됨 (TCP)")
                
                # 비동기 방식으로 WebSocket 클라이언트에게 브로드캐스트
                try:
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    new_loop.run_until_complete(broadcast_to_ws_clients(ecs_response))
                    new_loop.close()
                    logger.debug("ECS 클러스터 데이터 WebSocket 브로드캐스트 완료")
                except Exception as e:
                    logger.error(f"ECS 응답 브로드캐스트 중 오류: {e}")
            except Exception as e:
                logger.error(f"ECS 데이터 조회 중 오류 발생: {e}")
            
            # EKS 클러스터 목록
            try:
                eks_clusters = aws_services.list_eks_clusters(region)
                eks_response = {
                    "service": "eks",
                    "clusters": eks_clusters
                }
                client_socket.sendall(json.dumps(eks_response, ensure_ascii=False).encode())
                logger.info(f"EKS 클러스터 {len(eks_clusters)}개 전송됨 (TCP)")
                
                # 비동기 방식으로 WebSocket 클라이언트에게 브로드캐스트
                try:
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    new_loop.run_until_complete(broadcast_to_ws_clients(eks_response))
                    new_loop.close()
                    logger.debug("EKS 클러스터 데이터 WebSocket 브로드캐스트 완료")
                except Exception as e:
                    logger.error(f"EKS 응답 브로드캐스트 중 오류: {e}")
            except Exception as e:
                logger.error(f"EKS 데이터 조회 중 오류 발생: {e}")
            
            # 활동 로그
            activity_response = {
                "service": "activity",
                "message": "모든 AWS 서비스 데이터가 로드되었습니다."
            }
            client_socket.sendall(json.dumps(activity_response, ensure_ascii=False).encode())
            logger.info("활동 로그 메시지 전송됨 (TCP)")
            
            # 비동기 방식으로 WebSocket 클라이언트에게 브로드캐스트
            try:
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                new_loop.run_until_complete(broadcast_to_ws_clients(activity_response))
                new_loop.close()
                logger.debug("활동 로그 Web브로드캐스트 완료")
            except Exception as e:
                logger.error(f"활동 로그 브로드캐스트 중 오류: {e}")
                
            return
            
        # 특정 서비스 갱신 명령어 처리
        elif action == "refresh" and "service" in message:
            service = message.get("service")
            logger.info(f"{service.upper()} 서비스 갱신 요청 (TCP) - 리전: {region}")
            
            if service == "ec2":
                try:
                    instances = aws_services.list_ec2_instances(region)
                    response = {
                        "service": "ec2",
                        "instances": instances
                    }
                    # 클라이언트에 직접 응답 전송 (중복 방지를 위해 이 부분만 수정)
                    client_socket.sendall(json.dumps(response, ensure_ascii=False).encode())
                    logger.info(f"EC2 인스턴스 {len(instances)}개 조회됨")
                    
                    # WebSocket 클라이언트에게 브로드캐스트
                    try:
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        new_loop.run_until_complete(broadcast_to_ws_clients(response))
                        new_loop.close()
                    except Exception as e:
                        logger.error(f"WebSocket 브로드캐스트 중 오류: {e}")
                    
                    # 중복 응답 방지를 위해 response 변수 초기화
                    response = None
                except Exception as e:
                    logger.error(f"EC2 데이터 조회 중 오류 발생: {e}")
                    response = {
                        "service": "ec2",
                        "error": str(e),
                        "message": "EC2 데이터 조회 중 오류가 발생했습니다."
                    }
            
            elif service == "ecs":
                try:
                    clusters = aws_services.list_ecs_clusters(region)
                    response = {
                        "service": "ecs",
                        "clusters": clusters
                    }
                    # 클라이언트에 직접 응답 전송 (중복 방지를 위해 이 부분만 수정)
                    client_socket.sendall(json.dumps(response, ensure_ascii=False).encode())
                    logger.info(f"ECS 클러스터 {len(clusters)}개 조회됨")
                    
                    # WebSocket 클라이언트에게 브로드캐스트
                    try:
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        new_loop.run_until_complete(broadcast_to_ws_clients(response))
                        new_loop.close()
                    except Exception as e:
                        logger.error(f"WebSocket 브로드캐스트 중 오류: {e}")
                    
                    # 중복 응답 방지를 위해 response 변수 초기화
                    response = None
                except Exception as e:
                    logger.error(f"ECS 데이터 조회 중 오류 발생: {e}")
                    response = {
                        "service": "ecs",
                        "error": str(e),
                        "message": "ECS 데이터 조회 중 오류가 발생했습니다."
                    }
            
            elif service == "eks":
                try:
                    clusters = aws_services.list_eks_clusters(region)
                    response = {
                        "service": "eks",
                        "clusters": clusters
                    }
                    # 클라이언트에 직접 응답 전송 (중복 방지를 위해 이 부분만 수정)
                    client_socket.sendall(json.dumps(response, ensure_ascii=False).encode())
                    logger.info(f"EKS 클러스터 {len(clusters)}개 조회됨")
                    
                    # WebSocket 클라이언트에게 브로드캐스트
                    try:
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        new_loop.run_until_complete(broadcast_to_ws_clients(response))
                        new_loop.close()
                    except Exception as e:
                        logger.error(f"WebSocket 브로드캐스트 중 오류: {e}")
                    
                    # 중복 응답 방지를 위해 response 변수 초기화
                    response = None
                except Exception as e:
                    logger.error(f"EKS 데이터 조회 중 오류 발생: {e}")
                    response = {
                        "service": "eks",
                        "error": str(e),
                        "message": "EKS 데이터 조회 중 오류가 발생했습니다."
                    }
                
    # AWS 서비스 명령어 처리 (기존 표준 메시지 형식 지원)
    elif isinstance(message, dict) and "type" in message:
        message_type = message.get("type")
        content = message.get("content", {})
        logger.info(f"타입 기반 메시지 처리 (TCP): {message_type}")
        
        # 활동 모니터링 메시지 처리
        if message_type in [
            message_format.MessageType.KEYBOARD_ACTIVITY,
            message_format.MessageType.MOUSE_MOVEMENT,
            message_format.MessageType.MOUSE_CLICK,
            message_format.MessageType.SCREEN_CHANGE,
            message_format.MessageType.ACTIVE_WINDOW,
            message_format.MessageType.AUDIO_PLAYBACK,
            message_format.MessageType.USER_ACTIVITY
        ]:
            # 모든 클라이언트에게 브로드캐스트
            content_type = content.get("activity", "UNKNOWN") if isinstance(content, dict) else "UNKNOWN"
            logger.info(f"활동 메시지 브로드캐스트 시작 - 타입: {message_type}, 활동: {content_type}")
            
            response = message
            # TCP 클라이언트에게 브로드캐스트
            tcp_result = send_to_tcp_clients(response)
            if tcp_result:
                logger.debug("TCP 클라이언트 브로드캐스트 성공")
            else:
                logger.warning("TCP 클라이언트 브로드캐스트 실패 또는 클라이언트 없음")
                
            # WebSocket 클라이언트에게도 브로드캐스트
            try:
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                new_loop.run_until_complete(broadcast_to_ws_clients(response))
                new_loop.close()
                logger.info(f"활동 메시지 브로드캐스트 완료: {message_type}, 활동: {content_type}")
            except Exception as e:
                logger.error(f"활동 메시지 브로드캐스트 중 오류: {e}")
            return
        
        # AWS 서비스 관련 명령어 처리
        if message_type == message_format.MessageType.AWS_EC2_LIST:
            try:
                instances = aws_services.list_ec2_instances(region)
                response = message_format.create_message(
                    message_format.MessageType.AWS_EC2_LIST, 
                    {"instances": instances}
                )
                logger.info(f"EC2 인스턴스 {len(instances)}개 조회됨 (타입 기반 메시지)")
            except Exception as e:
                logger.error(f"EC2 데이터 조회 중 오류 발생: {e}")
                response = message_format.create_message(
                    "ERROR", 
                    {"error": str(e), "message": "EC2 데이터 조회 중 오류가 발생했습니다."}
                )
        
        # ...기존 로직...
    
    # 응답 전송
    if response:
        try:
            response_json = json.dumps(response, ensure_ascii=False).encode()
            client_socket.sendall(response_json)
            logger.debug(f"TCP 응답 전송됨: {len(response_json)} 바이트")
            
            # 모든 클라이언트에게 브로드캐스트
            send_to_tcp_clients(response)
            
            # WebSocket 클라이언트에게도 브로드캐스트
            try:
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                new_loop.run_until_complete(broadcast_to_ws_clients(response))
                new_loop.close()
                logger.debug("응답 WebSocket 브로드캐스트 완료")
            except Exception as e:
                logger.error(f"응답 브로드캐스트 중 오류: {e}")
        except Exception as e:
            logger.error(f"응답 전송 중 오류: {e}")

def process_legacy_command(command, client_socket):
    """이전 형식의 문자열 명령어를 처리합니다 (하위 호환성)."""
    logger.info(f"레거시 명령어 처리: {command}")
    # ...기존 legacy command 처리 로직...

def start_tcp_server():
    """TCP 서버를 실행하여 클라이언트 요청을 처리합니다."""    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server.bind((SERVER_IP, TCP_PORT))
        server.listen(5)
        logger.info(f"TCP 서버가 {SERVER_IP}:{TCP_PORT}에서 시작되었습니다.")
        
        while True:
            client, address = server.accept()
            tcp_clients.append(client)
            logger.info(f"새 TCP 클라이언트 연결됨: {address}")
            logger.debug(f"현재 TCP 클라이언트 수: {len(tcp_clients)}")
            
            # 각 클라이언트 연결을 별도의 스레드에서 처리
            client_thread = threading.Thread(target=handle_tcp_client, args=(client, address), name=f"TCP-Client-{address[0]}:{address[1]}")
            client_thread.daemon = True
            client_thread.start()
            logger.debug(f"TCP 클라이언트 스레드 시작됨: {client_thread.name}")
            
    except Exception as e:
        logger.error(f"TCP 서버 오류 발생: {e}")
        logger.debug(f"에러 상세 정보: {traceback.format_exc()}")
    finally:
        server.close()
        logger.info("TCP 서버가 종료되었습니다.")

async def start_websocket_server():
    """WebSocket 서버를 시작합니다."""    
    global event_loop
    event_loop = asyncio.get_event_loop()
    
    try:
        logger.info(f"WebSocket 서버가 {SERVER_IP}:{WS_PORT}에서 시작됩니다.")
        
        # WebSocket 서버 설정 개선
        # max_size를 늘리고, ping_interval을 설정하여 연결 안정성 향상
        # close_timeout을 늘려 비정상적인 종료에 대한 유예 시간 제공
        # max_queue를 늘려 많은 클라이언트가 대기할 수 있도록 함
        server = await websockets.serve(
            lambda websocket, path: handle_websocket(websocket), 
            SERVER_IP, 
            WS_PORT,
            max_size=10 * 1024 * 1024,  # 최대 메시지 크기 10MB
            ping_interval=30,  # 30초마다 ping 전송
            ping_timeout=10,   # ping 응답 10초 타임아웃
            close_timeout=5,   # 연결 종료 5초 타임아웃
            max_queue=32       # 메시지 큐 크기 증가
        )
        
        logger.info("WebSocket 서버가 시작되었습니다. 클라이언트 연결을 기다리는 중...")
        await asyncio.Future()  # 무한정 실행
    except Exception as e:
        logger.error(f"WebSocket 서버 오류 발생: {e}")
        logger.debug(f"에러 상세 정보: {traceback.format_exc()}")
    finally:
        logger.info("WebSocket 서버가 종료되었습니다.")

def run_server():
    """WebSocket 서버만 실행합니다."""    
    # 기본 로깅 설정
    logging.basicConfig(
        level=logging.DEBUG,  # 디버깅 목적으로 DEBUG 레벨 사용
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.StreamHandler(),  # 콘솔 출력
            logging.FileHandler('aws_monitor.log')  # 파일 출력
        ]
    )
    
    logger.info("========== WebSocket 서버 시작 ==========")
    logger.info(f"기본 AWS 리전: {DEFAULT_REGION}")
    
    # 활동 모니터링 시작
    try:
        from core import activity_monitor
        logger.info("활동 모니터링 모듈 시작 시도 중...")
        result = activity_monitor.start_monitoring()
        if result:
            logger.info("활동 모니터링이 성공적으로 시작되었습니다.")
        else:
            logger.warning("활동 모니터링이 이미 실행 중이거나 시작할 수 없습니다.")
    except Exception as e:
        logger.error(f"활동 모니터링 시작 중 오류: {e}")
    
    # WebSocket 서버 시작 (메인 스레드에서 실행)
    try:
        logger.info(f"WebSocket 서버를 {SERVER_IP}:{WS_PORT}에서 시작합니다.")
        asyncio.run(start_websocket_server())
    except KeyboardInterrupt:
        logger.info("사용자에 의해 서버가 종료되었습니다.")
    except Exception as e:
        logger.error(f"서버 실행 중 예상치 못한 오류 발생: {e}")
        logger.debug(f"에러 상세 정보: {traceback.format_exc()}")
    
    logger.info("========== WebSocket 서버 종료 ==========")
    return None  # TCP thread 반환하지 않음