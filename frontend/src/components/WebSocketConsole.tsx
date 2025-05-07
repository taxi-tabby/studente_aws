import React, { useState } from 'react';
import type { WebSocketMessage } from '../types/aws';
import './WebSocketConsole.css';

interface WebSocketConsoleProps {
  messages: WebSocketMessage[];
  isConnected?: boolean;
}

// 메시지 요약 함수: 타입과 주요 내용을 기반으로 요약된 문자열 생성
const summarizeMessage = (message: WebSocketMessage): string => {
  let summary = message.type || 'Unknown';
  
  // 메시지 유형별 요약
  if (message.content) {
    if (message.type === 'USER_ACTIVITY') {
      summary += `: ${message.content.activity || '활동'}`;
      if (message.content.activity === 'TIMER_TICK') {
        summary += ` (${Math.floor((message.content.nowtime || 0) / 1000)}초)`;
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
};

const WebSocketConsole: React.FC<WebSocketConsoleProps> = ({ 
  messages,
  isConnected = true
}) => {
  // 최대 50개의 메시지만 표시하도록 제한
  const displayMessages = messages.slice(-50).reverse(); // 최근 메시지가 상단에 오도록 reverse
  
  // 현재 확장된 메시지의 인덱스를 저장하는 상태
  const [expandedMessageIndex, setExpandedMessageIndex] = useState<number | null>(null);
  
  // 메시지 클릭 핸들러
  const handleMessageClick = (index: number) => {
    if (expandedMessageIndex === index) {
      setExpandedMessageIndex(null); // 이미 확장된 메시지면 접기
    } else {
      setExpandedMessageIndex(index); // 새로운 메시지 확장
    }
  };

  return (
    <div className={`websocket-console ${!isConnected ? 'disconnected' : ''}`}>
      {!isConnected && (
        <div className="connection-status-overlay">
          <div className="connection-status-message">
            <span className="connection-status-icon">⚠️</span>
            <span>연결이 끊어져 있습니다. 메시지를 수신할 수 없습니다.</span>
          </div>
        </div>
      )}
      <div className="message-list">
        {displayMessages.length === 0 ? (
          <div className="no-messages">No messages received yet.</div>
        ) : (
          displayMessages.map((message, index) => (
            <div 
              key={index} 
              className={`message-item ${expandedMessageIndex === index ? 'expanded' : ''}`}
              onClick={() => handleMessageClick(index)}
            >
              <div className="message-summary">
                <div className="message-timestamp">
                  {message.timestamp ? 
                    new Date(typeof message.timestamp === 'number' ? 
                      message.timestamp * 1000 : 
                      message.timestamp
                    ).toLocaleTimeString() : 
                    'No timestamp'}
                </div>
                <div className="message-type-summary">
                  {summarizeMessage(message)}
                </div>
                <div className="message-expand-icon">
                  {expandedMessageIndex === index ? '▼' : '▶'}
                </div>
              </div>
              
              {expandedMessageIndex === index && (
                <div className="message-details">
                  <div className="message-type-full">{message.type || 'Unknown'}</div>
                  <div className="message-content">
                    {message.content ? (
                      <pre>{JSON.stringify(message.content, null, 2)}</pre>
                    ) : message.data ? (
                      <pre>{JSON.stringify(message.data, null, 2)}</pre>
                    ) : (
                      <pre>{JSON.stringify(message, null, 2)}</pre>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default WebSocketConsole;