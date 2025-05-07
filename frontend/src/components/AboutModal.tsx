import React from 'react';
import Modal from './Modal';

interface AboutModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const AboutModal: React.FC<AboutModalProps> = ({ isOpen, onClose }) => {
  return (
    <Modal
      isOpen={isOpen}
      title="About Studente AWS"
      onClose={onClose}
      footer={
        <button className="modal-button" onClick={onClose}>
          Close
        </button>
      }
    >
      <div className="about-content">
        <h3>AWS Management and Monitoring</h3>
        <p>Studente AWS is a tool designed to help monitor and manage AWS resources while tracking user activity to maintain cloud resource usage efficiency.</p>
        
        <div className="development-status">
          <h4>Development Status</h4>
          <p><strong>⚠️ CURRENTLY UNDER DEVELOPMENT ⚠️</strong></p>
        </div>
        
        <h4>Features</h4>
        <ul>
          <li>EC2 Instance Management</li>
          <li>ECS Cluster Monitoring</li>
          <li>EKS Cluster Monitoring</li>
          <li>User Activity Tracking</li>
          <li>Timer-based Resource Management</li>
        </ul>
        
        <h4>Version</h4>
        <p>1.0.0</p>
        
        <div className="tracker-download">
          <h4>Studente AWS Tracker</h4>
          <p>Download the tracker: <a href="https://github.com/taxi-tabby/studente_aws/raw/refs/heads/main/dist/main.exe" target="_blank" rel="noopener noreferrer">Download Executable</a></p>
        </div>
        
        <div className="copyright-info">
          <p>&copy; {new Date().getFullYear()} <a href="mailto:rkdmf0000@gmail.com">rkdmf0000@gmail.com</a></p>
        </div>
      </div>
    </Modal>
  );
};

export default AboutModal;