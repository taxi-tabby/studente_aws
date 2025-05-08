import React, { useState, useCallback, useEffect, useRef } from 'react';
import type { WebSocketMessage } from '../types/aws';
import './WebSocketConsole.css';
import { useTranslation } from 'react-i18next';

interface WebSocketConsoleProps {
  messages: WebSocketMessage[];
  isConnected?: boolean;
  onClearMessages?: () => void; // 상위 컴포넌트의 메시지 클리어 함수
}

// 메시지 필터 옵션 타입 정의
type FilterOption = 'all' | 'test' | 'aws' | 'activity' | 'error';

// 메시지 인덱스 맵을 위한 타입 정의
interface MessageWithIndex extends WebSocketMessage {
  __index?: number; // 고유 인덱스 속성 추가
}

const WebSocketConsole: React.FC<WebSocketConsoleProps> = ({ 
  messages,
  isConnected = true,
  onClearMessages
}) => {
  const { t } = useTranslation();
  
  // 필터 상태 추가
  const [filter, setFilter] = useState<FilterOption>('all');
  
  // 현재 확장된 메시지의 인덱스를 저장하는 상태
  const [expandedMessageIndex, setExpandedMessageIndex] = useState<number | null>(null);
  
  // 메시지 인덱스 맵을 유지하기 위한 ref
  const messageIndexMapRef = useRef<Map<WebSocketMessage, number>>(new Map());
  const nextIndexRef = useRef<number>(0);
  
  // 메시지 요약 함수: 타입과 주요 내용을 기반으로 요약된 문자열 생성
  const summarizeMessage = useCallback((message: WebSocketMessage): string => {
    let summary = message.type || t('console.unknownType', 'Unknown');
    
    // 메시지 유형별 요약
    if (message.content) {
      if (message.type === 'USER_ACTIVITY') {
        summary += `: ${message.content.activity || t('console.activity', 'activity')}`;
        if (message.content.activity === 'TIMER_TICK') {
          summary += ` (${Math.floor((message.content.nowtime || 0) / 1000)}s)`;
        }
      } else if (message.content.instanceId) {
        summary += `: ${message.content.instanceId}`;
      } else if (message.content.region) {
        summary += `: ${message.content.region}`;
      } else if (message.type?.includes('AWS')) {
        summary += `: ${Object.keys(message.content).join(', ')}`;
      }
    } else if (message.service) {
      summary += `: ${message.service}`;
      if (message.status) summary += ` (${message.status})`;
    }
    
    return summary;
  }, [t]);
  
  // 메시지에 고유 인덱스를 할당
  const getMessageIndex = useCallback((message: WebSocketMessage): number => {
    if (!messageIndexMapRef.current.has(message)) {
      // 새 메시지에는 새 인덱스 할당
      messageIndexMapRef.current.set(message, nextIndexRef.current++);
    }
    return messageIndexMapRef.current.get(message) as number;
  }, []);
  
  // 메시지 필터링 함수
  const filterMessages = useCallback((msgs: WebSocketMessage[]): WebSocketMessage[] => {
    switch (filter) {
      case 'test':
        return msgs.filter(msg => 
          msg.type?.toLowerCase().includes('test') || 
          msg.content?.message?.toLowerCase().includes('test') ||
          msg.service?.toLowerCase().includes('test')
        );
      case 'aws':
        return msgs.filter(msg => 
          (msg.type && (
            msg.type.toLowerCase().includes('aws') || 
            msg.type.toLowerCase().includes('ec2') ||
            msg.type.toLowerCase().includes('ecs') ||
            msg.type.toLowerCase().includes('eks')
          )) ||
          msg.service === 'aws' || 
          msg.service === 'ec2' || 
          msg.service === 'ecs' || 
          msg.service === 'eks'
        );
      case 'activity':
        return msgs.filter(msg => 
          msg.type === 'USER_ACTIVITY' || 
          msg.service === 'activity' ||
          msg.content?.activity 
        );
      case 'error':
        return msgs.filter(msg => 
          msg.type?.toLowerCase().includes('error') || 
          msg.status === 'error' ||
          msg.content?.error
        );
      case 'all':
      default:
        return msgs;
    }
  }, [filter]);
  
  // 필터링된 메시지
  const filteredMessages = filterMessages(messages);
  
  // 최대 50개의 메시지만 표시하도록 제한 및 인덱스 할당
  const displayMessages: MessageWithIndex[] = filteredMessages.slice(-50).reverse().map(msg => {
    const indexedMsg = msg as MessageWithIndex;
    indexedMsg.__index = getMessageIndex(msg);
    return indexedMsg;
  });
  
  // 메시지 클릭 핸들러
  const handleMessageClick = (index: number) => {
    if (expandedMessageIndex === index) {
      setExpandedMessageIndex(null); // 이미 확장된 메시지면 접기
    } else {
      setExpandedMessageIndex(index); // 새로운 메시지 확장
    }
  };

  // 필터 변경 시 expanded 메시지 리셋
  useEffect(() => {
    setExpandedMessageIndex(null);
  }, [filter]);

  // 현재 선택된 메시지 찾기
  const selectedMessage = expandedMessageIndex !== null ? 
    displayMessages.find(message => message.__index === expandedMessageIndex) : 
    null;
    
  // 메시지의 에러 여부를 확인하는 함수
  const isErrorMessage = (message: WebSocketMessage): boolean => {
    return (
      (message.type && message.type.toLowerCase().includes('error')) ||
      message.status === 'error' ||
      (message.content && (
        message.content.error ||
        message.content.status === 'error' ||
        message.content.errorMessage
      ))
    );
  };
  
  // JSON 객체를 문자열화하는 함수 - 원본 구조 유지
  const formatJsonOutput = (obj: any): string => {
    // 빈 객체 혹은 undefined/null 객체 처리
    if (!obj || (typeof obj === 'object' && Object.keys(obj).length === 0)) {
      return '{}';
    }
    
    try {
      // 키 정렬 없이 원본 구조 그대로 들여쓰기만 적용하여 출력
      return JSON.stringify(obj, null, 2);
    } catch (error) {
      // 직렬화할 수 없는 객체의 경우 기본 문자열로 변환
      return String(obj);
    }
  };

  return (
    <div className={`websocket-console ${!isConnected ? 'disconnected' : ''}`}>
      {!isConnected && (
        <div className="connection-status-overlay">
          <div className="connection-status-message">
            <span className="connection-status-icon">⚠️</span>
            <span>{t('connection.cannotReceiveMessages')}</span>
          </div>
        </div>
      )}
      
      <div className="console-controls">
        <div className="filter-controls">
          <label htmlFor="message-filter">{t('console.filter')}: </label>
          <select 
            id="message-filter" 
            value={filter} 
            onChange={(e) => setFilter(e.target.value as FilterOption)}
            className="filter-dropdown"
          >
            <option value="all">{t('console.filterAll')}</option>
            <option value="test">{t('console.filterTest')}</option>
            <option value="aws">{t('console.filterAws')}</option>
            <option value="activity">{t('console.filterActivity')}</option>
            <option value="error">{t('console.filterError')}</option>
          </select>
        </div>
        <button 
          className="clear-button"
          onClick={onClearMessages}
        >
          {t('buttons.clearConsole')}
        </button>
      </div>
      
      <div className="console-split-view">
        <div className="message-list">
          {displayMessages.length === 0 ? (
            <div className="no-messages">{t('console.noMessages')}</div>
          ) : (
            displayMessages.map((message) => {
              const isError = isErrorMessage(message);
              return (
                <div 
                  key={`message-${message.__index}`}
                  className={`message-item ${expandedMessageIndex === message.__index ? 'selected' : ''} ${isError ? 'error-message' : ''}`}
                  onClick={() => handleMessageClick(message.__index!)}
                >
                  <div className="message-summary">
                    <div className="message-timestamp">
                      {message.timestamp ? 
                        new Date(typeof message.timestamp === 'number' ? 
                          message.timestamp * 1000 : 
                          message.timestamp
                        ).toLocaleTimeString() : 
                        <span className="no-timestamp">{t('console.noTimestamp')}</span>}
                    </div>
                    <div className="message-type-summary">
                      {summarizeMessage(message)}
                    </div>
                    {isError && <div className="message-error-icon">⚠️</div>}
                    <div className="expand-indicator">▼</div>
                  </div>
                </div>
              );
            })
          )}
        </div>
        
        <div className="message-detail-panel">
          {selectedMessage ? (
            <div className={`message-details ${isErrorMessage(selectedMessage) ? 'error-details' : ''}`}>
              {/* 헤더 정보 섹션 */}
              <div className="message-header">
                <div className="message-type-full">{selectedMessage.type || 'Unknown'}</div>
                <div className="message-timestamp-full">
                  {selectedMessage.timestamp ? 
                    new Date(typeof selectedMessage.timestamp === 'number' ? 
                      selectedMessage.timestamp * 1000 : 
                      selectedMessage.timestamp
                    ).toLocaleString() : 
                    t('console.noTimestamp')}
                </div>
                {selectedMessage.id && (
                  <div className="message-id">ID: {selectedMessage.id}</div>
                )}
                {selectedMessage.service && (
                  <div className="message-service">Service: {selectedMessage.service}</div>
                )}
                {selectedMessage.status && (
                  <div className={`message-status ${selectedMessage.status === 'error' ? 'error-status' : ''}`}>
                    Status: {selectedMessage.status}
                  </div>
                )}
              </div>
              
              {/* 전체 메시지 내용 표시 */}
              <div className="message-content-full">
                <div className="section-header">Full Message</div>
                <div className="message-content">
                  <pre>{formatJsonOutput(selectedMessage)}</pre>
                </div>
              </div>
              
              {/* 메시지 내용 별도 표시 */}
              {selectedMessage.content && (
                <div className="message-content-section">
                  <div className="section-header">Content</div>
                  <div className="message-content">
                    <pre>{formatJsonOutput(selectedMessage.content)}</pre>
                  </div>
                </div>
              )}
              
              {/* 데이터 별도 표시 */}
              {selectedMessage.data && (
                <div className="message-data-section">
                  <div className="section-header">Data</div>
                  <div className="message-content">
                    <pre>{formatJsonOutput(selectedMessage.data)}</pre>
                  </div>
                </div>
              )}
              
              {/* 최소 정보만 있는 메시지를 위한 기본 섹션 */}
              {!selectedMessage.content && !selectedMessage.data && !(
                isErrorMessage(selectedMessage) && 
                (selectedMessage.content?.error || selectedMessage.content?.errorMessage || selectedMessage.message)
              ) && (
                <div className="message-basic-section">
                  <div className="section-header">Message Information</div>
                  <div className="message-content">
                    <div className="basic-info-item">
                      <strong>Type:</strong> {selectedMessage.type || 'Unknown'}
                    </div>
                    {selectedMessage.service && (
                      <div className="basic-info-item">
                        <strong>Service:</strong> {selectedMessage.service}
                      </div>
                    )}
                    {selectedMessage.status && (
                      <div className="basic-info-item">
                        <strong>Status:</strong> {selectedMessage.status}
                      </div>
                    )}
                  </div>
                </div>
              )}
              
              {/* 에러 메시지 특별 표시 */}
              {isErrorMessage(selectedMessage) && (
                <div className="message-error-section">
                  <div className="section-header error-header">Error Details</div>
                  <div className="message-content error-content">
                    {selectedMessage.content?.error && (
                      <div className="error-item">
                        <strong>Error:</strong> {selectedMessage.content.error}
                      </div>
                    )}
                    {selectedMessage.content?.errorMessage && (
                      <div className="error-item">
                        <strong>Error Message:</strong> {selectedMessage.content.errorMessage}
                      </div>
                    )}
                    {selectedMessage.message && (
                      <div className="error-item">
                        <strong>Message:</strong> {selectedMessage.message}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="no-selection">
              <p>{t('console.selectMessagePrompt')}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default WebSocketConsole;