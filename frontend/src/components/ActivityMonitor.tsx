import React from 'react';
import './ActivityMonitor.css';
import type { ActivityStatus } from '../types/aws';

interface ActivityMonitorProps {
  activityStatus: ActivityStatus;
  isConnected?: boolean; // 연결 상태를 받는 props 추가
}

const ActivityMonitor: React.FC<ActivityMonitorProps> = ({ 
  activityStatus, 
  isConnected = true // 기본값은 연결된 상태
}) => {
  // 연결이 끊어졌을 때 표시할 클래스 이름
  const disconnectedClass = !isConnected ? 'disconnected' : '';
  
  return (
    <div className={`activity-monitor ${disconnectedClass}`}>
      <h2>사용자 활동 모니터링 {!isConnected && <span className="connection-warning">(연결 끊김)</span>}</h2>
      <div className="activity-indicators">
        <div className={`activity-indicator ${activityStatus.keyboard ? 'active' : ''} ${!isConnected ? 'disabled' : ''}`}>
          <span className="indicator-label">키보드</span>
          <span className={`indicator-status ${activityStatus.keyboard ? 'active' : ''}`}></span>
        </div>
        <div className={`activity-indicator ${activityStatus.mouseMovement ? 'active' : ''} ${!isConnected ? 'disabled' : ''}`}>
          <span className="indicator-label">마우스 이동</span>
          <span className={`indicator-status ${activityStatus.mouseMovement ? 'active' : ''}`}></span>
        </div>
        <div className={`activity-indicator ${activityStatus.mouseClick ? 'active' : ''} ${!isConnected ? 'disabled' : ''}`}>
          <span className="indicator-label">마우스 클릭</span>
          <span className={`indicator-status ${activityStatus.mouseClick ? 'active' : ''}`}></span>
        </div>
        <div className={`activity-indicator ${activityStatus.screen ? 'active' : ''} ${!isConnected ? 'disabled' : ''}`}>
          <span className="indicator-label">화면 변화</span>
          <span className={`indicator-status ${activityStatus.screen ? 'active' : ''}`}></span>
        </div>
        <div className={`activity-indicator ${activityStatus.audio ? 'active' : ''} ${!isConnected ? 'disabled' : ''}`}>
          <span className="indicator-label">오디오</span>
          <span className={`indicator-status ${activityStatus.audio ? 'active' : ''}`}></span>
        </div>
      </div>
      {activityStatus.activeWindow && (
        <div className="active-window">
          <span className="window-label">활성 창:</span>
          <span className="window-name">{activityStatus.activeWindow}</span>
        </div>
      )}
    </div>
  );
};

export default ActivityMonitor;