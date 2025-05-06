import os
import sys
import subprocess

def install_pyinstaller():
    """PyInstaller 패키지를 설치합니다."""
    try:
        print("PyInstaller 설치 중...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("PyInstaller 설치 완료!")
    except subprocess.CalledProcessError as e:
        print(f"PyInstaller 설치 실패: {e}")
        sys.exit(1)

def create_executable():
    """Python 스크립트를 실행파일로 변환합니다."""
    try:
        print("실행파일 생성 중...")
        subprocess.check_call(["pyinstaller", "--onefile", "--noconsole", "main.py"])
        print(f"실행파일 생성 완료! 경로: {os.path.join(os.getcwd(), 'dist', 'main.exe')}")
    except subprocess.CalledProcessError as e:
        print(f"실행파일 생성 실패: {e}")
        sys.exit(1)

def main():
    install_pyinstaller()
    create_executable()
    print("프로그램 실행파일 생성이 완료되었습니다.")

if __name__ == "__main__":
    main()