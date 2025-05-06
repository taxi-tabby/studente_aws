import React from 'react';
import type { EC2Instance } from '../types/aws';
import './AWSServices.css';

interface EC2InstancesProps {
  instances: EC2Instance[];
}

const EC2Instances: React.FC<EC2InstancesProps> = ({ instances }) => {
  return (
    <div className="dashboard-section">
      <h2>EC2 Instances</h2>
      {instances.length > 0 ? (
        <table className="aws-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>ID</th>
              <th>State</th>
              <th>Type</th>
              <th>Availability Zone</th>
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