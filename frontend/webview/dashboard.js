(function() {
  // Check if we're running in VS Code
  const vscode = acquireVsCodeApi ? acquireVsCodeApi() : null;
  let wsClient = null;
  
  document.addEventListener('DOMContentLoaded', function() {
    // If we're in a regular browser (development mode) and don't have a VSCode webview
    if (!vscode) {
      initializeDevEnvironment();
    } else {
      initializeVSCodeEnvironment();
    }
    
    // Add event listeners to the refresh buttons
    document.querySelectorAll('.refresh-btn').forEach(button => {
      button.addEventListener('click', () => {
        const service = button.dataset.service;
        if (service) {
          refreshService(service);
        }
      });
    });
  });
  
  function initializeDevEnvironment() {
    console.log('Running in development mode');
    
    // Development mode - WebSocket connection is handled in dashboard-dev.html
    // Just configure the UI
    document.querySelectorAll('.refresh-btn').forEach(button => {
      const service = button.dataset.service;
      if (service) {
        refreshService(service);
      }
    });

    // 개발 모드에서도 활동 모니터링 시작
    startActivityMonitoring();
  }
  
  function initializeVSCodeEnvironment() {
    console.log('Running in VS Code webview');
    
    // Add VS Code specific behavior
    window.addEventListener('message', event => {
      const message = event.data;
      
      switch (message.type) {
        case 'wsMessage':
          handleWebSocketMessage(message.data);
          break;
      }
    });
    
    // 활동 모니터링 시작 (페이지 로딩 시 자동 시작)
    startActivityMonitoring();
    
    // Initialize by requesting data
    refreshAllServices();
  }

  function startActivityMonitoring() {
    logActivity("활동 모니터링 시작 중...");
    
    if (vscode) {
      // VS Code 환경에서 메시지 전송
      vscode.postMessage({
        command: 'sendWs',
        data: JSON.stringify({
          action: 'startMonitoring'
        })
      });
      console.log("startMonitoring 액션 전송됨 (VS Code)");
    } else if (wsClient && wsClient.readyState === WebSocket.OPEN) {
      // 개발 환경에서 WebSocket 메시지 전송
      wsClient.send(JSON.stringify({
        action: 'startMonitoring'
      }));
      console.log("startMonitoring 액션 전송됨 (Dev)");
    } else {
      console.warn("WebSocket 연결이 없어 startMonitoring 액션을 전송할 수 없습니다.");
    }
  }
  
  function refreshAllServices() {
    refreshService('ec2');
    refreshService('ecs');
    refreshService('eks');
  }
  
  function refreshService(service) {
    logActivity(`Requesting ${service.toUpperCase()} data...`);
    
    if (vscode) {
      // If VS Code environment, send message via VS Code's postMessage API
      vscode.postMessage({
        command: 'sendWs',
        data: JSON.stringify({
          service: service,
          action: 'list'
        })
      });
    } else if (wsClient && wsClient.readyState === WebSocket.OPEN) {
      // If dev environment, the WebSocket is handled in dashboard-dev.html
      wsClient.send(JSON.stringify({
        service: service,
        action: 'list'
      }));
    }
  }
  
  function handleWebSocketMessage(message) {
    console.log('Received message:', message);
    
    if (typeof message === 'string') {
      try {
        message = JSON.parse(message);
      } catch (e) {
        console.error('Error parsing message:', e);
        return;
      }
    }
    
    // 활동 모니터링 응답 처리
    if (message.service === 'activity') {
      logActivity(`활동 모니터링 상태: ${message.status || 'update'} - ${message.message}`);
      return;
    }
    
    if (message.type === 'serviceData') {
      updateServiceData(message.service, message.data);
      logActivity(`Received ${message.service.toUpperCase()} data`);
    }
  }
  
  function updateServiceData(service, data) {
    const container = document.getElementById(`${service}-${service === 'ec2' ? 'instances' : 'clusters'}`);
    
    if (!container) {
      console.error(`Container for ${service} not found`);
      return;
    }
    
    if (!data || data.length === 0) {
      container.innerHTML = `<p>No ${service.toUpperCase()} ${service === 'ec2' ? 'instances' : 'clusters'} found</p>`;
      return;
    }
    
    let html = '<table class="data-table"><thead><tr>';
    
    // Generate table headers based on the first item's keys
    const headers = Object.keys(data[0]);
    headers.forEach(header => {
      html += `<th>${header}</th>`;
    });
    
    html += '</tr></thead><tbody>';
    
    // Generate table rows
    data.forEach(item => {
      html += '<tr>';
      headers.forEach(header => {
        let value = item[header];
        
        // Apply styling based on status
        if (header === 'state' || header === 'status') {
          const statusClass = value.toLowerCase();
          html += `<td class="${statusClass}">${value}</td>`;
        } else {
          html += `<td>${value}</td>`;
        }
      });
      html += '</tr>';
    });
    
    html += '</tbody></table>';
    container.innerHTML = html;
  }
  
  function logActivity(message) {
    const logContainer = document.getElementById('activity-log');
    const timestamp = new Date().toLocaleTimeString();
    const logEntry = document.createElement('p');
    logEntry.innerHTML = `<span class="timestamp">${timestamp}</span> ${message}`;
    
    logContainer.appendChild(logEntry);
    
    // Keep only the latest 20 entries
    while (logContainer.children.length > 20) {
      logContainer.removeChild(logContainer.firstChild);
    }
    
    // Auto-scroll to bottom
    logContainer.scrollTop = logContainer.scrollHeight;
  }
  
  // Expose some functions to the global scope for development mode
  window.dashboardAPI = {
    refreshService,
    handleWebSocketMessage,
    logActivity,
    startActivityMonitoring
  };
})();