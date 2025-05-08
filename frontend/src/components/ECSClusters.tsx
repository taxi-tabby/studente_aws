import React from 'react';
import type { ECSCluster } from '../types/aws';
import './AWSServices.css';
import { useTranslation } from 'react-i18next';
import { WebSocketClient, ServiceType } from '../utils/WebSocketClient';

interface ECSClustersProps {
  clusters: ECSCluster[];
  isConnected?: boolean; // 연결 상태 추가
  webSocketClient?: WebSocketClient; // WebSocketClient 인스턴스 추가
}

const ECSClusters: React.FC<ECSClustersProps> = ({ 
  clusters, 
  isConnected = true, // 기본값은 연결된 상태
  webSocketClient // WebSocketClient 인스턴스
}) => {
  const { t } = useTranslation();
  
  const handleRefresh = () => {
    // 웹소켓 클라이언트가 제공된 경우 직접 명령 체계 활용
    if (webSocketClient && isConnected) {
      console.log('ECS 서비스 데이터 새로고침 요청');
      webSocketClient.refreshService(ServiceType.ECS);
    }
  };
  
  return (
    <div className={`dashboard-section ${!isConnected ? 'disconnected' : ''}`}>
      <div className="section-header">
        <h2>
          ECS {t('aws.clusters')}
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
      {clusters.length > 0 ? (
        <table className="aws-table">
          <thead>
            <tr>
              <th>{t('table.name')}</th>
              <th>{t('table.state')}</th>
              <th>{t('aws.services')}</th>
              <th>Task Count</th>
              <th>Region</th>
            </tr>
          </thead>
          <tbody>
            {clusters.map((cluster) => (
              <tr key={cluster.name}>
                <td>{cluster.name}</td>
                <td>
                  <span className={`status-badge ${cluster.status.toLowerCase()}`}>
                    {cluster.status}
                  </span>
                </td>
                <td>{cluster.serviceCount}</td>
                <td>{cluster.taskCount}</td>
                <td>{cluster.region}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p className={!isConnected ? 'text-disconnected' : ''}>
          {isConnected ? t('aws.noClusters') : t('connection.cannotReceiveMessages')}
        </p>
      )}
    </div>
  );
};

export default ECSClusters;