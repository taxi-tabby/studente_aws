import * as vscode from 'vscode';
import { DashboardPanel } from './dashboardPanel';

export function activate(context: vscode.ExtensionContext) {
  console.log('AWS Dashboard extension is now active');

  // Register the command to open the dashboard
  const openDashboardCommand = vscode.commands.registerCommand('aws-dashboard.openDashboard', () => {
    DashboardPanel.createOrShow(context.extensionUri);
  });

  context.subscriptions.push(openDashboardCommand);
}

export function deactivate() {
  // Clean up resources when the extension is deactivated
}