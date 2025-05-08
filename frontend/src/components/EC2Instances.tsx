import React from 'react';
import type { EC2Instance } from '../types/aws';
import './AWSServices.css';
import { useTranslation } from 'react-i18next';
import { WebSocketClient, ServiceType } from '../utils/WebSocketClient';

interface EC2InstancesProps {
  instances: EC2Instance[];
  onStartInstance?: (instanceId: string) => void;
  onStopInstance?: (instanceId: string) => void;
  isConnected?: boolean; // 연결 상태 추가
  webSocketClient?: WebSocketClient; // WebSocketClient 인스턴스 추가
}

const EC2Instances: React.FC<EC2InstancesProps> = ({ 
  instances, 
  onStartInstance, 
  onStopInstance,
  isConnected = true, // 기본값은 연결된 상태
  webSocketClient // WebSocketClient 인스턴스
}) => {
  const { t } = useTranslation();
  
  const handleStartInstance = (instanceId: string) => {
    // 웹소켓 클라이언트가 제공된 경우 직접 명령 체계 활용
    if (webSocketClient && isConnected) {
      console.log(`EC2 인스턴스 시작 요청: ${instanceId}`);
      // webSocketClient.startEC2Instance(instanceId);
      return;
    }
    
    // 기존 방식 유지 (하위 호환성)
    if (onStartInstance && isConnected) {
      onStartInstance(instanceId);
    }
  };

  const handleStopInstance = (instanceId: string) => {
    // 웹소켓 클라이언트가 제공된 경우 직접 명령 체계 활용
    if (webSocketClient && isConnected) {
      console.log(`EC2 인스턴스 중지 요청: ${instanceId}`);
      // webSocketClient.stopEC2Instance(instanceId);
      return;
    }
    
    // 기존 방식 유지 (하위 호환성)
    if (onStopInstance && isConnected) {
      onStopInstance(instanceId);
    }
  };
  
  const handleRefresh = () => {
    // 웹소켓 클라이언트가 제공된 경우 직접 명령 체계 활용
    if (webSocketClient && isConnected) {
      console.log('EC2 서비스 데이터 새로고침 요청');
      webSocketClient.refreshService(ServiceType.EC2);
    }
  };

  return (
    <div className={`dashboard-section ${!isConnected ? 'disconnected' : ''}`}>
      <div className="section-header">
        <h2>
          EC2 {t('aws.instances')}
          {!isConnected && <span className="connection-warning">({t('connection.disconnected')})</span>}
        </h2>
        <button 
          className="refresh-button" 
          onClick={handleRefresh}
          disabled={!isConnected}
        >
          {t('buttons.refresh')}
        </button>
      </div>
      {instances.length > 0 ? (
        <table className="aws-table">
          <thead>
            <tr>
              <th>{t('table.name')}</th>
              <th>{t('table.id')}</th>
              <th>{t('table.state')}</th>
              <th>{t('table.type')}</th>
              <th>{t('table.region')}</th>
              <th>{t('table.actions')}</th>
            </tr>
          </thead>
          <tbody>
            {instances.map((instance) => (
              <tr key={instance.id}>
                <td>{instance.name}</td>
                <td>{instance.id}</td>
                <td>
                  <span className={`status-badge ${instance.state.toLowerCase()}`}>
                    {instance.state}
                  </span>
                </td>
                <td>{instance.type}</td>
                <td>{instance.region}</td>
                <td className="action-buttons">
                  {isConnected ? (
                    <>
                      {instance.state === 'stopped' && (
                        <button 
                          className="start-button"
                          onClick={() => handleStartInstance(instance.id)}
                          title={t('buttons.start')}
                        >
                          <span role="img" aria-label="Start">▶️</span>
                        </button>
                      )}
                      {instance.state === 'running' && (
                        <button 
                          className="stop-button"
                          onClick={() => handleStopInstance(instance.id)}
                          title={t('buttons.stop')}
                        >
                          <span role="img" aria-label="Stop">⏹️</span>
                        </button>
                      )}
                      {instance.state !== 'running' && instance.state !== 'stopped' && (
                        <span className="status-badge transitioning">
                          {instance.state}...
                        </span>
                      )}
                    </>
                  ) : (
                    <span className="status-disabled">{t('table.notAvailable')}</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p className={!isConnected ? 'text-disconnected' : ''}>
          {isConnected ? t('aws.noInstances') : t('connection.cannotReceiveMessages')}
        </p>
      )}
    </div>
  );
};

export default EC2Instances;