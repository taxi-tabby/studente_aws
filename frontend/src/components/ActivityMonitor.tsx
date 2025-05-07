import React from 'react';
import './ActivityMonitor.css';
import type { ActivityStatus } from '../types/aws';
import { useTranslation } from 'react-i18next';

interface ActivityMonitorProps {
  activityStatus: ActivityStatus;
  isConnected?: boolean; // 연결 상태를 받는 props 추가
}

const ActivityMonitor: React.FC<ActivityMonitorProps> = ({ 
  activityStatus, 
  isConnected = true // 기본값은 연결된 상태
}) => {
  const { t } = useTranslation();
  
  // 연결이 끊어졌을 때 표시할 클래스 이름
  const disconnectedClass = !isConnected ? 'disconnected' : '';
  
  return (
    <div className={`activity-monitor ${disconnectedClass}`}>
      <h2>{t('activity.title')} {!isConnected && <span className="connection-warning">({t('connection.connectionLost')})</span>}</h2>
      <div className="activity-indicators">
        <div className={`activity-indicator ${activityStatus.keyboard ? 'active' : ''} ${!isConnected ? 'disabled' : ''}`}>
          <span className="indicator-label">{t('activity.keyboard')}</span>
          <span className={`indicator-status ${activityStatus.keyboard ? 'active' : ''}`}></span>
        </div>
        <div className={`activity-indicator ${activityStatus.mouseMovement ? 'active' : ''} ${!isConnected ? 'disabled' : ''}`}>
          <span className="indicator-label">{t('activity.mouseMovement')}</span>
          <span className={`indicator-status ${activityStatus.mouseMovement ? 'active' : ''}`}></span>
        </div>
        <div className={`activity-indicator ${activityStatus.mouseClick ? 'active' : ''} ${!isConnected ? 'disabled' : ''}`}>
          <span className="indicator-label">{t('activity.mouseClick')}</span>
          <span className={`indicator-status ${activityStatus.mouseClick ? 'active' : ''}`}></span>
        </div>
        <div className={`activity-indicator ${activityStatus.screen ? 'active' : ''} ${!isConnected ? 'disabled' : ''}`}>
          <span className="indicator-label">{t('activity.screenChange')}</span>
          <span className={`indicator-status ${activityStatus.screen ? 'active' : ''}`}></span>
        </div>
        <div className={`activity-indicator ${activityStatus.audio ? 'active' : ''} ${!isConnected ? 'disabled' : ''}`}>
          <span className="indicator-label">{t('activity.audio')}</span>
          <span className={`indicator-status ${activityStatus.audio ? 'active' : ''}`}></span>
        </div>
      </div>
      {activityStatus.activeWindow && (
        <div className="active-window">
          <span className="window-label">{t('activity.status')}:</span>
          <span className="window-name">{activityStatus.activeWindow}</span>
        </div>
      )}
    </div>
  );
};

export default ActivityMonitor;