import React from 'react';
import type { EC2Instance } from '../types/aws';
import './AWSServices.css';

interface EC2InstancesProps {
  instances: EC2Instance[];
  onRefresh?: () => void;
  onStartInstance?: (instanceId: string) => void;
  onStopInstance?: (instanceId: string) => void;
}

const EC2Instances: React.FC<EC2InstancesProps> = ({ instances, onRefresh, onStartInstance, onStopInstance }) => {
  const handleStartInstance = (instanceId: string) => {
    if (onStartInstance) {
      onStartInstance(instanceId);
    }
  };

  const handleStopInstance = (instanceId: string) => {
    if (onStopInstance) {
      onStopInstance(instanceId);
    }
  };

  return (
    <div className="dashboard-section">
      <div className="section-header">
        <h2>EC2 Instances</h2>
        <button className="refresh-button" onClick={onRefresh}>
          <span className="refresh-icon">🔄</span> Refresh
        </button>
      </div>
      {instances.length > 0 ? (
        <table className="aws-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>ID</th>
              <th>State</th>
              <th>Type</th>
              <th>Availability Zone</th>
              <th>Actions</th>
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
                <td>{instance.zone}</td>
                <td className="action-buttons">
                  {instance.state === 'stopped' && (
                    <button 
                      className="start-button"
                      onClick={() => handleStartInstance(instance.id)}
                      title="Start Instance"
                    >
                      <span role="img" aria-label="Start">▶️ Start</span>
                    </button>
                  )}
                  {instance.state === 'running' && (
                    <button 
                      className="stop-button"
                      onClick={() => handleStopInstance(instance.id)}
                      title="Stop Instance"
                    >
                      <span role="img" aria-label="Stop">⏹️ Stop</span>
                    </button>
                  )}
                  {instance.state !== 'running' && instance.state !== 'stopped' && (
                    <span className="status-badge transitioning">
                      {instance.state}...
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p>No EC2 instances available</p>
      )}
    </div>
  );
};

export default EC2Instances;