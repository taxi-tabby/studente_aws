"""
AWS 서비스 자동 관리 모듈
"""
import os
import threading
import time
import yaml
import logging
from datetime import datetime, timedelta
from core.config.config_loader import config
from core.aws_auth import aws_auth
from core.aws_services import (
    start_ec2_instance, 
    stop_ec2_instance,
    start_ecs_service,
    stop_ecs_service,
    scale_eks_nodegroup
)

# 로거 설정
logger = logging.getLogger(__name__)

# 서비스 목록 파일 경로
SERVICE_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "services.yaml")

class ServiceManager:
    """AWS 서비스 자동 관리 클래스"""
    _instance = None
    _services = {
        "ec2_instances": [],
        "ecs_services": [],
        "eks_nodegroups": []
    }
    _last_activity_time = datetime.now()
    _user_away = False
    _thread = None
    _running = False
    
    def __new__(cls):
        """싱글톤 패턴 구현"""
        if cls._instance is None:
            cls._instance = super(ServiceManager, cls).__new__(cls)
        return cls._instance
    
    def start(self):
        """서비스 관리자 시작"""
        if self._running:
            return False
        
        # 서비스 목록 로드
        self._load_services()
        
        # 서비스 관리 스레드 시작
        self._running = True
        self._thread = threading.Thread(target=self._service_check_loop, daemon=True)
        self._thread.start()
        
        logger.info("서비스 관리자가 시작되었습니다.")
        return True
    
    def _load_services(self):
        """서비스 목록을 YAML 파일에서 로드"""
        try:
            if not os.path.exists(SERVICE_FILE_PATH):
                # 파일이 없으면 빈 서비스 목록으로 초기화
                self._save_services()
                return
                
            with open(SERVICE_FILE_PATH, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                
            # None 타입 체크 및 기본값 설정
            if not data:
                data = {}
                
            self._services = {
                "ec2_instances": data.get("ec2_instances", []) or [],
                "ecs_services": data.get("ecs_services", []) or [],
                "eks_nodegroups": data.get("eks_nodegroups", []) or []
            }
            
            logger.info(f"서비스 목록을 로드했습니다: EC2 {len(self._services['ec2_instances'])}개, "
                       f"ECS {len(self._services['ecs_services'])}개, "
                       f"EKS {len(self._services['eks_nodegroups'])}개")
                
        except Exception as e:
            logger.error(f"서비스 목록 로드 중 오류 발생: {e}")
            self._services = {
                "ec2_instances": [],
                "ecs_services": [],
                "eks_nodegroups": []
            }
    
    def _save_services(self):
        """서비스 목록을 YAML 파일로 저장"""
        try:
            with open(SERVICE_FILE_PATH, "w", encoding="utf-8") as f:
                yaml.dump(self._services, f, default_flow_style=False, allow_unicode=True)
                
            logger.info("서비스 목록을 파일에 저장했습니다.")
            return True
        except Exception as e:
            logger.error(f"서비스 목록 저장 중 오류 발생: {e}")
            return False
    
    def _service_check_loop(self):
        """서비스 상태 확인 및 관리 루프"""
        inactivity_timeout = config.get("activity_monitor", "inactivity_timeout_minutes", 30)
        check_interval = config.get("aws", "service_state_check_interval_minutes", 5)
        
        while self._running:
            try:
                # 사용자가 자리에 없는지 확인
                idle_time = datetime.now() - self._last_activity_time
                idle_minutes = idle_time.total_seconds() / 60
                
                # 상태 변경 확인
                if idle_minutes >= inactivity_timeout and not self._user_away:
                    # 사용자가 부재중 상태로 변경
                    logger.info(f"사용자가 {int(idle_minutes)}분 동안 활동이 없어 부재중 상태로 전환합니다.")
                    self._user_away = True
                    self._stop_all_services()
                    
                elif idle_minutes < inactivity_timeout and self._user_away:
                    # 사용자가 돌아옴 상태로 변경
                    logger.info("사용자 활동이 감지되어 서비스를 시작합니다.")
                    self._user_away = False
                    self._start_all_services()
                    
                # 체크 간격 대기
                time.sleep(check_interval * 60)
                
            except Exception as e:
                logger.error(f"서비스 체크 루프에서 오류 발생: {e}")
                time.sleep(60)  # 오류 발생 시 1분 대기
    
    def _stop_all_services(self):
        """모든 등록된 서비스 중지"""
        if not aws_auth.is_authenticated():
            logger.error("AWS 인증이 되어있지 않아 서비스를 중지할 수 없습니다.")
            return
        
        try:
            # EC2 인스턴스 중지
            for instance in self._services["ec2_instances"]:
                instance_id = instance.get("instance_id")
                region = instance.get("region")
                description = instance.get("description", "")
                
                if instance_id and region:
                    try:
                        logger.info(f"EC2 인스턴스 중지 중: {instance_id} ({description})")
                        stop_ec2_instance(instance_id, region)
                    except Exception as e:
                        logger.error(f"EC2 인스턴스 {instance_id} 중지 중 오류: {e}")
            
            # ECS 서비스 중지
            for service in self._services["ecs_services"]:
                cluster_name = service.get("cluster_name")
                service_name = service.get("service_name")
                region = service.get("region")
                description = service.get("description", "")
                
                if cluster_name and service_name and region:
                    try:
                        logger.info(f"ECS 서비스 중지 중: {service_name} ({description})")
                        stop_ecs_service(cluster_name, service_name, region)
                    except Exception as e:
                        logger.error(f"ECS 서비스 {service_name} 중지 중 오류: {e}")
            
            # EKS 노드그룹 스케일 다운
            for nodegroup in self._services["eks_nodegroups"]:
                cluster_name = nodegroup.get("cluster_name")
                nodegroup_name = nodegroup.get("nodegroup_name")
                region = nodegroup.get("region")
                description = nodegroup.get("description", "")
                
                if cluster_name and nodegroup_name and region:
                    try:
                        logger.info(f"EKS 노드그룹 중지 중: {nodegroup_name} ({description})")
                        scale_eks_nodegroup(cluster_name, nodegroup_name, region, 0)
                    except Exception as e:
                        logger.error(f"EKS 노드그룹 {nodegroup_name} 중지 중 오류: {e}")
            
            logger.info("모든 서비스 중지 작업이 완료되었습니다.")
            
        except Exception as e:
            logger.error(f"서비스 중지 중 오류 발생: {e}")
    
    def _start_all_services(self):
        """모든 등록된 서비스 시작"""
        if not aws_auth.is_authenticated():
            logger.error("AWS 인증이 되어있지 않아 서비스를 시작할 수 없습니다.")
            return
        
        try:
            # EC2 인스턴스 시작
            for instance in self._services["ec2_instances"]:
                instance_id = instance.get("instance_id")
                region = instance.get("region")
                description = instance.get("description", "")
                
                if instance_id and region:
                    try:
                        logger.info(f"EC2 인스턴스 시작 중: {instance_id} ({description})")
                        start_ec2_instance(instance_id, region)
                    except Exception as e:
                        logger.error(f"EC2 인스턴스 {instance_id} 시작 중 오류: {e}")
            
            # ECS 서비스 시작
            for service in self._services["ecs_services"]:
                cluster_name = service.get("cluster_name")
                service_name = service.get("service_name")
                region = service.get("region")
                description = service.get("description", "")
                
                if cluster_name and service_name and region:
                    try:
                        logger.info(f"ECS 서비스 시작 중: {service_name} ({description})")
                        start_ecs_service(cluster_name, service_name, region)
                    except Exception as e:
                        logger.error(f"ECS 서비스 {service_name} 시작 중 오류: {e}")
            
            # EKS 노드그룹 스케일 업
            for nodegroup in self._services["eks_nodegroups"]:
                cluster_name = nodegroup.get("cluster_name")
                nodegroup_name = nodegroup.get("nodegroup_name")
                region = nodegroup.get("region")
                desired_size = nodegroup.get("desired_size", 1)
                description = nodegroup.get("description", "")
                
                if cluster_name and nodegroup_name and region:
                    try:
                        logger.info(f"EKS 노드그룹 시작 중: {nodegroup_name} ({description})")
                        scale_eks_nodegroup(cluster_name, nodegroup_name, region, desired_size)
                    except Exception as e:
                        logger.error(f"EKS 노드그룹 {nodegroup_name} 시작 중 오류: {e}")
            
            logger.info("모든 서비스 시작 작업이 완료되었습니다.")
            
        except Exception as e:
            logger.error(f"서비스 시작 중 오류 발생: {e}")
    
    def update_activity_time(self):
        """사용자 활동 시간 업데이트"""
        self._last_activity_time = datetime.now()
    
    def register_ec2_instance(self, instance_id, region, description=""):
        """EC2 인스턴스 등록"""
        for instance in self._services["ec2_instances"]:
            if instance.get("instance_id") == instance_id and instance.get("region") == region:
                logger.info(f"이미 등록된 EC2 인스턴스입니다: {instance_id}")
                return False
                
        self._services["ec2_instances"].append({
            "instance_id": instance_id,
            "region": region,
            "description": description
        })
        
        self._save_services()
        logger.info(f"EC2 인스턴스가 등록되었습니다: {instance_id}")
        return True
    
    def unregister_ec2_instance(self, instance_id, region):
        """EC2 인스턴스 등록 해제"""
        for i, instance in enumerate(self._services["ec2_instances"]):
            if instance.get("instance_id") == instance_id and instance.get("region") == region:
                self._services["ec2_instances"].pop(i)
                self._save_services()
                logger.info(f"EC2 인스턴스가 등록 해제되었습니다: {instance_id}")
                return True
                
        logger.warning(f"등록되지 않은 EC2 인스턴스입니다: {instance_id}")
        return False
    
    def register_ecs_service(self, cluster_name, service_name, region, description=""):
        """ECS 서비스 등록"""
        for service in self._services["ecs_services"]:
            if (service.get("cluster_name") == cluster_name and 
                service.get("service_name") == service_name and 
                service.get("region") == region):
                logger.info(f"이미 등록된 ECS 서비스입니다: {service_name}")
                return False
                
        self._services["ecs_services"].append({
            "cluster_name": cluster_name,
            "service_name": service_name,
            "region": region,
            "description": description
        })
        
        self._save_services()
        logger.info(f"ECS 서비스가 등록되었습니다: {service_name}")
        return True
    
    def unregister_ecs_service(self, cluster_name, service_name, region):
        """ECS 서비스 등록 해제"""
        for i, service in enumerate(self._services["ecs_services"]):
            if (service.get("cluster_name") == cluster_name and 
                service.get("service_name") == service_name and 
                service.get("region") == region):
                self._services["ecs_services"].pop(i)
                self._save_services()
                logger.info(f"ECS 서비스가 등록 해제되었습니다: {service_name}")
                return True
                
        logger.warning(f"등록되지 않은 ECS 서비스입니다: {service_name}")
        return False
    
    def register_eks_nodegroup(self, cluster_name, nodegroup_name, region, desired_size=1, description=""):
        """EKS 노드그룹 등록"""
        for nodegroup in self._services["eks_nodegroups"]:
            if (nodegroup.get("cluster_name") == cluster_name and 
                nodegroup.get("nodegroup_name") == nodegroup_name and 
                nodegroup.get("region") == region):
                logger.info(f"이미 등록된 EKS 노드그룹입니다: {nodegroup_name}")
                return False
                
        self._services["eks_nodegroups"].append({
            "cluster_name": cluster_name,
            "nodegroup_name": nodegroup_name,
            "region": region,
            "desired_size": desired_size,
            "description": description
        })
        
        self._save_services()
        logger.info(f"EKS 노드그룹이 등록되었습니다: {nodegroup_name}")
        return True
    
    def unregister_eks_nodegroup(self, cluster_name, nodegroup_name, region):
        """EKS 노드그룹 등록 해제"""
        for i, nodegroup in enumerate(self._services["eks_nodegroups"]):
            if (nodegroup.get("cluster_name") == cluster_name and 
                nodegroup.get("nodegroup_name") == nodegroup_name and 
                nodegroup.get("region") == region):
                self._services["eks_nodegroups"].pop(i)
                self._save_services()
                logger.info(f"EKS 노드그룹이 등록 해제되었습니다: {nodegroup_name}")
                return True
                
        logger.warning(f"등록되지 않은 EKS 노드그룹입니다: {nodegroup_name}")
        return False
    
    def get_registered_services(self):
        """등록된 모든 서비스 조회"""
        return self._services
    
    def is_user_away(self):
        """사용자 부재 상태 확인"""
        return self._user_away

# 전역 인스턴스
service_manager = ServiceManager()