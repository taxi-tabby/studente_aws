/**
 * WebSocket 통신에 사용되는 타입 및 상수 정의
 */

// 명령 타입 정의 - 서버에 요청 가능한 명령들
export const CommandType = {
  // 기본 명령
  TEST: 'test',
  REFRESH_SERVICE: 'refresh_service',
  PASSWORD_VERIFY: 'verify_password',
  
  // 활동 모니터링 명령 - command_definitions.py 참조
} as const;

// 서비스 타입 정의
export const ServiceType = {
  EC2: 'ec2',
  ECS: 'ecs',
  EKS: 'eks', 
} as const;

// 메시지 타입 정의 - 서버로부터 받을 수 있는 메시지 타입
export const MessageType = {
  // AWS 서비스 관련
} as const;

// WebSocket 설정 상수
export const WS_CONFIG = {
  RECONNECT_INTERVAL: 2000,
  MAX_RECONNECT_ATTEMPTS: 10,
  CONNECTION_TIMEOUT: 5000,
  PING_INTERVAL: 30000
};