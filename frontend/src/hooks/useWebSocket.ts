/**
 * WebSocket 서비스를 사용하기 위한 React Hook
 */
import { useEffect, useState, useRef, useCallback } from 'react';
import { WebSocketService } from '../services/WebSocketService';
import type { WebSocketMessage } from '../types/socket';
import { AwsApi } from '../api/AwsApi';
import { ActivityApi } from '../api/ActivityApi';

// WebSocket 서비스 연결 상태
export type ConnectionStatus = 'disconnected' | 'connecting' | 'connected';

// Hook 반환 타입
export interface UseWebSocketReturn {
  connectionStatus: ConnectionStatus;
  messages: WebSocketMessage[];
  clearMessages: () => void;
  reconnect: () => void;
  webSocketService: WebSocketService;
  awsApi: AwsApi;
  activityApi: ActivityApi;
}

/**
 * WebSocket 서비스를 사용하기 위한 커스텀 훅
 * 
 * @param port WebSocket 서버 포트
 * @param hostname WebSocket 서버 호스트 이름
 * @returns 연결 상태, 메시지 목록, 메시지 초기화 함수, 재연결 함수, API 객체들
 */
export const useWebSocket = (
  port: number,
  hostname: string = 'localhost'
): UseWebSocketReturn => {
  // 상태 관리
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('disconnected');
  const [messages, setMessages] = useState<WebSocketMessage[]>([]);
  
  // 서비스 객체 레퍼런스
  const webSocketServiceRef = useRef<WebSocketService | null>(null);
  const awsApiRef = useRef<AwsApi | null>(null);
  const activityApiRef = useRef<ActivityApi | null>(null);

  // 최대 메시지 수
  const MAX_MESSAGES = 500;
  
  // WebSocket 메시지 핸들러
  const handleMessage = useCallback((message: WebSocketMessage) => {
    setConnectionStatus('connected');
    
    // 메시지 목록에 추가
    setMessages(prevMessages => {
      // 새 메시지 추가 및 최대 개수 제한
      const updatedMessages = [...prevMessages, message];
      return updatedMessages.slice(Math.max(0, updatedMessages.length - MAX_MESSAGES));
    });
  }, []);
  
  // 메시지 목록 초기화
  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);
  
  // WebSocket 재연결
  const reconnect = useCallback(() => {
    if (webSocketServiceRef.current) {
      setConnectionStatus('connecting');
      webSocketServiceRef.current.connect();
    }
  }, []);

  // 컴포넌트 마운트 시 WebSocket 서비스 초기화 및 연결
  useEffect(() => {
    // WebSocket 서비스 생성
    if (!webSocketServiceRef.current) {
      webSocketServiceRef.current = new WebSocketService(port, handleMessage, hostname);
      
      // API 객체 생성
      if (webSocketServiceRef.current) {
        awsApiRef.current = new AwsApi(webSocketServiceRef.current);
        activityApiRef.current = new ActivityApi(webSocketServiceRef.current);
      }
      
      // 연결 끊김 콜백 설정
      webSocketServiceRef.current.setDisconnectCallback(() => {
        setConnectionStatus('disconnected');
      });
    }
    
    // 연결 시도
    setConnectionStatus('connecting');
    webSocketServiceRef.current.connect();
    
    // WebSocket 연결 상태 주기적 체크
    const connectionCheck = setInterval(() => {
      // 연결 상태 확인
      if (webSocketServiceRef.current?.getConnectionStatus()) {
        setConnectionStatus('connected');
        clearInterval(connectionCheck);
      }
    }, 1000);
    
    // 컴포넌트 언마운트 시 연결 해제 및 리소스 정리
    return () => {
      if (webSocketServiceRef.current) {
        webSocketServiceRef.current.disconnect();
      }
      clearInterval(connectionCheck);
    };
  }, [port, hostname, handleMessage]);
  
  // Hook 반환값
  return {
    connectionStatus,
    messages,
    clearMessages,
    reconnect,
    webSocketService: webSocketServiceRef.current!,
    awsApi: awsApiRef.current!,
    activityApi: activityApiRef.current!
  };
};