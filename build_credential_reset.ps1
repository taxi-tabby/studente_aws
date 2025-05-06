# AWS 자격 증명 초기화 도구를 EXE로 빌드하는 PowerShell 스크립트

# 콘솔에 메시지 출력
Write-Host "AWS 자격 증명 초기화 도구 빌드를 시작합니다..." -ForegroundColor Green

# 필요한 패키지 확인 및 설치
Write-Host "PyInstaller 패키지가 설치되어 있는지 확인합니다..." -ForegroundColor Yellow
$pyinstallerCheck = python -c "import PyInstaller" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "PyInstaller 패키지를 설치합니다..." -ForegroundColor Yellow
    pip install pyinstaller
    if ($LASTEXITCODE -ne 0) {
        Write-Host "PyInstaller 설치 중 오류가 발생했습니다." -ForegroundColor Red
        exit 1
    }
}

# EXE 파일 빌드
Write-Host "자격 증명 초기화 도구를 빌드합니다..." -ForegroundColor Yellow
pyinstaller --clean --onefile --noconsole `
    --name "AWS_Credential_Reset" `
    --icon="G:\aws_study\resources\reset_icon.ico" `
    --add-data "G:\aws_study\resources\reset_icon.ico;resources\" `
    "G:\aws_study\reset_credentials.py"

# 빌드 성공 여부 확인
if ($LASTEXITCODE -eq 0) {
    # EXE 파일 경로
    $exePath = "G:\aws_study\dist\AWS_Credential_Reset.exe"
    
    # EXE 파일이 존재하는지 확인
    if (Test-Path $exePath) {
        Write-Host "자격 증명 초기화 도구 빌드에 성공했습니다!" -ForegroundColor Green
        Write-Host "파일 위치: $exePath" -ForegroundColor Cyan
    } else {
        Write-Host "EXE 파일이 생성되었지만 예상 위치에 없습니다." -ForegroundColor Red
    }
} else {
    Write-Host "자격 증명 초기화 도구 빌드 중 오류가 발생했습니다." -ForegroundColor Red
}

# 작업 완료
Write-Host "빌드 작업이 완료되었습니다." -ForegroundColor Green