import React from 'react';
import type { EC2Instance } from '../types/aws';
import './AWSServices.css';

interface EC2InstancesProps {
  instances: EC2Instance[];
  onRefresh?: () => void;
  onStartInstance?: (instanceId: string) => void;
  onStopInstance?: (instanceId: string) => void;
  isConnected?: boolean; // 연결 상태 추가
}

const EC2Instances: React.FC<EC2InstancesProps> = ({ 
  instances, 
  onRefresh, 
  onStartInstance, 
  onStopInstance,
  isConnected = true // 기본값은 연결된 상태
}) => {
  const handleStartInstance = (instanceId: string) => {
    if (onStartInstance && isConnected) {
      onStartInstance(instanceId);
    }
  };

  const handleStopInstance = (instanceId: string) => {
    if (onStopInstance && isConnected) {
      onStopInstance(instanceId);
    }
  };

  return (
    <div className={`dashboard-section ${!isConnected ? 'disconnected' : ''}`}>
      <div className="section-header">
        <h2>
          EC2 Instances
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
                  {isConnected ? (
                    <>
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
                    </>
                  ) : (
                    <span className="status-disabled">사용 불가</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p className={!isConnected ? 'text-disconnected' : ''}>
          {isConnected ? 'No EC2 instances available' : '연결이 끊어져 데이터를 표시할 수 없습니다.'}
        </p>
      )}
    </div>
  );
};

export default EC2Instances;