import React from 'react';
import { useTranslation } from 'react-i18next';
import Modal from './Modal';

interface LicenseModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const LicenseModal: React.FC<LicenseModalProps> = ({ isOpen, onClose }) => {
  const { t } = useTranslation();
  
  return (
    <Modal
      isOpen={isOpen}
      title={t('license.title', 'License Information')}
      onClose={onClose}
      footer={
        <button className="modal-button" onClick={onClose}>
          {t('buttons.close', 'Close')}
        </button>
      }
    >
      <div className="license-content">
        <h3>{t('license.projectLicense', 'Project License')}</h3>
        <div className="project-license">
          <h4>{t('license.backendTitle', 'Python Server Project')}</h4>
          <p>{t('license.noLicense', 'No License')}</p>
          
          <h4>{t('license.frontendTitle', 'Frontend Project')}</h4>
          <p>{t('license.noLicense', 'No License')}</p>
          
          <p>Copyright &copy; {new Date().getFullYear()} <a href="mailto:rkdmf0000@gmail.com">rkdmf0000@gmail.com</a></p>
        </div>
        
        <h4>{t('license.libraries', 'Libraries Used')}</h4>
        
        <h5>{t('license.pythonLibraries', 'Python Server Project Libraries')}</h5>
        <ul className="library-list">
          <li>boto3 - Apache License 2.0 - AWS SDK for Python</li>
          <li>pynput - LGPL-3.0 License - Keyboard and mouse monitoring</li>
          <li>opencv-python - MIT License - Screen change detection</li>
          <li>numpy - BSD License - Numerical computing</li>
          <li>PyAudio - MIT License - Audio detection</li>
          <li>pyyaml - MIT License - YAML file processing</li>
          <li>psutil - BSD License - Process and system utilities</li>
          <li>pywin32 - PSF License - Windows API access</li>
          <li>pyinstaller - GPL License - Creating executable</li>
        </ul>
        
        <h5>{t('license.frontendLibraries', 'Frontend Project Libraries')}</h5>
        <ul className="library-list">
          <li>React - MIT License - UI library</li>
          <li>TypeScript - Apache License 2.0 - Type-safe JavaScript</li>
          <li>Vite - MIT License - Frontend build tool</li>
          <li>i18next - MIT License - Internationalization framework</li>
          <li>react-i18next - MIT License - React internationalization</li>
          <li>react-dom - MIT License - React DOM rendering</li>
          <li>ESLint - MIT License - Code linting</li>
          <li>CSS Modules - MIT License - Component styling</li>
        </ul>
      </div>
    </Modal>
  );
};

export default LicenseModal;