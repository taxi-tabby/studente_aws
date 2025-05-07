import React from 'react';
import type { ActivityStatus } from '../types/aws';
import './ActivityMonitor.css';

interface ActivityMonitorProps {
	activityStatus: ActivityStatus;
}

const ActivityMonitor: React.FC<ActivityMonitorProps> = ({ activityStatus }) => {
	return (
		<div className="dashboard-section">
			<h2>Activity Monitoring</h2>
			<div className="activity-container">
				<div className="activity-indicator">
					<span>Keyboard:</span>
					<div
						className={`indicator-light ${activityStatus.keyboard ? 'active' : ''}`}
						data-activity="keyboard"
					></div>
				</div>
				<div className="activity-indicator">
					<span>Mouse Movement:</span>
					<div
						className={`indicator-light ${activityStatus.mouseMovement ? 'active' : ''}`}
						data-activity="mouse-movement"
					></div>
				</div>
				<div className="activity-indicator">
					<span>Mouse Click:</span>
					<div
						className={`indicator-light ${activityStatus.mouseClick ? 'active' : ''}`}
						data-activity="mouse-click"
					></div>
				</div>
				<div className="activity-indicator disabled">
					<span>Screen Change:</span>
					<div className="indicator-light" data-activity="screen"></div>
					<small>(Not implemented)</small>
				</div>



				<div className="activity-indicator">
					<span>Audio:</span>
					<div className={`indicator-light ${activityStatus.audio ? 'active' : ''}`} data-activity="audio"></div>
					{/* <small>(Not implemented)</small> */}
				</div>



				<div className="activity-indicator disabled">
					<span>Active Window:</span>
					<div className="active-window-name">Not implemented</div>
				</div>
			</div>
		</div>
	);
};

export default ActivityMonitor;