import * as vscode from 'vscode';
import * as path from 'path';
import { TcpClient } from './tcpClient';

export class DashboardPanel {
  // Track the current panel
  public static currentPanel: DashboardPanel | undefined;

  private static readonly viewType = 'awsDashboard';
  private readonly _panel: vscode.WebviewPanel;
  private readonly _extensionUri: vscode.Uri;
  private _disposables: vscode.Disposable[] = [];
  private _tcpClient: TcpClient;

  public static createOrShow(extensionUri: vscode.Uri) {
    const column = vscode.window.activeTextEditor
      ? vscode.window.activeTextEditor.viewColumn
      : undefined;

    // If we already have a panel, show it
    if (DashboardPanel.currentPanel) {
      DashboardPanel.currentPanel._panel.reveal(column);
      return;
    }

    // Otherwise, create a new panel
    const panel = vscode.window.createWebviewPanel(
      DashboardPanel.viewType,
      'AWS Dashboard',
      column || vscode.ViewColumn.One,
      {
        // Enable scripts in the webview
        enableScripts: true,
        // Restrict the webview to only load resources from the `webview` directory
        localResourceRoots: [
          vscode.Uri.joinPath(extensionUri, 'webview'),
          vscode.Uri.joinPath(extensionUri, 'media')
        ],
        retainContextWhenHidden: true
      }
    );

    DashboardPanel.currentPanel = new DashboardPanel(panel, extensionUri);
  }

  private constructor(panel: vscode.WebviewPanel, extensionUri: vscode.Uri) {
    this._panel = panel;
    this._extensionUri = extensionUri;

    // Set the webview's initial HTML content
    this._update();

    // Connect to the TCP server
    this._tcpClient = new TcpClient(message => {
      this._panel.webview.postMessage({ type: 'wsMessage', data: message });
    });
    this._tcpClient.connect();

    // Listen for when the panel is disposed
    // This happens when the user closes the panel or when the panel is closed programmatically
    this._panel.onDidDispose(() => this.dispose(), null, this._disposables);

    // Handle messages from the webview
    this._panel.webview.onDidReceiveMessage(
      message => {
        switch (message.command) {
          case 'sendWs':
            this._tcpClient.send(message.data);
            return;
          case 'refreshData':
            // Implement refresh functionality if needed
            return;
        }
      },
      null,
      this._disposables
    );
  }

  public dispose() {
    DashboardPanel.currentPanel = undefined;

    // Clean up resources
    this._tcpClient.disconnect();
    this._panel.dispose();

    while (this._disposables.length) {
      const disposable = this._disposables.pop();
      if (disposable) {
        disposable.dispose();
      }
    }
  }

  private _update() {
    const webview = this._panel.webview;
    this._panel.title = 'AWS Dashboard';
    this._panel.webview.html = this._getHtmlForWebview(webview);
  }

  private _getHtmlForWebview(webview: vscode.Webview) {
    // Get the local path to main script run in the webview
    const scriptPathOnDisk = vscode.Uri.joinPath(this._extensionUri, 'webview', 'dashboard.js');
    const scriptUri = webview.asWebviewUri(scriptPathOnDisk);

    // Get the local path to css file
    const stylePathOnDisk = vscode.Uri.joinPath(this._extensionUri, 'webview', 'dashboard.css');
    const styleUri = webview.asWebviewUri(stylePathOnDisk);

    // Use a nonce to only allow specific scripts to be run
    const nonce = getNonce();

    return `<!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src ${webview.cspSource}; script-src 'nonce-${nonce}';">
      <link href="${styleUri}" rel="stylesheet">
      <title>AWS Dashboard</title>
    </head>
    <body>
      <div class="container">
        <h1>AWS Services Dashboard</h1>
        
        <div class="dashboard-section">
          <h2>EC2 Instances</h2>
          <button class="refresh-btn" data-service="ec2">Refresh EC2</button>
          <div id="ec2-instances" class="service-container">
            <p>Loading EC2 instances...</p>
          </div>
        </div>
        
        <div class="dashboard-section">
          <h2>ECS Clusters</h2>
          <button class="refresh-btn" data-service="ecs">Refresh ECS</button>
          <div id="ecs-clusters" class="service-container">
            <p>Loading ECS clusters...</p>
          </div>
        </div>
        
        <div class="dashboard-section">
          <h2>EKS Clusters</h2>
          <button class="refresh-btn" data-service="eks">Refresh EKS</button>
          <div id="eks-clusters" class="service-container">
            <p>Loading EKS clusters...</p>
          </div>
        </div>
        
        <div class="dashboard-section">
          <h2>Activity Log</h2>
          <div id="activity-log" class="log-container">
            <p>No activity yet</p>
          </div>
        </div>
      </div>
      
      <script nonce="${nonce}" src="${scriptUri}"></script>
    </body>
    </html>`;
  }
}

function getNonce() {
  let text = '';
  const possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  for (let i = 0; i < 32; i++) {
    text += possible.charAt(Math.floor(Math.random() * possible.length));
  }
  return text;
}