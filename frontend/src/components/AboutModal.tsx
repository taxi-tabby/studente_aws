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

        <div className="privacy-policy">
          <h4>Privacy Policy</h4>
          <div className="multilingual-privacy">
            <p><strong>EN:</strong> We do not collect your data. We only detect events (keyboard, mouse movement, mouse clicks, screen changes, audio, etc.) without collecting detailed data about these interactions.</p>
            <p><strong>KO:</strong> 저희는 사용자의 데이터를 수집하지 않습니다. 사용하는 대상 데이터(키보드, 마우스 이동, 마우스 클릭, 화면 변화, 오디오 등)는 상세 데이터를 수집하지 않으며 해당 이벤트 발생 여부만 확인합니다.</p>
            <p><strong>JP:</strong> 当社はユーザーデータを収集しません。検出対象のデータ（キーボード、マウスの動き、マウスクリック、画面の変化、音声など）の詳細は収集せず、イベントの発生のみを確認します。</p>
            <p><strong>CN:</strong> 我们不收集您的数据。我们只检测事件（键盘、鼠标移动、鼠标点击、屏幕变化、音频等）而不收集这些交互的详细数据。</p>
          </div>
        </div>

        <div className="disclaimer">
          <h4>Disclaimer</h4>
          <div className="multilingual-disclaimer">
            <p><strong>EN:</strong> All threats or issues arising from the use of this application are the sole responsibility of the individual user.</p>
            <p><strong>KO:</strong> 해당 기능을 사용해서 발생하는 모든 위협은 개인의 책임입니다.</p>
            <p><strong>JP:</strong> この機能の使用によって生じるすべての脅威は、個人の責任となります。</p>
            <p><strong>CN:</strong> 使用此功能产生的所有威胁均由个人负责。</p>
          </div>
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