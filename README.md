# AWS 서비스 관리 및 사용자 활동 모니터링 애플리케이션

이 애플리케이션은 사용자의 활동(키보드, 마우스, 화면 변화, 소리 재생 등)을 모니터링하고, AWS 서비스(EC2, ECS, EKS)를 자동으로 관리하는 백그라운드 애플리케이션입니다. 사용자가 일정 시간 동안 감지되지 않으면 등록된 AWS 서비스를 자동으로 종료하고, 다시 감지되면 서비스를 시작하여 AWS 비용을 절감합니다.

## 주요 기능

- 사용자 활동 감지
  - 키보드 입력 감지
  - 마우스 움직임 및 클릭 감지
  - 화면 변화 감지
  - 활성 창 변경 감지
  - 오디오 재생 감지

- AWS 서비스 자동 관리
  - 사용자 부재 시 EC2, ECS, EKS 서비스 자동 종료
  - 사용자 활동 감지 시 서비스 자동 시작
  - 설정된 비활성 시간(기본 30분) 후 자동 종료
  - YAML 파일을 통한 관리 대상 서비스 설정

- AWS 서비스 수동 관리
  - EC2 인스턴스 조회/시작/중지
  - ECS 클러스터 및 서비스 조회/시작/중지
  - EKS 클러스터 조회 및 노드그룹 스케일링

- 기타 기능
  - UDP 서버를 통한 명령 처리 (포트 20200)
  - AWS 인증 GUI 제공
  - 중복 실행 방지
  - JSON 파일 기반 설정 관리

## 설치 방법

### 필수 요구사항

- Python 3.7 이상
- pip 패키지 관리자

### 의존성 설치

```bash
pip install -r requirements.txt
```

### 직접 실행하기

```bash
python main.py
```

### 실행 파일로 빌드하기

Windows에서:
```bash
powershell -ExecutionPolicy Bypass -File .\build_executable.ps1
```

Linux/Mac에서:
```bash
chmod +x build_executable.sh
./build_executable.sh
```

## 사용 방법

1. **첫 실행 시 AWS 인증**
   - 애플리케이션 실행 시 AWS Access Key ID와 Secret Access Key를 입력하는 창이 나타납니다.
   - 올바른 자격 증명을 입력하면 인증에 성공하고, 이후 백그라운드에서 실행됩니다.
   - "자격 증명 저장" 옵션을 체크하면 다음 실행 시 자동으로 인증됩니다.

2. **서비스 자동 관리**
   - 애플리케이션은 사용자 활동을 지속적으로 모니터링합니다.
   - 설정된 시간(기본 30분) 동안 사용자 활동이 감지되지 않으면 등록된 모든 AWS 서비스를 자동으로 종료합니다.
   - 사용자 활동이 다시 감지되면 이전에 실행 중이던 서비스를 자동으로 시작합니다.
   - 관리 대상 서비스는 `services.yaml` 파일에 등록됩니다.

3. **UDP 통신을 통한 서비스 등록 및 명령 전송**
   - UDP 클라이언트를 통해 포트 20200으로 서비스 등록 및 명령을 전송할 수 있습니다.
   
   **텍스트 기반 명령어 예시:**
   ```
   LIST_EC2             # EC2 인스턴스 목록 조회
   LIST_ECS             # ECS 클러스터 목록 조회
   LIST_EKS             # EKS 클러스터 목록 조회
   LIST_ALL_SERVICES    # 모든 서비스 목록 조회
   START_EC2:인스턴스ID:리전   # EC2 인스턴스 시작
   STOP_EC2:인스턴스ID:리전    # EC2 인스턴스 중지
   START_ECS:클러스터명:서비스명:리전  # ECS 서비스 시작
   STOP_ECS:클러스터명:서비스명:리전   # ECS 서비스 중지
   SCALE_EKS:클러스터명:노드그룹명:리전:노드수  # EKS 노드그룹 스케일링
   
   # 관리 대상 서비스 등록
   REGISTER_EC2:인스턴스ID:리전   # EC2 인스턴스 자동 관리 등록
   REGISTER_ECS:클러스터명:서비스명:리전  # ECS 서비스 자동 관리 등록
   REGISTER_EKS:클러스터명:노드그룹명:리전  # EKS 노드그룹 자동 관리 등록
   
   # 관리 대상 서비스 제거
   UNREGISTER_EC2:인스턴스ID:리전  # EC2 인스턴스 자동 관리 해제
   UNREGISTER_ECS:클러스터명:서비스명:리전  # ECS 서비스 자동 관리 해제
   UNREGISTER_EKS:클러스터명:노드그룹명:리전  # EKS 노드그룹 자동 관리 해제
   
   # 등록된 서비스 조회
   LIST_REGISTERED_SERVICES  # 자동 관리 대상 서비스 목록 조회
   ```
   
   **JSON 형식 명령어 예시:**
   ```json
   {
     "id": "요청ID",
     "type": "AWS_EC2_LIST",
     "timestamp": 1621234567,
     "source": "client",
     "content": {}
   }
   
   {
     "id": "요청ID",
     "type": "REGISTER_SERVICE",
     "timestamp": 1621234567,
     "source": "client",
     "content": {
       "service_type": "EC2",
       "instance_id": "i-1234567890abcdef0",
       "region": "ap-northeast-2"
     }
   }
   ```

4. **설정 파일 수정**
   - `core/config/settings.json` 파일을 수정하여 애플리케이션의 동작을 제어할 수 있습니다.
   - 각 모니터링 기능의 활성화/비활성화 및 세부 설정 조정이 가능합니다.
   - `inactivity_timeout_minutes` 값을 수정하여 사용자 부재 감지 시간을 조정할 수 있습니다(기본값: 30분).

## 서비스 등록 파일 (YAML)

애플리케이션은 자동으로 관리할 AWS 서비스 목록을 YAML 파일(`services.yaml`)로 관리합니다. 파일 구조는 다음과 같습니다:

```yaml
ec2_instances:
  - instance_id: i-1234567890abcdef0
    region: ap-northeast-2
    description: "개발 서버"
  - instance_id: i-0987654321fedcba0
    region: us-west-2
    description: "테스트 서버"

ecs_services:
  - cluster_name: my-cluster
    service_name: my-service
    region: ap-northeast-2
    description: "API 서버"

eks_nodegroups:
  - cluster_name: my-eks-cluster
    nodegroup_name: my-nodegroup
    region: ap-northeast-2
    desired_size: 2
    description: "쿠버네티스 클러스터"
```

이 파일은 UDP 명령을 통해 서비스를 등록하거나 해제할 때 자동으로 업데이트됩니다. 직접 수정할 수도 있으나, 애플리케이션이 실행 중일 때는 UDP 명령을 통해 변경하는 것이 좋습니다.

## 설정 파일 옵션

`core/config/settings.json` 파일에서 다음 설정을 조정할 수 있습니다:

- **activity_monitor**: 사용자 활동 모니터링 설정
  - **inactivity_timeout_minutes**: 사용자 부재 판단 시간(분)
  - **keyboard**: 키보드 활동 감지 설정
  - **mouse**: 마우스 활동 감지 설정
  - **screen**: 화면 변화 감지 설정
  - **audio**: 오디오 재생 감지 설정
  - **window**: 활성 창 감지 설정

- **aws**: AWS 관련 설정
  - **regions**: 검색할 AWS 리전 목록
  - **credentials**: 인증 관련 설정
  - **service_state_check_interval_minutes**: 서비스 상태 확인 간격(분)

- **udp_server**: UDP 서버 설정
  - **ip**: 바인딩할 IP 주소
  - **port**: 사용할 포트 번호
  - **buffer_size**: 버퍼 크기

## 프로젝트 구조

```
aws_study/
├── core/
│   ├── __init__.py
│   ├── activity_monitor.py   # 사용자 활동 모니터링 기능
│   ├── aws_auth.py           # AWS 인증 관련 기능
│   ├── aws_services.py       # AWS 서비스 관리 기능
│   ├── service_manager.py    # 서비스 자동 관리 기능
│   ├── udp_server.py         # UDP 서버 및 명령어 처리
│   ├── config/
│   │   ├── __init__.py
│   │   ├── config_loader.py  # 설정 파일 관리
│   │   └── settings.json     # 설정 파일
│   └── messages/
│       ├── __init__.py
│       └── message_format.py # 메시지 형식 및 전송 기능
├── main.py                   # 메인 실행 파일
├── setup.py                  # 설치 스크립트
├── services.yaml             # 관리 대상 서비스 목록
├── build_executable.ps1      # Windows용 빌드 스크립트
└── build_executable.sh       # Linux/Mac용 빌드 스크립트
```

## 주의 사항

1. 이 애플리케이션은 백그라운드에서 실행되며, 중복 실행을 방지합니다.
2. AWS 자격 증명 정보는 안전하게 관리되어야 합니다.
3. 화면 변화 감지 및 오디오 감지는 시스템 리소스를 상당히 사용할 수 있습니다.
4. 설정 파일에서 필요한 기능만 활성화하여 사용하는 것을 권장합니다.
5. **중요:** 자동으로 종료되어도 문제가 없는 서비스만 등록하세요. 중요한 프로덕션 서비스는 등록하지 마세요!

## 비용 절감 효과

이 애플리케이션은 개발자가 자리를 비울 때 자동으로 AWS 서비스를 종료하고, 돌아왔을 때 다시 시작함으로써 다음과 같은 비용 절감 효과를 제공합니다:

- 야간 또는 근무 외 시간에 불필요한 서비스 실행 방지
- 주말 및 휴일 동안 서비스 자동 종료
- 개발 및 테스트 환경의 유휴 시간 최소화

실제 사례에서는 AWS 비용을 최대 70%까지 절감한 사례가 있습니다.

## 문제 해결

- **AWS 인증 실패**: 올바른 자격 증명을 입력했는지 확인하세요.
- **중복 실행 오류**: 이미 실행 중인 인스턴스가 있는지 확인하세요.
- **모듈 오류**: 필요한 모든 패키지가 설치되어 있는지 확인하세요.
- **UDP 통신 문제**: 방화벽 설정을 확인하고, 포트 20200이 열려 있는지 확인하세요.
- **서비스 자동 관리 오류**: `services.yaml` 파일이 올바르게 구성되어 있는지 확인하세요.

## 로그 확인

애플리케이션 실행 중 발생하는 로그는 `aws_monitor.log` 파일에 저장됩니다. 문제 발생 시 이 파일을 확인하여 오류 내용을 파악할 수 있습니다.



----
#### 개발 중

## 데모 화면

![애플리케이션 데모](readmeasset/s1.gif)

