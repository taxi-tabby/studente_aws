# AWS 서비스 모니터링 서버 (Backend)

이 디렉토리는 AWS 서비스 관리 및 사용자 활동 모니터링 애플리케이션의 서버 부분을 포함합니다.

## 개요

서버 컴포넌트는 다음과 같은 핵심 기능을 제공합니다:
- 사용자 활동 모니터링 (키보드, 마우스, 화면, 오디오 등)
- AWS 서비스 자동 관리 (EC2, ECS, EKS)
- UDP 서버를 통한 명령 처리
- 설정 및 서비스 관리 기능

## 주요 모듈

### activity_monitor.py
사용자 활동을 감지하는 모듈로 키보드 입력, 마우스 움직임, 화면 변화, 소리 재생 등을 모니터링합니다.

```python
# 사용 예시
from core.activity_monitor import ActivityMonitor

# 모니터 인스턴스 생성
monitor = ActivityMonitor()

# 모니터링 시작
monitor.start()

# 사용자 활동 확인
is_active = monitor.is_user_active()
```

### aws_auth.py
AWS 서비스 인증을 처리하는 모듈입니다. AWS 자격 증명을 관리하고 세션을 생성합니다.

```python
# 사용 예시
from core.aws_auth import AWSAuth

# AWS 인증 객체 생성
auth = AWSAuth()

# 자격 증명 설정
auth.set_credentials("ACCESS_KEY_ID", "SECRET_ACCESS_KEY")

# 세션 생성
session = auth.get_session("ap-northeast-2")
```

### aws_services.py
AWS 리소스(EC2, ECS, EKS)를 관리하는 모듈입니다. 서비스 조회, 시작, 중지 기능을 제공합니다.

```python
# 사용 예시
from core.aws_services import AWSServices

# 서비스 객체 생성
aws_services = AWSServices()

# EC2 인스턴스 목록 조회
instances = aws_services.list_ec2_instances("ap-northeast-2")

# EC2 인스턴스 시작
aws_services.start_ec2_instance("i-1234567890abcdef0", "ap-northeast-2")
```

### service_manager.py
등록된 AWS 서비스를 자동으로 관리하는 모듈입니다. 사용자 활동 감지에 따라 서비스를 시작하거나 중지합니다.

```python
# 사용 예시
from core.service_manager import ServiceManager

# 서비스 매니저 생성
manager = ServiceManager()

# 서비스 관리 시작
manager.start()

# 서비스 등록
manager.register_ec2_service("i-1234567890abcdef0", "ap-northeast-2", "개발 서버")
```

### tcp_server.py / udp_server.py
명령을 수신하고 처리하는 서버 모듈입니다. 클라이언트로부터 요청을 받아 적절한 작업을 수행합니다.

```python
# 사용 예시
from core.udp_server import UDPServer

# UDP 서버 생성
server = UDPServer("127.0.0.1", 20200)

# 서버 시작
server.start()
```

## 설정 모듈

### config/config_loader.py
설정 파일을 로드하고 관리하는 모듈입니다. JSON 형식의 설정 파일을 처리합니다.

```python
# 사용 예시
from core.config.config_loader import ConfigLoader

# 설정 로더 생성
config = ConfigLoader()

# 설정 값 가져오기
timeout = config.get("activity_monitor.inactivity_timeout_minutes")
```

## 메시지 모듈

### messages/message_format.py
클라이언트와 서버 간의 메시지 형식을 정의하고 처리하는 모듈입니다. JSON 형식의 메시지를 처리합니다.

```python
# 사용 예시
from core.messages.message_format import Message

# 메시지 생성
msg = Message.create("AWS_EC2_LIST", {})

# 메시지 파싱
parsed_msg = Message.parse(json_string)
```

## 서버 실행 방법

서버 모듈은 main.py 스크립트를 통해 실행됩니다:

```bash
python main.py
```

또는 빌드된 실행 파일을 통해 실행할 수 있습니다.

## 시스템 요구 사항

- Python 3.7 이상
- boto3 라이브러리 (AWS SDK)
- pynput (키보드/마우스 모니터링)
- opencv-python (화면 변화 감지)
- numpy
- pyyaml (YAML 파일 처리)
- pyaudio (오디오 감지)

## 서버 설정

서버의 동작은 `config/settings.json` 파일을 통해 구성할 수 있습니다.
주요 설정 항목:

1. **activity_monitor**: 사용자 활동 모니터링 설정
   - inactivity_timeout_minutes: 사용자 부재 판단 시간(분)
   - 각 모니터링 유형별 활성화/비활성화 설정

2. **aws**: AWS 관련 설정
   - regions: 검색할 AWS 리전 목록
   - credentials: 자격 증명 관련 설정
   - service_state_check_interval_minutes: 서비스 상태 확인 간격

3. **udp_server**: UDP 서버 설정
   - ip: 바인딩할 IP 주소
   - port: 사용할 포트 번호
   - buffer_size: 버퍼 크기

## 테스트 방법

서버 모듈을 테스트하기 위한 간단한 UDP 클라이언트 예제:

```python
import socket
import json

def send_command(command):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_address = ('localhost', 20200)
    
    # 텍스트 명령어 전송
    client_socket.sendto(command.encode(), server_address)
    
    # 응답 수신
    data, _ = client_socket.recvfrom(4096)
    return data.decode()

# EC2 인스턴스 목록 조회
response = send_command("LIST_EC2")
print(response)

# JSON 형식 명령어 전송
def send_json_command(command_type, content=None):
    if content is None:
        content = {}
    
    message = {
        "id": "test-request",
        "type": command_type,
        "timestamp": int(time.time()),
        "source": "test-client",
        "content": content
    }
    
    return send_command(json.dumps(message))

# JSON 형식으로 EC2 목록 조회
response = send_json_command("AWS_EC2_LIST")
print(response)
```

## 로깅

서버 모듈은 로깅을 위해 Python의 표준 logging 모듈을 사용합니다.
로그는 'aws_monitor.log' 파일에 기록되며, 다음과 같이 로그 레벨과 포맷이 구성되어 있습니다:

```
[시간] [로그 레벨] [모듈명] - 메시지 내용
```

## 보안 고려사항

1. AWS 자격 증명은 안전하게 저장되어야 합니다.
2. UDP 통신은 기본적으로 암호화되지 않으므로, 신뢰할 수 있는 네트워크에서만 사용해야 합니다.
3. 중요한 프로덕션 서비스는 자동 관리 대상에서 제외해야 합니다.

## 문제 해결

1. **AWS 인증 실패**
   - AWS 자격 증명이 올바른지 확인하세요.
   - IAM 권한이 충분한지 확인하세요.

2. **모니터링 기능 오작동**
   - 필요한 시스템 권한이 있는지 확인하세요.
   - 리소스 사용량이 높은 경우 일부 모니터링 기능을 비활성화하세요.

3. **UDP 서버 문제**
   - 포트가 다른 프로세스에 의해 사용 중인지 확인하세요.
   - 방화벽 설정을 확인하세요.

4. **서비스 관리 실패**
   - AWS API 할당량을 초과하지 않았는지 확인하세요.
   - 서비스 YAML 파일의 형식이 올바른지 확인하세요.