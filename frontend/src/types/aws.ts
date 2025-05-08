
// [{'id': 'i-0e493abf123ebf7c7', 'type': 't2.nano', 'state': 'stopped', 'name': '', 'public_ip': None, 'private_ip': '172.31.3.229', 'region': 'ap-northeast-2'}]
export interface EC2Instance {
  id: string;
  name: string;
  state: string;
  type: string;
  zone?: string;
  region: string;
  public_ip?: string;
  private_ip?: string;
}


export interface ECSCluster {
  name: string;
  status: string;
  serviceCount: number;
  taskCount: number;
  region: string;
}

export interface EKSCluster {
  name: string;
  status: string;
  version: string;
  nodeCount: number;
  region: string;
}

export interface ActivityStatus {
  keyboard: boolean;
  mouseMovement: boolean;
  mouseClick: boolean;
  screen: boolean;
  audio: boolean;
  activeWindow: string;
}

// WebSocket 메시지를 위한 포괄적인 인터페이스 정의
export interface WebSocketMessage {
  // 기본 메시지 식별자 필드
  type?: string;
  service?: string;
  status?: string;
  message?: string;
  
  // 데이터 필드 - 여러 형태의 데이터가 올 수 있음
  data?: any;
  content?: any;
  
  // 서비스별 응답 필드
  instances?: EC2Instance[];
  clusters?: ECSCluster[] | EKSCluster[];
  
  // 액션 관련 필드
  action?: string;
  region?: string;
  
  // 기타 임의 필드 허용 (인덱스 시그니처)
  [key: string]: any;
}