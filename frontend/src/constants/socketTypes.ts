/**
 * WebSocket 통신에 사용되는 타입 및 상수 정의
 */

// 명령 타입 정의 - 서버에 요청 가능한 명령들
export const CommandType = {
  // 기본 명령
  TEST: 'test',
  REFRESH_SERVICE: 'refresh_service',
  
  // 활동 모니터링 명령 - command_definitions.py 참조
  START_MONITORING: 'startMonitoring',
  
  // AWS 서비스 명령
  GET_ALL: 'getAll',
  GET_EC2_INSTANCES: 'getEC2Instances', 
  GET_ECS_CLUSTERS: 'getECSClusters',
  GET_EKS_CLUSTERS: 'getEKSClusters',
  
  // EC2 인스턴스 제어
  START_INSTANCE: 'startInstance',
  STOP_INSTANCE: 'stopInstance',
  
  // 기타 시스템 명령
  PING: 'PING',
  CLIENT_REQUEST: 'CLIENT_REQUEST'
} as const;

// 서비스 타입 정의
export const ServiceType = {
  EC2: 'ec2',
  ECS: 'ecs',
  EKS: 'eks', 
  ACTIVITY: 'activity',
  SYSTEM: 'system'
} as const;

// 메시지 타입 정의 - 서버로부터 받을 수 있는 메시지 타입
export const MessageType = {
  // AWS 서비스 관련
  AWS_EC2_LIST: 'AWS_EC2_LIST',
  AWS_ECS_LIST: 'AWS_ECS_LIST',
  AWS_EKS_LIST: 'AWS_EKS_LIST',
  AWS_SERVICE_STATUS: 'AWS_SERVICE_STATUS',
  
  // 활동 모니터링 관련 (서버 command_definitions.py 참조)
  KEYBOARD_ACTIVITY: 'KEYBOARD_ACTIVITY',
  MOUSE_MOVEMENT: 'MOUSE_MOVEMENT',
  MOUSE_CLICK: 'MOUSE_CLICK',
  SCREEN_CHANGE: 'SCREEN_CHANGE',
  ACTIVE_WINDOW: 'ACTIVE_WINDOW',
  AUDIO_PLAYBACK: 'AUDIO_PLAYBACK',
  USER_ACTIVITY: 'USER_ACTIVITY',
  SYSTEM_STATUS: 'SYSTEM_STATUS',
  
  // 타이머 관련
  TIMER_START: 'TIMER_START',
  TIMER_TICK: 'TIMER_TICK',
  TIMER_END: 'TIMER_END'
} as const;

// WebSocket 설정 상수
export const WS_CONFIG = {
  RECONNECT_INTERVAL: 2000,
  MAX_RECONNECT_ATTEMPTS: 10,
  CONNECTION_TIMEOUT: 5000,
  PING_INTERVAL: 30000,
  DEFAULT_REGION: 'ap-northeast-2'
};