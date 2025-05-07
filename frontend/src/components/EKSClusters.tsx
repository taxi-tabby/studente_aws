import React from 'react';
import type { EKSCluster } from '../types/aws';
import './AWSServices.css';
import { useTranslation } from 'react-i18next';

interface EKSClustersProps {
  clusters: EKSCluster[];
  onRefresh?: () => void;
  isConnected?: boolean; // 연결 상태 추가
}

const EKSClusters: React.FC<EKSClustersProps> = ({ 
  clusters, 
  onRefresh,
  isConnected = true // 기본값은 연결된 상태
}) => {
  const { t } = useTranslation();

  return (
    <div className={`dashboard-section ${!isConnected ? 'disconnected' : ''}`}>
      <div className="section-header">
        <h2>
          EKS {t('aws.clusters')}
          {!isConnected && <span className="connection-warning">({t('connection.disconnected')})</span>}
        </h2>
        <button 
          className="refresh-button" 
          onClick={onRefresh}
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
              <th>Version</th>
              <th>Node Count</th>
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
                <td>{cluster.version}</td>
                <td>{cluster.nodeCount}</td>
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

export default EKSClusters;