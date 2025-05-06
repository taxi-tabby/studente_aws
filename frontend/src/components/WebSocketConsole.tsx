import React, { useRef, useEffect } from 'react';
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
  const consoleEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (consoleEndRef.current) {
      consoleEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

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

  return (
    <div className="dashboard-section websocket-console-container">
      <h2>WebSocket Console</h2>
      <div className="websocket-console">
        {messages.map((message, index) => (
          <div key={message.id || index} className="console-message">
            <div className="message-header">
              <span className="message-timestamp">[{formatTimestamp(message.timestamp) || 'No timestamp'}]</span>
              <span className="message-type">{message.type || 'Unknown'}</span>
              {message.source && <span className="message-source">from {message.source}</span>}
            </div>
            <pre className="message-content">{formatMessage(message)}</pre>
          </div>
        ))}
        <div ref={consoleEndRef} />
      </div>
    </div>
  );
};

export default WebSocketConsole;