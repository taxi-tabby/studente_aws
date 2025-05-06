import React from 'react';
import type { EKSCluster } from '../types/aws';
import './AWSServices.css';

interface EKSClustersProps {
  clusters: EKSCluster[];
  onRefresh?: () => void;
}

const EKSClusters: React.FC<EKSClustersProps> = ({ clusters, onRefresh }) => {
  return (
    <div className="dashboard-section">
      <div className="section-header">
        <h2>EKS Clusters</h2>
        <button className="refresh-button" onClick={onRefresh}>
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
              <th>Endpoint</th>
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
                <td className="endpoint">{cluster.endpoint}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p>No EKS clusters available</p>
      )}
    </div>
  );
};

export default EKSClusters;