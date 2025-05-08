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

        <div className="github-repo">
          <h4>GitHub Repository</h4>
          <p><a href="https://github.com/taxi-tabby/studente_aws" target="_blank" rel="noopener noreferrer">https://github.com/taxi-tabby/studente_aws</a></p>
        </div>

        <h4>만든 넘</h4>
        <p>아직 까진 나 혼자 단독 개발</p>
        
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