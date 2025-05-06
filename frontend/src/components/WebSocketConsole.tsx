import React from 'react';
import './WebSocketConsole.css';

interface WebSocketMessage {
  id?: string;
  type?: string;
  timestamp?: number;
  source?: string;
  content?: any;
  [key: string]: any;
}

interface WebSocketConsoleProps {
  messages: WebSocketMessage[];
}

const WebSocketConsole: React.FC<WebSocketConsoleProps> = ({ messages }) => {
  // Format message as JSON string with indentation
  const formatMessage = (message: WebSocketMessage) => {
    return JSON.stringify(message, null, 2);
  };

  // Format timestamp to readable format
  const formatTimestamp = (timestamp?: number) => {
    if (!timestamp) return '';
    const date = new Date(timestamp * 1000);
    return date.toLocaleTimeString();
  };

  // 메시지 배열을 복사하고 역순으로 정렬 (최신 메시지가 맨 위에 오도록)
  const reversedMessages = [...messages].reverse();

  return (
    <div className="dashboard-section websocket-console-container">
      <h2>Console</h2>
      <div className="websocket-console">
        {reversedMessages.map((message, index) => (
          <div key={message.id || index} className="console-message">
            <div className="message-header">
              <span className="message-timestamp">[{formatTimestamp(message.timestamp) || 'No timestamp'}]</span>
              <span className="message-type">{message.type || 'Unknown'}</span>
              {message.source && <span className="message-source">from {message.source}</span>}
            </div>
            <pre className="message-content">{formatMessage(message)}</pre>
          </div>
        ))}
      </div>
    </div>
  );
};

export default WebSocketConsole;