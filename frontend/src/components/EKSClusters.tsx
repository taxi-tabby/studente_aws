import React from 'react';
import type { EKSCluster } from '../types/aws';
import './AWSServices.css';

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
  return (
    <div className={`dashboard-section ${!isConnected ? 'disconnected' : ''}`}>
      <div className="section-header">
        <h2>
          EKS Clusters
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
          {isConnected ? 'No EKS clusters available' : '연결이 끊어져 데이터를 표시할 수 없습니다.'}
        </p>
      )}
    </div>
  );
};

export default EKSClusters;