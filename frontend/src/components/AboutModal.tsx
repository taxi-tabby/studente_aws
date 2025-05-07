import React from 'react';
import { useTranslation } from 'react-i18next';
import Modal from './Modal';

interface AboutModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const AboutModal: React.FC<AboutModalProps> = ({ isOpen, onClose }) => {
  const { t } = useTranslation();
  
  return (
    <Modal
      isOpen={isOpen}
      title={t('about.title', 'About Studente AWS')}
      onClose={onClose}
      footer={
        <button className="modal-button" onClick={onClose}>
          {t('buttons.close', 'Close')}
        </button>
      }
    >
      <div className="about-content">
        <h3>{t('about.subtitle', 'AWS Management and Monitoring')}</h3>
        <p>{t('about.description', 'Studente AWS is a tool designed to help monitor and manage AWS resources while tracking user activity to maintain cloud resource usage efficiency.')}</p>
        
        <h4>{t('about.features', 'Features')}</h4>
        <ul>
          <li>{t('about.feature1', 'EC2 Instance Management')}</li>
          <li>{t('about.feature2', 'ECS Cluster Monitoring')}</li>
          <li>{t('about.feature3', 'EKS Cluster Monitoring')}</li>
          <li>{t('about.feature4', 'User Activity Tracking')}</li>
          <li>{t('about.feature5', 'Timer-based Resource Management')}</li>
        </ul>
        
        <h4>{t('about.version', 'Version')}</h4>
        <p>1.0.0</p>
        
        <h4>{t('about.contact', 'Contact')}</h4>
        <p>
          <a href="mailto:rkdmf0000@gmail.com">rkdmf0000@gmail.com</a>
        </p>
        
        <div className="copyright-info">
          <p>&copy; {new Date().getFullYear()} Studente AWS</p>
        </div>
      </div>
    </Modal>
  );
};

export default AboutModal;