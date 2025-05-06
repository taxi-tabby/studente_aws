#!/bin/bash

# Linux/Mac Shell 스크립트 - 실행파일 생성

# 색상 설정
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# PyInstaller 설치
echo -e "${GREEN}PyInstaller 설치 중...${NC}"
pip install pyinstaller
if [ $? -ne 0 ]; then
    echo -e "${RED}PyInstaller 설치 실패!${NC}"
    exit 1
fi

# 실행파일 생성
echo -e "${GREEN}실행파일 생성 중...${NC}"
pyinstaller --onefile --noconsole main.py
if [ $? -ne 0 ]; then
    echo -e "${RED}실행파일 생성 실패!${NC}"
    exit 1
fi

echo -e "${GREEN}실행파일 생성 완료! 경로: $(pwd)/dist/main${NC}"

# Linux/Mac 시작 시 자동 실행 설정 (선택사항)
# 주석을 해제하여 사용할 수 있습니다.

# Linux (systemd) 자동 실행 설정
# if [ -d "/etc/systemd/system" ]; then
#     echo -e "${GREEN}리눅스 systemd 서비스로 등록 중...${NC}"
#     SERVICE_FILE="/etc/systemd/system/user-activity-monitor.service"
#     echo "[Unit]
# Description=User Activity Monitor Service
# After=network.target
# 
# [Service]
# ExecStart=$(pwd)/dist/main
# Restart=always
# User=$USER
# 
# [Install]
# WantedBy=multi-user.target" | sudo tee $SERVICE_FILE > /dev/null
# 
#     sudo systemctl daemon-reload
#     sudo systemctl enable user-activity-monitor.service
#     echo -e "${GREEN}systemd 서비스 등록 완료!${NC}"
# fi

# Mac 자동 실행 설정
# if [ "$(uname)" == "Darwin" ]; then
#     echo -e "${GREEN}Mac 시작 프로그램에 등록 중...${NC}"
#     PLIST_FILE="$HOME/Library/LaunchAgents/com.user.activitymonitor.plist"
#     mkdir -p "$HOME/Library/LaunchAgents"
#     echo "<?xml version=\"1.0\" encoding=\"UTF-8\"?>
# <!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\">
# <plist version=\"1.0\">
# <dict>
#     <key>Label</key>
#     <string>com.user.activitymonitor</string>
#     <key>ProgramArguments</key>
#     <array>
#         <string>$(pwd)/dist/main</string>
#     </array>
#     <key>RunAtLoad</key>
#     <true/>
#     <key>KeepAlive</key>
#     <true/>
# </dict>
# </plist>" > "$PLIST_FILE"
#     
#     launchctl load "$PLIST_FILE"
#     echo -e "${GREEN}Mac 시작 프로그램 등록 완료!${NC}"
# fi

echo -e "${GREEN}프로세스 완료!${NC}"