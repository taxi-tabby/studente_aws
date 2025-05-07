import React, { useState, useEffect } from 'react';
import './Timer.css';

interface TimerProps {
  value: number; // 밀리초 단위 타이머 값 (서버에서 직접 받은 남은 시간)
  maxValue?: number; // 최대 타이머 값
  isActive?: boolean; // 타이머가 활성화되어 있는지 (사용자 활동이 있는지)
  isConnected?: boolean; // 서버와 연결되어 있는지
}

const formatTime = (milliseconds: number) => {
  const totalSeconds = Math.floor(milliseconds / 1000);
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  
  return {
    hours,
    minutes,
    seconds,
    formatted: `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
  };
};

// 타이머 기본 최대값 (30분)
const DEFAULT_MAX_VALUE = 30 * 60 * 1000;

const Timer: React.FC<TimerProps> = ({ value, maxValue = DEFAULT_MAX_VALUE, isActive = true, isConnected = true }) => {
  // 서버에서 직접 남은 시간을 받으므로 별도 계산 필요 없음
  const remainingTime = value;
  const time = formatTime(remainingTime);
  
  // 시간이 얼마나 남았는지에 따른 색상 결정
  const percentRemaining = (remainingTime / maxValue) * 100;
  const [timerClass, setTimerClass] = useState('timer-normal');
  const [pulseEffect, setPulseEffect] = useState(false);
  
  useEffect(() => {
    // 시간이 얼마나 남았는지에 따라 타이머 클래스 결정
    if (percentRemaining <= 10) {
      setTimerClass('timer-critical');
    } else if (percentRemaining <= 30) {
      setTimerClass('timer-warning');
    } else {
      setTimerClass('timer-normal');
    }
    
    // 사용자 활동이 감지되면 펄스 효과 주기
    if (isActive && isConnected) {
      setPulseEffect(true);
      const timer = setTimeout(() => setPulseEffect(false), 1000);
      return () => clearTimeout(timer);
    }
  }, [percentRemaining, isActive, isConnected]);
  
  return (
    <div className={`timer-container ${timerClass} ${pulseEffect ? 'timer-pulse' : ''} ${!isConnected ? 'timer-disconnected' : ''}`}>
      <div className="timer-title">
        남은 세션 시간
        {!isConnected && <span className="timer-connection-warning">(연결 끊김)</span>}
      </div>
      <div className="timer-value">
        <div className="time-unit">
          <span className="time-number">{time.hours.toString().padStart(2, '0')}</span>
          <span className="time-label">시간</span>
        </div>
        <div className="time-separator">:</div>
        <div className="time-unit">
          <span className="time-number">{time.minutes.toString().padStart(2, '0')}</span>
          <span className="time-label">분</span>
        </div>
        <div className="time-separator">:</div>
        <div className="time-unit">
          <span className="time-number">{time.seconds.toString().padStart(2, '0')}</span>
          <span className="time-label">초</span>
        </div>
      </div>
      <div className="timer-progress-container">
        <div 
          className="timer-progress-bar" 
          style={{ width: `${isConnected ? percentRemaining : 0}%` }}
        ></div>
      </div>
    </div>
  );
};

export default Timer;