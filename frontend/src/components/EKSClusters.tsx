import React from 'react';
import type { EKSCluster } from '../types/aws';
import './AWSServices.css';

interface EKSClustersProps {
  clusters: EKSCluster[];
}

const EKSClusters: React.FC<EKSClustersProps> = ({ clusters }) => {
  return (
    <div className="dashboard-section">
      <h2>EKS Clusters</h2>
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