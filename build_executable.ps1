# Windows PowerShell 스크립트 - 실행파일 생성
# 관리자 권한으로 실행하는 것을 권장합니다

# PyInstaller 설치
Write-Host "PyInstaller 설치 중..." -ForegroundColor Green
pip install pyinstaller
if ($LASTEXITCODE -ne 0) {
    Write-Host "PyInstaller 설치 실패!" -ForegroundColor Red
    exit 1
}

# 실행파일 생성
Write-Host "실행파일 생성 중..." -ForegroundColor Green
pyinstaller --onefile --noconsole main.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "실행파일 생성 실패!" -ForegroundColor Red
    exit 1
}

Write-Host "실행파일 생성 완료! 경로: $((Get-Location).Path)\dist\main.exe" -ForegroundColor Green

# Windows 시작 시 자동 실행 설정 (선택사항 - 주석 해제하여 사용)
# $exePath = "$((Get-Location).Path)\dist\main.exe"
# $taskName = "UserActivityMonitor"
# Write-Host "Windows 시작 프로그램에 등록 중..." -ForegroundColor Green
# schtasks /create /tn $taskName /tr $exePath /sc onlogon /rl highest
# if ($LASTEXITCODE -ne 0) {
#     Write-Host "시작 프로그램 등록 실패!" -ForegroundColor Red
# } else {
#     Write-Host "시작 프로그램에 성공적으로 등록되었습니다." -ForegroundColor Green
# }

Write-Host "프로세스 완료!" -ForegroundColor Green