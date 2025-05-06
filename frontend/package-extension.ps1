# PowerShell script to package the VS Code extension

# Ensure dependencies are installed
Write-Host "Installing dependencies..." -ForegroundColor Green
npm install

# Compile TypeScript
Write-Host "Compiling TypeScript..." -ForegroundColor Green
npm run compile

# Install vsce if not already installed
Write-Host "Ensuring vsce is installed..." -ForegroundColor Green
npm list -g vsce > $null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing vsce globally..." -ForegroundColor Yellow
    npm install -g vsce
}

# Package the extension
Write-Host "Packaging extension..." -ForegroundColor Green
vsce package

Write-Host "Extension packaged successfully! Install the .vsix file in VS Code." -ForegroundColor Green
Write-Host "To install, run: code --install-extension aws-dashboard-0.1.0.vsix" -ForegroundColor Cyan