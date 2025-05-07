import React from 'react';
import type { ECSCluster } from '../types/aws';
import './AWSServices.css';

interface ECSClustersProps {
  clusters: ECSCluster[];
  onRefresh?: () => void;
  isConnected?: boolean; // 연결 상태 추가
}

const ECSClusters: React.FC<ECSClustersProps> = ({ 
  clusters, 
  onRefresh,
  isConnected = true // 기본값은 연결된 상태
}) => {
  return (
    <div className={`dashboard-section ${!isConnected ? 'disconnected' : ''}`}>
      <div className="section-header">
        <h2>
          ECS Clusters
          {!isConnected && <span className="connection-warning">(연결 끊김)</span>}
        </h2>
        <button 
          className="refresh-button" 
          onClick={onRefresh}
          disabled={!isConnected}
        >
          <span className="refresh-icon">🔄</span> Refresh
        </button>
      </div>
      {clusters.length > 0 ? (
        <table className="aws-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Status</th>
              <th>Services</th>
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
          {isConnected ? 'No ECS clusters available' : '연결이 끊어져 데이터를 표시할 수 없습니다.'}
        </p>
      )}
    </div>
  );
};

export default ECSClusters;