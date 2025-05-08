"""
AWS 서비스 관리 모듈
"""
import logging
import boto3
from botocore.exceptions import ClientError
from core.aws_auth import aws_auth
from core.config.config_loader import config

# 로거 설정
logger = logging.getLogger(__name__)

# 기본 AWS 리전 설정
aws_regions = config.settings.get("aws", {}).get("regions", ["ap-northeast-2"])
DEFAULT_REGION = aws_regions[0] if aws_regions else "ap-northeast-2"
logger.info(f"AWS 기본 리전: {DEFAULT_REGION}")

def _get_ec2_client(region):
    """EC2 클라이언트를 생성합니다.
    
    Args:
        region: AWS 리전
        
    Returns:
        boto3.client: EC2 클라이언트
    """
    session = aws_auth.get_session(region_name=region)
    if session:
        return session.client('ec2')
    return None

def _get_ecs_client(region):
    """ECS 클라이언트를 생성합니다.
    
    Args:
        region: AWS 리전
        
    Returns:
        boto3.client: ECS 클라이언트
    """
    session = aws_auth.get_session(region_name=region)
    if session:
        return session.client('ecs')
    return None

def _get_eks_client(region):
    """EKS 클라이언트를 생성합니다.
    
    Args:
        region: AWS 리전
        
    Returns:
        boto3.client: EKS 클라이언트
    """
    session = aws_auth.get_session(region_name=region)
    if session:
        return session.client('eks')
    return None

def list_ec2_instances(region=None):
    """EC2 인스턴스 목록을 조회합니다.
    
    Args:
        region: AWS 리전 (None인 경우 모든 리전 조회)
        
    Returns:
        list: EC2 인스턴스 목록
    """
    instances = []
    
    # 모든 리전을 조회하는 경우
    regions_to_check = [region] if region else aws_regions
    logger.info(f"----------------------- EC2 인스턴스 조회 리전: {regions_to_check}")
    
    for current_region in regions_to_check:
        client = _get_ec2_client(current_region)
        if not client:
            logger.error(f"--------------------- AWS 인증 정보가 없습니다. 리전: {current_region}")
            continue
        
        try:
            response = client.describe_instances()
            
            for reservation in response.get('Reservations', []):
                for instance in reservation.get('Instances', []):
                    # 인스턴스 이름 찾기
                    name = ""
                    for tag in instance.get('Tags', []):
                        if tag['Key'] == 'Name':
                            name = tag['Value']
                            break
                    
                    instances.append({
                        'id': instance.get('InstanceId'),
                        'type': instance.get('InstanceType'),
                        'state': instance.get('State', {}).get('Name'),
                        'name': name,
                        'public_ip': instance.get('PublicIpAddress'),
                        'private_ip': instance.get('PrivateIpAddress'),
                        'region': current_region  # 리전 정보 추가
                    })
            
        except ClientError as e:
            logger.error(f"EC2 인스턴스 목록 조회 중 오류 발생 (리전: {current_region}): {e}")
    
    print("------------------------------------ EC2 인스턴스 목록:", instances)
    
    return instances

def start_ec2_instance(instance_id, region):
    """EC2 인스턴스를 시작합니다.
    
    Args:
        instance_id: EC2 인스턴스 ID
        region: AWS 리전
        
    Returns:
        bool: 성공 여부
    """
    client = _get_ec2_client(region)
    if not client:
        logger.error("AWS 인증 정보가 없습니다.")
        return False
    
    try:
        response = client.describe_instances(InstanceIds=[instance_id])
        # 인스턴스가 이미 실행 중인지 확인
        for reservation in response.get('Reservations', []):
            for instance in reservation.get('Instances', []):
                state = instance.get('State', {}).get('Name')
                if state == 'running':
                    logger.info(f"인스턴스 {instance_id}가 이미 실행 중입니다.")
                    return True
        
        # 인스턴스 시작
        client.start_instances(InstanceIds=[instance_id])
        logger.info(f"인스턴스 {instance_id}가 시작되었습니다.")
        return True
        
    except ClientError as e:
        logger.error(f"EC2 인스턴스 시작 중 오류 발생: {e}")
        return False

def stop_ec2_instance(instance_id, region):
    """EC2 인스턴스를 중지합니다.
    
    Args:
        instance_id: EC2 인스턴스 ID
        region: AWS 리전
        
    Returns:
        bool: 성공 여부
    """
    client = _get_ec2_client(region)
    if not client:
        logger.error("AWS 인증 정보가 없습니다.")
        return False
    
    try:
        response = client.describe_instances(InstanceIds=[instance_id])
        # 인스턴스가 이미 중지 상태인지 확인
        for reservation in response.get('Reservations', []):
            for instance in reservation.get('Instances', []):
                state = instance.get('State', {}).get('Name')
                if state in ('stopped', 'stopping'):
                    logger.info(f"인스턴스 {instance_id}가 이미 중지되었거나 중지 중입니다.")
                    return True
        
        # 인스턴스 중지
        client.stop_instances(InstanceIds=[instance_id])
        logger.info(f"인스턴스 {instance_id}가 중지되었습니다.")
        return True
        
    except ClientError as e:
        logger.error(f"EC2 인스턴스 중지 중 오류 발생: {e}")
        return False

def list_ecs_clusters(region):
    """ECS 클러스터 목록을 조회합니다.
    
    Args:
        region: AWS 리전
        
    Returns:
        list: ECS 클러스터 목록
    """
    client = _get_ecs_client(region)
    if not client:
        logger.error("AWS 인증 정보가 없습니다.")
        return []
    
    try:
        response = client.list_clusters()
        cluster_arns = response.get('clusterArns', [])
        
        if not cluster_arns:
            return []
            
        # 클러스터 정보 조회
        response = client.describe_clusters(clusters=cluster_arns)
        clusters = []
        
        for cluster in response.get('clusters', []):
            clusters.append({
                'name': cluster.get('clusterName'),
                'status': cluster.get('status'),
                'running_tasks_count': cluster.get('runningTasksCount'),
                'pending_tasks_count': cluster.get('pendingTasksCount'),
                'active_services_count': cluster.get('activeServicesCount')
            })
        
        return clusters
        
    except ClientError as e:
        logger.error(f"ECS 클러스터 목록 조회 중 오류 발생: {e}")
        return []

def list_ecs_services(cluster_name, region):
    """ECS 서비스 목록을 조회합니다.
    
    Args:
        cluster_name: ECS 클러스터 이름
        region: AWS 리전
        
    Returns:
        list: ECS 서비스 목록
    """
    client = _get_ecs_client(region)
    if not client:
        logger.error("AWS 인증 정보가 없습니다.")
        return []
    
    try:
        response = client.list_services(cluster=cluster_name)
        service_arns = response.get('serviceArns', [])
        
        if not service_arns:
            return []
            
        # 서비스 정보 조회
        response = client.describe_services(cluster=cluster_name, services=service_arns)
        services = []
        
        for service in response.get('services', []):
            services.append({
                'name': service.get('serviceName'),
                'status': service.get('status'),
                'desired_count': service.get('desiredCount'),
                'running_count': service.get('runningCount'),
                'pending_count': service.get('pendingCount')
            })
        
        return services
        
    except ClientError as e:
        logger.error(f"ECS 서비스 목록 조회 중 오류 발생: {e}")
        return []

def start_ecs_service(cluster_name, service_name, region):
    """ECS 서비스를 시작합니다.
    
    Args:
        cluster_name: ECS 클러스터 이름
        service_name: ECS 서비스 이름
        region: AWS 리전
        
    Returns:
        bool: 성공 여부
    """
    client = _get_ecs_client(region)
    if not client:
        logger.error("AWS 인증 정보가 없습니다.")
        return False
    
    try:
        # 서비스 현재 상태 확인
        response = client.describe_services(
            cluster=cluster_name,
            services=[service_name]
        )
        
        if not response.get('services'):
            logger.error(f"서비스 {service_name}를 찾을 수 없습니다.")
            return False
            
        service = response['services'][0]
        desired_count = service.get('desiredCount', 0)
        
        # 이미 실행 중인 경우
        if desired_count > 0:
            logger.info(f"서비스 {service_name}가 이미 실행 중입니다.")
            return True
            
        # 서비스 시작 (desired_count를 1로 설정)
        client.update_service(
            cluster=cluster_name,
            service=service_name,
            desiredCount=1
        )
        
        logger.info(f"서비스 {service_name}가 시작되었습니다.")
        return True
        
    except ClientError as e:
        logger.error(f"ECS 서비스 시작 중 오류 발생: {e}")
        return False

def stop_ecs_service(cluster_name, service_name, region):
    """ECS 서비스를 중지합니다.
    
    Args:
        cluster_name: ECS 클러스터 이름
        service_name: ECS 서비스 이름
        region: AWS 리전
        
    Returns:
        bool: 성공 여부
    """
    client = _get_ecs_client(region)
    if not client:
        logger.error("AWS 인증 정보가 없습니다.")
        return False
    
    try:
        # 서비스 현재 상태 확인
        response = client.describe_services(
            cluster=cluster_name,
            services=[service_name]
        )
        
        if not response.get('services'):
            logger.error(f"서비스 {service_name}를 찾을 수 없습니다.")
            return False
            
        service = response['services'][0]
        desired_count = service.get('desiredCount', 0)
        
        # 이미 중지된 경우
        if desired_count == 0:
            logger.info(f"서비스 {service_name}가 이미 중지되었습니다.")
            return True
            
        # 서비스 중지 (desired_count를 0으로 설정)
        client.update_service(
            cluster=cluster_name,
            service=service_name,
            desiredCount=0
        )
        
        logger.info(f"서비스 {service_name}가 중지되었습니다.")
        return True
        
    except ClientError as e:
        logger.error(f"ECS 서비스 중지 중 오류 발생: {e}")
        return False

def list_eks_clusters(region):
    """EKS 클러스터 목록을 조회합니다.
    
    Args:
        region: AWS 리전
        
    Returns:
        list: EKS 클러스터 목록
    """
    client = _get_eks_client(region)
    if not client:
        logger.error("AWS 인증 정보가 없습니다.")
        return []
    
    try:
        response = client.list_clusters()
        cluster_names = response.get('clusters', [])
        
        if not cluster_names:
            return []
            
        # 클러스터 정보 조회
        clusters = []
        for cluster_name in cluster_names:
            cluster_info = client.describe_cluster(name=cluster_name)
            cluster = cluster_info.get('cluster', {})
            
            clusters.append({
                'name': cluster.get('name'),
                'status': cluster.get('status'),
                'version': cluster.get('version'),
                'endpoint': cluster.get('endpoint'),
                'created_at': cluster.get('createdAt')
            })
        
        return clusters
        
    except ClientError as e:
        logger.error(f"EKS 클러스터 목록 조회 중 오류 발생: {e}")
        return []

def list_eks_nodegroups(cluster_name, region):
    """EKS 노드그룹 목록을 조회합니다.
    
    Args:
        cluster_name: EKS 클러스터 이름
        region: AWS 리전
        
    Returns:
        list: EKS 노드그룹 목록
    """
    client = _get_eks_client(region)
    if not client:
        logger.error("AWS 인증 정보가 없습니다.")
        return []
    
    try:
        response = client.list_nodegroups(clusterName=cluster_name)
        nodegroup_names = response.get('nodegroups', [])
        
        if not nodegroup_names:
            return []
            
        # 노드그룹 정보 조회
        nodegroups = []
        for nodegroup_name in nodegroup_names:
            nodegroup_info = client.describe_nodegroup(
                clusterName=cluster_name,
                nodegroupName=nodegroup_name
            )
            nodegroup = nodegroup_info.get('nodegroup', {})
            
            nodegroups.append({
                'name': nodegroup.get('nodegroupName'),
                'status': nodegroup.get('status'),
                'instance_type': nodegroup.get('instanceTypes', [])[0] if nodegroup.get('instanceTypes') else None,
                'desired_size': nodegroup.get('scalingConfig', {}).get('desiredSize'),
                'min_size': nodegroup.get('scalingConfig', {}).get('minSize'),
                'max_size': nodegroup.get('scalingConfig', {}).get('maxSize')
            })
        
        return nodegroups
        
    except ClientError as e:
        logger.error(f"EKS 노드그룹 목록 조회 중 오류 발생: {e}")
        return []

def scale_eks_nodegroup(cluster_name, nodegroup_name, region, desired_size):
    """EKS 노드그룹을 스케일링합니다.
    
    Args:
        cluster_name: EKS 클러스터 이름
        nodegroup_name: EKS 노드그룹 이름
        region: AWS 리전
        desired_size: 원하는 노드 수
        
    Returns:
        bool: 성공 여부
    """
    client = _get_eks_client(region)
    if not client:
        logger.error("AWS 인증 정보가 없습니다.")
        return False
    
    try:
        # 노드그룹 현재 상태 확인
        response = client.describe_nodegroup(
            clusterName=cluster_name,
            nodegroupName=nodegroup_name
        )
        
        if not response.get('nodegroup'):
            logger.error(f"노드그룹 {nodegroup_name}을 찾을 수 없습니다.")
            return False
            
        nodegroup = response['nodegroup']
        current_desired = nodegroup.get('scalingConfig', {}).get('desiredSize')
        min_size = nodegroup.get('scalingConfig', {}).get('minSize')
        max_size = nodegroup.get('scalingConfig', {}).get('maxSize')
        
        # 이미 원하는 크기인 경우
        if current_desired == desired_size:
            logger.info(f"노드그룹 {nodegroup_name}가 이미 원하는 크기({desired_size})입니다.")
            return True
            
        # 스케일링 제한 확인
        if desired_size < min_size:
            logger.warning(f"원하는 크기({desired_size})가 최소 크기({min_size})보다 작습니다. 최소 크기로 설정됩니다.")
            desired_size = min_size
        
        if desired_size > max_size:
            logger.warning(f"원하는 크기({desired_size})가 최대 크기({max_size})보다 큽니다. 최대 크기로 설정됩니다.")
            desired_size = max_size
            
        # 노드그룹 스케일링
        client.update_nodegroup_config(
            clusterName=cluster_name,
            nodegroupName=nodegroup_name,
            scalingConfig={
                'desiredSize': desired_size,
                'minSize': min_size,
                'maxSize': max_size
            }
        )
        
        action = "시작" if desired_size > 0 else "중지"
        logger.info(f"노드그룹 {nodegroup_name}가 {action}되었습니다. (크기: {desired_size})")
        return True
        
    except ClientError as e:
        logger.error(f"EKS 노드그룹 스케일링 중 오류 발생: {e}")
        return False