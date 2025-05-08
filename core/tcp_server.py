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
from core.commands.command_registry import process_command
from core.commands import command_definitions

# 로거 설정
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# 서버 설정
SERVER_IP = "127.0.0.1"
WS_PORT = 20201  # WebSocket 서버 포트
TCP_PORT = 20200  # TCP 서버 포트

# 클라이언트 연결 목록
ws_clients = set()
tcp_clients = []

# AWS 리전 설정
aws_regions = config.settings.get("aws", {}).get("regions", ["ap-northeast-2"])

# 활동 모니터링 메시지 처리를 위한 글로벌 이벤트 루프
event_loop = None

# WebSocket 메시지 브로드캐스트
async def broadcast_to_ws_clients(message, exclude_client=None):
    """연결된 모든 WebSocket 클라이언트에게 메시지를 전송합니다. exclude_client 파라미터가 있으면 해당 클라이언트는 제외합니다."""
    if not ws_clients:
        logger.debug("연결된 WebSocket 클라이언트가 없습니다.")
        return
        
    # 메시지가 문자열이 아닌 경우 JSON으로 변환
    if isinstance(message, dict):
        message_str = json.dumps(message, ensure_ascii=False)
        message_type = message.get("type", "UNKNOWN")
        message_id = message.get("id", "")[:8] if "id" in message else "NO_ID"
        logger.debug(f"WebSocket 브로드캐스트: 타입: {message_type}, ID: {message_id}")
    else:
        message_str = str(message)
        logger.debug(f"WebSocket 문자열 메시지 브로드캐스트: {message_str[:50]}...")
        
    disconnected_clients = set()
    success_count = 0
    for client in ws_clients:
        # 제외할 클라이언트면 건너뜀
        if exclude_client is not None and client == exclude_client:
            continue
            
        try:
            await client.send(message_str)
            success_count += 1
        except websockets.exceptions.ConnectionClosed:
            disconnected_clients.add(client)
            logger.warning(f"WebSocket 연결이 닫힘: {client.remote_address}")
        except Exception as e:
            logger.error(f"WebSocket 메시지 전송 중 오류: {e}")
            disconnected_clients.add(client)
            
    # 연결이 끊어진 클라이언트 제거
    for client in disconnected_clients:
        ws_clients.remove(client)
        logger.info(f"연결이 끊어진 WebSocket 클라이언트 제거: {client.remote_address if hasattr(client, 'remote_address') else 'Unknown'}")
    
    if isinstance(message, dict):
        logger.info(f"WebSocket 브로드캐스트 완료: {success_count}/{len(ws_clients) - (1 if exclude_client in ws_clients else 0)} 클라이언트 성공")
    else:
        logger.info(f"WebSocket 문자열 메시지 브로드캐스트 완료: {success_count}/{len(ws_clients) - (1 if exclude_client in ws_clients else 0)} 클라이언트 성공")

# 활동 모니터링 메시지 전달 함수
def forward_activity_message(message):
    """활동 모니터링 메시지를 모든 클라이언트에게 전달합니다."""
    global event_loop
    
    try:
        if isinstance(message, dict):
            message_type = message.get("type", "UNKNOWN")
            content_type = message.get("content", {}).get("activity", "UNKNOWN") if isinstance(message.get("content"), dict) else "UNKNOWN"
            message_id = message.get("id", "")[:8] if "id" in message else "NO_ID"
            
            logger.info(f"활동 모니터링 메시지 전달 - 타입: {message_type}, 활동: {content_type}")
            
            # TCP 클라이언트에게 메시지 전송
            tcp_success = send_to_tcp_clients(message)
            
            # WebSocket 클라이언트에게 메시지 전송
            ws_success = False
            if event_loop and event_loop.is_running():
                future = asyncio.run_coroutine_threadsafe(broadcast_to_ws_clients(message), event_loop)
                try:
                    future.result(timeout=3.0)
                    ws_success = True
                    logger.debug("활동 메시지 전송됨")
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
                    logger.debug("임시 이벤트 루프로 메시지 전송됨")
                except Exception as e:
                    logger.error(f"임시 이벤트 루프 생성 중 오류: {e}")
                
            return tcp_success or ws_success
    except Exception as e:
        logger.error(f"활동 모니터링 메시지 전달 중 오류: {e}")
        logger.debug(f"에러 상세 정보: {traceback.format_exc()}")
    
    return False

# WebSocket 핸들러
async def handle_websocket(websocket, path=None):
    """WebSocket 연결을 처리합니다. path 매개변수는 옵션으로 설정됨."""
    try:
        logger.info(f"WebSocket 클라이언트 연결됨: {websocket.remote_address}, 경로: {path}")
        
        # 클라이언트를 집합에 추가
        ws_clients.add(websocket)
        logger.debug(f"현재 WebSocket 클라이언트 수: {len(ws_clients)}")
        
        # 클라이언트 연결 확인 메시지 전송
        try:
            welcome_message = {
                "type": "connection",
                "status": "connected",
                "message": "WebSocket 서버에 연결되었습니다.",
                "self": True
            }
            await websocket.send(json.dumps(welcome_message, ensure_ascii=False))
            logger.debug("환영 메시지 전송됨")
        except Exception as e:
            logger.error(f"환영 메시지 전송 중 오류: {e}")
        
        # 메시지 수신 및 처리
        try:
            async for message in websocket:
                try:
                    logger.debug(f"WebSocket 메시지 수신: {message[:200] if len(message) > 200 else message}")
                    
                    # JSON 메시지 파싱 시도
                    try:
                        data = json.loads(message)
                        logger.debug(f"수신된 JSON 데이터: {json.dumps(data, ensure_ascii=False)[:500]}")
                        
                        # 유효한 데이터 형식 확인
                        if not isinstance(data, dict):
                            await websocket.send(json.dumps({
                                "status": "error", 
                                "message": "데이터가 올바른 JSON 객체 형식이 아닙니다.",
                                "self": True
                            }, ensure_ascii=False))
                            logger.warning("잘못된 데이터 형식: dict가 아님")
                            continue
                        
                        # 명령어 처리 시스템으로 메시지 전달
                        response = await process_command(data, websocket, data.get("region"))
                        if response:
                            # share 플래그가 있으면 모든 클라이언트에게 브로드캐스트
                            if isinstance(response, dict) and response.get("share") is True:
                                logger.info("'share' 플래그가 있는 응답을 모든 클라이언트에게 브로드캐스트합니다.")
                                # share 플래그 제거 후 브로드캐스트
                                broadcast_response = {k: v for k, v in response.items() if k != "share"}
                                # 다른 클라이언트에게는 self: False 설정
                                broadcast_response["self"] = False
                                await broadcast_to_ws_clients(broadcast_response, exclude_client=websocket)
                                # TCP 클라이언트에게도 전송
                                send_to_tcp_clients(broadcast_response, exclude_client=None)
                            
                            # 항상 요청한 클라이언트에게는 응답 전송 (self: True 확인)
                            if isinstance(response, dict) and "self" not in response:
                                response["self"] = True
                            await websocket.send(json.dumps(response, ensure_ascii=False))
                            logger.debug("WebSocket 응답 전송 완료")
                            
                    except json.JSONDecodeError:
                        # JSON이 아닌 경우, 텍스트 메시지로 처리
                        logger.warning(f"JSON 파싱 실패: {message[:50]}...")
                        await websocket.send(json.dumps({
                            "status": "error", 
                            "message": "유효한 JSON 형식이 아닙니다.",
                            "self": True
                        }, ensure_ascii=False))
                        
                    except Exception as e:
                        logger.error(f"WebSocket 메시지 처리 중 오류: {str(e)}")
                        logger.debug(f"에러 상세 정보: {traceback.format_exc()}")
                        await websocket.send(json.dumps({
                            "status": "error",
                            "message": f"메시지 처리 중 오류가 발생했습니다: {str(e)}",
                            "self": True
                        }, ensure_ascii=False))
                        
                except Exception as message_error:
                    logger.error(f"메시지 수신/처리 중 예외 발생: {str(message_error)}")
                    logger.debug(f"에러 상세 정보: {traceback.format_exc()}")
                    
        except websockets.exceptions.ConnectionClosed as e:
            logger.info(f"WebSocket 클라이언트 연결 종료됨: {websocket.remote_address} - 코드: {e.code}, 이유: {e.reason}")
            
        except Exception as e:
            logger.error(f"WebSocket 핸들러 오류: {e}")
            logger.debug(f"에러 상세 정보: {traceback.format_exc()}")
            
    except Exception as e:
        logger.error(f"WebSocket 연결 처리 중 오류: {e}")
        logger.debug(f"에러 상세 정보: {traceback.format_exc()}")
        
    finally:
        # 클라이언트 제거
        try:
            if websocket in ws_clients:
                ws_clients.remove(websocket)
                logger.info(f"WebSocket 클라이언트 연결 해제: {websocket.remote_address}")
                logger.debug(f"현재 WebSocket 클라이언트 수: {len(ws_clients)}")
        except Exception as e:
            logger.error(f"클라이언트 제거 중 오류: {e}")

def send_to_tcp_clients(message, exclude_client=None):
    """연결된 모든 TCP 클라이언트로 메시지를 전송합니다. exclude_client 파라미터가 있으면 해당 클라이언트는 제외합니다."""    
    global tcp_clients
    
    if not tcp_clients:
        logger.debug("연결된 TCP 클라이언트가 없습니다.")
        return False
    
    # 메시지가 문자열이 아닌 경우 JSON으로 변환
    if isinstance(message, dict):
        message_str = json.dumps(message, ensure_ascii=False)
        message_type = message.get("type", "UNKNOWN")
        message_id = message.get("id", "")[:8] if "id" in message else "NO_ID"
        logger.debug(f"TCP 메시지 전송 - 타입: {message_type}, ID: {message_id}")
    else:
        message_str = str(message)
        logger.debug(f"TCP 문자열 메시지 전송: {message_str[:50]}...")
    
    message_bytes = message_str.encode('utf-8')
    
    # 연결된 모든 TCP 클라이언트에게 메시지 전송
    disconnected_clients = []
    success_count = 0
    for client in tcp_clients:
        # 제외할 클라이언트면 건너뜀
        if exclude_client is not None and client == exclude_client:
            continue
            
        try:
            client.sendall(message_bytes)
            success_count += 1
        except Exception as e:
            logger.error(f"TCP 클라이언트 메시지 전송 중 오류: {e}")
            disconnected_clients.append(client)
    
    # 연결이 끊어진 클라이언트 제거
    for client in disconnected_clients:
        try:
            client.close()
            tcp_clients.remove(client)
            logger.info("연결이 끊어진 TCP 클라이언트를 제거했습니다.")
        except:
            logger.warning("TCP 클라이언트 제거 중 오류 발생")
    
    client_count = len(tcp_clients) - (1 if exclude_client in tcp_clients else 0)
    logger.info(f"TCP 메시지 전송 완료: {success_count}/{client_count} 클라이언트 성공")
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
                        
                        # 명령어 처리 시스템으로 메시지 전달
                        if isinstance(message, dict):
                            # 명령어 처리 시스템으로 메시지 전달
                            loop = asyncio.new_event_loop()
                            response = loop.run_until_complete(process_command(message, client_socket, message.get("region")))
                            loop.close()
                            
                            # 응답이 있으면 클라이언트에게 전송
                            if response:
                                # share 플래그가 있으면 모든 클라이언트에게 브로드캐스트
                                if isinstance(response, dict) and response.get("share") is True:
                                    logger.info("TCP: 'share' 플래그가 있는 응답을 모든 클라이언트에게 브로드캐스트합니다.")
                                    # share 플래그 제거 후 브로드캐스트
                                    broadcast_response = {k: v for k, v in response.items() if k != "share"}
                                    
                                    # WebSocket 클라이언트에게 브로드캐스트
                                    if event_loop and event_loop.is_running():
                                        future = asyncio.run_coroutine_threadsafe(broadcast_to_ws_clients(broadcast_response), event_loop)
                                        try:
                                            future.result(timeout=3.0)
                                            logger.debug("공유 메시지가 WebSocket 클라이언트에게 전송됨")
                                        except Exception as e:
                                            logger.error(f"WebSocket 공유 메시지 전송 중 오류: {e}")
                                    else:
                                        # 임시 이벤트 루프 생성하여 메시지 전송
                                        try:
                                            new_loop = asyncio.new_event_loop()
                                            asyncio.set_event_loop(new_loop)
                                            new_loop.run_until_complete(broadcast_to_ws_clients(broadcast_response))
                                            new_loop.close()
                                            logger.debug("임시 이벤트 루프로 공유 메시지 전송됨")
                                        except Exception as e:
                                            logger.error(f"임시 이벤트 루프 생성 중 오류: {e}")
                                    
                                    # TCP 클라이언트에게도 전송
                                    send_to_tcp_clients(broadcast_response, exclude_client=client_socket)
                                
                                # 요청한 클라이언트에게 항상 응답 전송
                                client_socket.sendall(json.dumps(response, ensure_ascii=False).encode())
                            continue
                                
                    except json.JSONDecodeError:
                        # JSON이 아닌 경우, 문자열 명령어로 처리
                        pass
                    
                    # 문자열 명령어 처리
                    command = data.decode().strip()
                    logger.debug(f"문자열 명령어 수신됨: {command}")
                    process_legacy_command(command, client_socket)
                    
                except Exception as e:
                    logger.error(f"TCP 메시지 처리 중 오류: {e}")
                    logger.debug(f"에러 상세 정보: {traceback.format_exc()}")
                    error_response = {"status": "error", "message": f"메시지 처리 중 오류가 발생했습니다: {str(e)}"}
                    client_socket.sendall(json.dumps(error_response, ensure_ascii=False).encode())
        
        except Exception as e:
            logger.error(f"TCP 클라이언트 처리 중 오류: {e}")
            logger.debug(f"에러 상세 정보: {traceback.format_exc()}")
            break
    
    # 연결 종료
    logger.info(f"TCP 클라이언트 연결 종료: {client_address}")
    try:
        client_socket.close()
        if client_socket in tcp_clients:
            tcp_clients.remove(client_socket)
    except:
        logger.warning("TCP 클라이언트 연결 종료 중 오류 발생")

def process_legacy_command(command, client_socket):
    """이전 형식의 문자열 명령어를 처리합니다 (하위 호환성)."""
    logger.info(f"레거시 명령어 처리: {command}")
    # 간단한 응답 전송
    response = {"status": "processed", "command": command, "message": "명령이 처리되었습니다."}
    client_socket.sendall(json.dumps(response, ensure_ascii=False).encode())

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
            
            # 각 클라이언트 연결을 별도의 스레드에서 처리
            client_thread = threading.Thread(target=handle_tcp_client, args=(client, address))
            client_thread.daemon = True
            client_thread.start()
            
    except Exception as e:
        logger.error(f"TCP 서버 오류: {e}")
        logger.debug(f"에러 상세 정보: {traceback.format_exc()}")
    finally:
        server.close()
        logger.info("TCP 서버가 종료되었습니다.")

async def start_websocket_server():
    """WebSocket 서버를 비동기로 시작합니다."""
    global event_loop
    try:
        logger.info(f"WebSocket 서버가 {SERVER_IP}:{WS_PORT}에서 시작됩니다.")
        event_loop = asyncio.get_event_loop()
        
        # 서버 설정 및 시작
        server = await websockets.serve(
            handle_websocket,
            SERVER_IP, 
            WS_PORT,
            max_size=10 * 1024 * 1024,  # 10MB
            ping_interval=30,
            ping_timeout=10,
            close_timeout=5
        )
        
        logger.info(f"WebSocket 서버가 {SERVER_IP}:{WS_PORT}에서 시작되었습니다.")
        
        # 서버가 계속 실행되도록 대기
        await asyncio.Future()
        
    except Exception as e:
        logger.error(f"WebSocket 서버 시작 중 오류: {e}")
        logger.error(f"에러 상세 정보: {traceback.format_exc()}")

def run_server():
    """WebSocket 서버와 필요시 TCP 서버를 실행합니다."""    
    # 기본 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.StreamHandler(),  # 콘솔 출력
            logging.FileHandler('aws_monitor.log')  # 파일 출력
        ]
    )
    
    logger.info("========== 서버 시작 ==========")
    
    # 명령어 핸들러 시스템에 브로드캐스트 함수 등록
    command_definitions.set_broadcast_functions(broadcast_to_ws_clients, send_to_tcp_clients)
    
    # 새로운 중앙화된 브로드캐스트 기능 등록
    from core.commands.command_registry import set_broadcast_function
    set_broadcast_function(broadcast_to_ws_clients)
    logger.info("명령어 핸들러 시스템에 브로드캐스트 함수가 등록되었습니다.")
    
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
    
    # WebSocket 서버 시작
    try:
        # TCP 서버 스레드 시작
        tcp_thread = threading.Thread(target=start_tcp_server)
        tcp_thread.daemon = True
        tcp_thread.start()
        logger.info("TCP 서버 스레드가 시작되었습니다.")
        
        # WebSocket 서버 코루틴 실행
        logger.info(f"WebSocket 서버를 {SERVER_IP}:{WS_PORT}에서 시작합니다.")
        asyncio.run(start_websocket_server())
        
    except Exception as e:
        logger.error(f"서버 시작 중 오류 발생: {e}")
        logger.error(f"에러 상세 정보: {traceback.format_exc()}")
    
    logger.info("========== 서버 종료 ==========")
    return None