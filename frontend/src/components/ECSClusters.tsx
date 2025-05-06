import React from 'react';
import type { ECSCluster } from '../types/aws';
import './AWSServices.css';

interface ECSClustersProps {
  clusters: ECSCluster[];
  onRefresh?: () => void;
}

const ECSClusters: React.FC<ECSClustersProps> = ({ clusters, onRefresh }) => {
  return (
    <div className="dashboard-section">
      <div className="section-header">
        <h2>ECS Clusters</h2>
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
              <th>Services</th>
              <th>Running Tasks</th>
              <th>Pending Tasks</th>
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
                <td>{cluster.activeServices}</td>
                <td>{cluster.runningTasks}</td>
                <td>{cluster.pendingTasks}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p>No ECS clusters available</p>
      )}
    </div>
  );
};

export default ECSClusters;