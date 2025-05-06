"""
설정 파일 관리 모듈
"""
import os
import json
import logging
import yaml

# 로거 설정
logger = logging.getLogger(__name__)

class ConfigLoader:
    """설정 파일 관리 클래스"""
    
    def __init__(self):
        """초기화"""
        # 현재 디렉토리 확인
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.config_dir = os.path.dirname(os.path.abspath(__file__))
        self.settings_file = os.path.join(self.config_dir, 'settings.json')
        self.services_file = os.path.join(self.base_dir, 'services.yaml')
        
        # 기본 설정값
        self.default_settings = {
            "activity_monitor": {
                "inactivity_timeout_minutes": 30,
                "keyboard": {
                    "enabled": True
                },
                "mouse": {
                    "enabled": True,
                    "movement_threshold": 5  # 5픽셀 이상 이동 시 감지
                },
                "screen": {
                    "enabled": True,
                    "interval_seconds": 5,  # 5초마다 화면 변화 감지
                    "diff_threshold": 0.05  # 5% 이상 변화 시 감지
                },
                "audio": {
                    "enabled": True,
                    "interval_seconds": 2,  # 2초마다 오디오 감지
                    "volume_threshold": 0.01  # 볼륨 임계값 (0.0 ~ 1.0)
                },
                "window": {
                    "enabled": True,
                    "interval_seconds": 2  # 2초마다 활성 창 변화 감지
                }
            },
            "aws": {
                "regions": [
                    "ap-northeast-2",
                    "us-east-1",
                    "us-west-1",
                    "us-west-2",
                    "eu-central-1",
                    "eu-west-1"
                ],
                "credentials": {
                    "save": True
                },
                "service_state_check_interval_minutes": 5
            },
            "udp_server": {
                "ip": "127.0.0.1",
                "port": 20200,
                "buffer_size": 4096
            }
        }
        
        # 기본 서비스 구성
        self.default_services = {
            "ec2_instances": [],
            "ecs_services": [],
            "eks_nodegroups": []
        }
        
        # 설정 로드
        self.settings = self._load_settings()
        self.services = self._load_services()
    
    def _load_settings(self):
        """settings.json 파일 로드
        
        Returns:
            dict: 설정 정보
        """
        # 설정 파일이 없으면 기본 설정 저장 후 반환
        if not os.path.exists(self.settings_file):
            logger.info("설정 파일이 없습니다. 기본 설정을 사용합니다.")
            self._save_settings(self.default_settings)
            return self.default_settings
        
        # 설정 파일 로드
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            # 설정 파일의 구조가 기본 설정과 다른 경우 업데이트
            updated_settings = self._update_dict_structure(settings, self.default_settings)
            if updated_settings != settings:
                logger.info("설정 파일 구조가 업데이트되었습니다.")
                self._save_settings(updated_settings)
            
            logger.info("설정 파일을 로드했습니다.")
            return updated_settings
            
        except Exception as e:
            logger.error(f"설정 파일 로드 중 오류 발생: {e}")
            logger.info("기본 설정을 사용합니다.")
            return self.default_settings
    
    def _load_services(self):
        """services.yaml 파일 로드
        
        Returns:
            dict: 서비스 정보
        """
        # 서비스 파일이 없으면 기본 서비스 저장 후 반환
        if not os.path.exists(self.services_file):
            logger.info("서비스 파일이 없습니다. 빈 서비스 파일을 생성합니다.")
            self._save_services(self.default_services)
            return self.default_services
        
        # 서비스 파일 로드
        try:
            with open(self.services_file, 'r', encoding='utf-8') as f:
                services = yaml.safe_load(f) or {}
            
            # YAML 파일이 예상 구조와 다른 경우를 처리
            if not isinstance(services, dict):
                logger.warning("서비스 파일 형식이 올바르지 않습니다. 빈 서비스 파일을 생성합니다.")
                self._save_services(self.default_services)
                return self.default_services
            
            # 기본 키가 없는 경우 추가
            for key in self.default_services:
                if key not in services:
                    services[key] = []
            
            logger.info("서비스 파일을 로드했습니다.")
            return services
            
        except Exception as e:
            logger.error(f"서비스 파일 로드 중 오류 발생: {e}")
            logger.info("기본 서비스 설정을 사용합니다.")
            return self.default_services
    
    def _save_settings(self, settings):
        """settings.json 파일 저장
        
        Args:
            settings (dict): 저장할 설정 정보
            
        Returns:
            bool: 저장 성공 여부
        """
        try:
            os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4)
            logger.info("설정 파일을 저장했습니다.")
            return True
        except Exception as e:
            logger.error(f"설정 파일 저장 중 오류 발생: {e}")
            return False
    
    def _save_services(self, services):
        """services.yaml 파일 저장
        
        Args:
            services (dict): 저장할 서비스 정보
            
        Returns:
            bool: 저장 성공 여부
        """
        try:
            with open(self.services_file, 'w', encoding='utf-8') as f:
                yaml.dump(services, f, default_flow_style=False, sort_keys=False)
            logger.info("서비스 파일을 저장했습니다.")
            return True
        except Exception as e:
            logger.error(f"서비스 파일 저장 중 오류 발생: {e}")
            return False
    
    def _update_dict_structure(self, source, reference):
        """딕셔너리 구조를 참조 딕셔너리에 맞게 업데이트
        
        Args:
            source (dict): 업데이트할 딕셔너리
            reference (dict): 참조 딕셔너리
            
        Returns:
            dict: 업데이트된 딕셔너리
        """
        if not isinstance(source, dict) or not isinstance(reference, dict):
            return reference
        
        result = source.copy()
        
        # 참조 딕셔너리의 모든 키를 확인
        for key, value in reference.items():
            # 소스에 키가 없으면 참조의 값을 사용
            if key not in result:
                result[key] = value
            # 두 값이 모두 딕셔너리인 경우 재귀 호출
            elif isinstance(value, dict) and isinstance(result[key], dict):
                result[key] = self._update_dict_structure(result[key], value)
        
        return result
    
    def get_settings(self):
        """설정 정보 반환
        
        Returns:
            dict: 설정 정보
        """
        return self.settings
    
    def get_services(self):
        """서비스 정보 반환
        
        Returns:
            dict: 서비스 정보
        """
        return self.services
    
    def update_settings(self, new_settings):
        """설정 정보 업데이트
        
        Args:
            new_settings (dict): 새로운 설정 정보
            
        Returns:
            bool: 업데이트 성공 여부
        """
        try:
            # 기존 설정을 유지하면서 새 설정으로 업데이트
            updated_settings = self._update_dict_structure(new_settings, self.settings)
            
            # 설정 저장
            if self._save_settings(updated_settings):
                self.settings = updated_settings
                return True
            return False
            
        except Exception as e:
            logger.error(f"설정 업데이트 중 오류 발생: {e}")
            return False
    
    def get(self, section, key, default=None):
        """설정 값 가져오기
        
        Args:
            section (str): 설정 섹션
            key (str): 설정 키
            default: 기본값
            
        Returns:
            설정 값 또는 기본값
        """
        try:
            if section in self.settings and key in self.settings[section]:
                return self.settings[section][key]
            return default
        except Exception as e:
            logger.error(f"설정 값 가져오는 중 오류 발생: {e}")
            return default
    
    def register_service(self, service_type, **kwargs):
        """서비스 등록
        
        Args:
            service_type (str): 서비스 타입 (ec2, ecs, eks)
            **kwargs: 서비스 정보
            
        Returns:
            bool: 등록 성공 여부
        """
        try:
            if service_type == 'ec2':
                key = 'ec2_instances'
                # 필수 매개변수 검증
                if 'instance_id' not in kwargs or 'region' not in kwargs:
                    logger.error("EC2 서비스 등록 실패: 필수 매개변수 누락")
                    return False
                
                # 중복 서비스 검사
                for instance in self.services.get(key, []):
                    if instance['instance_id'] == kwargs['instance_id'] and instance['region'] == kwargs['region']:
                        logger.info(f"이미 등록된 EC2 인스턴스입니다: {kwargs['instance_id']}")
                        return True
                
                # 서비스 추가
                service_info = {
                    'instance_id': kwargs['instance_id'],
                    'region': kwargs['region'],
                    'description': kwargs.get('description', '')
                }
                
            elif service_type == 'ecs':
                key = 'ecs_services'
                # 필수 매개변수 검증
                if 'cluster_name' not in kwargs or 'service_name' not in kwargs or 'region' not in kwargs:
                    logger.error("ECS 서비스 등록 실패: 필수 매개변수 누락")
                    return False
                
                # 중복 서비스 검사
                for service in self.services.get(key, []):
                    if (service['cluster_name'] == kwargs['cluster_name'] and
                        service['service_name'] == kwargs['service_name'] and
                        service['region'] == kwargs['region']):
                        logger.info(f"이미 등록된 ECS 서비스입니다: {kwargs['cluster_name']}/{kwargs['service_name']}")
                        return True
                
                # 서비스 추가
                service_info = {
                    'cluster_name': kwargs['cluster_name'],
                    'service_name': kwargs['service_name'],
                    'region': kwargs['region'],
                    'description': kwargs.get('description', '')
                }
                
            elif service_type == 'eks':
                key = 'eks_nodegroups'
                # 필수 매개변수 검증
                if 'cluster_name' not in kwargs or 'nodegroup_name' not in kwargs or 'region' not in kwargs:
                    logger.error("EKS 노드그룹 등록 실패: 필수 매개변수 누락")
                    return False
                
                # 중복 서비스 검사
                for nodegroup in self.services.get(key, []):
                    if (nodegroup['cluster_name'] == kwargs['cluster_name'] and
                        nodegroup['nodegroup_name'] == kwargs['nodegroup_name'] and
                        nodegroup['region'] == kwargs['region']):
                        logger.info(f"이미 등록된 EKS 노드그룹입니다: {kwargs['cluster_name']}/{kwargs['nodegroup_name']}")
                        return True
                
                # 서비스 추가
                service_info = {
                    'cluster_name': kwargs['cluster_name'],
                    'nodegroup_name': kwargs['nodegroup_name'],
                    'region': kwargs['region'],
                    'desired_size': kwargs.get('desired_size', 1),
                    'description': kwargs.get('description', '')
                }
                
            else:
                logger.error(f"지원하지 않는 서비스 타입: {service_type}")
                return False
            
            # 서비스 목록에 추가
            if key not in self.services:
                self.services[key] = []
            
            self.services[key].append(service_info)
            
            # 서비스 파일 저장
            if self._save_services(self.services):
                logger.info(f"{service_type} 서비스가 등록되었습니다.")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"서비스 등록 중 오류 발생: {e}")
            return False
    
    def unregister_service(self, service_type, **kwargs):
        """서비스 등록 해제
        
        Args:
            service_type (str): 서비스 타입 (ec2, ecs, eks)
            **kwargs: 서비스 정보
            
        Returns:
            bool: 등록 해제 성공 여부
        """
        try:
            if service_type == 'ec2':
                key = 'ec2_instances'
                # 필수 매개변수 검증
                if 'instance_id' not in kwargs or 'region' not in kwargs:
                    logger.error("EC2 서비스 등록 해제 실패: 필수 매개변수 누락")
                    return False
                
                # 서비스 찾기
                for i, instance in enumerate(self.services.get(key, [])):
                    if instance['instance_id'] == kwargs['instance_id'] and instance['region'] == kwargs['region']:
                        self.services[key].pop(i)
                        logger.info(f"EC2 인스턴스 등록이 해제되었습니다: {kwargs['instance_id']}")
                        break
                else:
                    logger.warning(f"등록되지 않은 EC2 인스턴스입니다: {kwargs['instance_id']}")
                    return False
                
            elif service_type == 'ecs':
                key = 'ecs_services'
                # 필수 매개변수 검증
                if 'cluster_name' not in kwargs or 'service_name' not in kwargs or 'region' not in kwargs:
                    logger.error("ECS 서비스 등록 해제 실패: 필수 매개변수 누락")
                    return False
                
                # 서비스 찾기
                for i, service in enumerate(self.services.get(key, [])):
                    if (service['cluster_name'] == kwargs['cluster_name'] and
                        service['service_name'] == kwargs['service_name'] and
                        service['region'] == kwargs['region']):
                        self.services[key].pop(i)
                        logger.info(f"ECS 서비스 등록이 해제되었습니다: {kwargs['cluster_name']}/{kwargs['service_name']}")
                        break
                else:
                    logger.warning(f"등록되지 않은 ECS 서비스입니다: {kwargs['cluster_name']}/{kwargs['service_name']}")
                    return False
                
            elif service_type == 'eks':
                key = 'eks_nodegroups'
                # 필수 매개변수 검증
                if 'cluster_name' not in kwargs or 'nodegroup_name' not in kwargs or 'region' not in kwargs:
                    logger.error("EKS 노드그룹 등록 해제 실패: 필수 매개변수 누락")
                    return False
                
                # 서비스 찾기
                for i, nodegroup in enumerate(self.services.get(key, [])):
                    if (nodegroup['cluster_name'] == kwargs['cluster_name'] and
                        nodegroup['nodegroup_name'] == kwargs['nodegroup_name'] and
                        nodegroup['region'] == kwargs['region']):
                        self.services[key].pop(i)
                        logger.info(f"EKS 노드그룹 등록이 해제되었습니다: {kwargs['cluster_name']}/{kwargs['nodegroup_name']}")
                        break
                else:
                    logger.warning(f"등록되지 않은 EKS 노드그룹입니다: {kwargs['cluster_name']}/{kwargs['nodegroup_name']}")
                    return False
                
            else:
                logger.error(f"지원하지 않는 서비스 타입: {service_type}")
                return False
            
            # 서비스 파일 저장
            if self._save_services(self.services):
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"서비스 등록 해제 중 오류 발생: {e}")
            return False

# 전역 인스턴스
config_loader = ConfigLoader()
# config 이름으로 별칭 추가하여 activity_monitor.py에서 import할 수 있도록 함
config = config_loader