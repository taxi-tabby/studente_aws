# Contributing to Studente AWS

*Read this in: [English](#installation-and-setup) | [한국어](#설치-및-설정) | [日本語](#インストールとセットアップ) | [中文](#安装与设置)*

> **Note:** This contribution documentation is still under development. Full guidelines and pull request processes are not yet available. We're actively working on completing this documentation. Please check back soon for updates.

## Installation and Setup

### Prerequisites
- Python 3.9+ installed
- Node.js 16+ and npm installed (for frontend development)
- AWS CLI configured with appropriate credentials
- Git installed

### Installation Steps
1. Clone the repository:
   ```bash
   git clone https://github.com/taxi-tabby/studente_aws.git
   cd studente_aws
   ```

2. Set up the backend:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up the frontend:
   ```bash
   cd frontend
   npm install
   ```

4. Configure AWS credentials:
   - Run the credential setup script:
     - Windows: `.\build_credential_reset.ps1`
     - Linux/Mac: `./build_executable.sh`
   - Follow the on-screen prompts to enter your AWS access key and secret

## Development

### Project Structure
- `core/`: Backend Python modules
  - `aws_services.py`: AWS service interaction logic
  - `activity_monitor.py`: System activity monitoring
  - `tcp_server.py` & `udp_server.py`: Network communication
- `frontend/`: React-based dashboard UI
- `main.py`: Application entry point

### Development Workflow
1. Make your changes in the appropriate modules
2. Test locally by running:
   ```bash
   python main.py
   ```
3. For frontend development, run:
   ```bash
   cd frontend
   npm run dev
   ```

### Building

> **Important:** Currently, only Windows builds are supported. Linux build capabilities are under development and not yet available.

- Build the executable:
  - Windows: `.\build_executable.ps1`
  - Linux/Mac: `./build_executable.sh` (Not yet functional)
- The output executable will be available in the `dist/` directory

## Contribution Guidelines

> **Important:** Detailed contribution guidelines are currently being prepared and will be available soon.

### Code Style
- Python: Follow PEP 8
- TypeScript/React: Follow project ESLint configuration
- Use meaningful variable and function names
- Include docstrings for all functions and classes

### Pull Request Process

> **Note:** The Pull Request process is still being finalized. Please check back later for detailed instructions.

### Testing
- Write tests for all new functionality
- Ensure all existing tests pass before submitting a PR
- Include both unit and integration tests where appropriate

---

# Studente AWS 기여 가이드

> **참고:** 이 기여 문서는 아직 개발 중입니다. 전체 가이드라인 및 PR(Pull Request) 프로세스는 아직 준비되지 않았습니다. 현재 이 문서를 완성하기 위해 적극적으로 작업 중입니다. 업데이트를 위해 곧 다시 확인해 주세요.

## 설치 및 설정

### 사전 요구사항
- Python 3.9+ 설치됨
- Node.js 16+ 및 npm 설치됨 (프론트엔드 개발용)
- AWS CLI가 적절한 자격 증명으로 구성됨
- Git 설치됨

### 설치 단계
1. 리포지토리 복제:
   ```bash
   git clone https://github.com/taxi-tabby/studente_aws.git
   cd studente_aws
   ```

2. 백엔드 설정:
   ```bash
   pip install -r requirements.txt
   ```

3. 프론트엔드 설정:
   ```bash
   cd frontend
   npm install
   ```

4. AWS 자격 증명 구성:
   - 자격 증명 설정 스크립트 실행:
     - Windows: `.\build_credential_reset.ps1`
     - Linux/Mac: `./build_executable.sh`
   - 화면 안내에 따라 AWS 액세스 키와 시크릿을 입력하세요

## 개발

### 프로젝트 구조
- `core/`: 백엔드 Python 모듈
  - `aws_services.py`: AWS 서비스 상호 작용 로직
  - `activity_monitor.py`: 시스템 활동 모니터링
  - `tcp_server.py` & `udp_server.py`: 네트워크 통신
- `frontend/`: React 기반 대시보드 UI
- `main.py`: 애플리케이션 진입점

### 개발 워크플로우
1. 적절한 모듈에서 변경 사항을 만듭니다
2. 로컬에서 다음을 실행하여 테스트합니다:
   ```bash
   python main.py
   ```
3. 프론트엔드 개발의 경우 다음을 실행합니다:
   ```bash
   cd frontend
   npm run dev
   ```

### 빌드

> **중요:** 현재는 Windows 빌드만 지원됩니다. Linux 빌드 기능은 개발 중이며 아직 사용할 수 없습니다.

- 실행 파일 빌드:
  - Windows: `.\build_executable.ps1`
  - Linux/Mac: `./build_executable.sh` (아직 작동하지 않음)
- 출력된 실행 파일은 `dist/` 디렉토리에서 사용할 수 있습니다

## 기여 가이드라인

> **중요:** 상세한 기여 가이드라인은 현재 준비 중이며 곧 제공될 예정입니다.

### 코드 스타일
- Python: PEP 8 준수
- TypeScript/React: 프로젝트 ESLint 구성 준수
- 의미 있는 변수 및 함수 이름 사용
- 모든 함수 및 클래스에 문서 문자열(docstring) 포함

### Pull Request 프로세스

> **참고:** Pull Request 프로세스는 아직 확정 중입니다. 자세한 지침은 나중에 다시 확인해 주세요.

### 테스팅
- 모든 새로운 기능에 대한 테스트 작성
- PR을 제출하기 전에 모든 기존 테스트가 통과하는지 확인
- 필요한 경우 단위 테스트와 통합 테스트를 모두 포함

---

# Studente AWS 貢献ガイド

> **注意:** この貢献ドキュメントはまだ開発中です。完全なガイドラインとプルリクエストプロセスはまだ利用できません。このドキュメントの完成に向けて積極的に取り組んでいます。更新については近日中に再度ご確認ください。

## インストールとセットアップ

### 前提条件
- Python 3.9+ がインストールされていること
- Node.js 16+ と npm がインストールされていること（フロントエンド開発用）
- AWS CLIが適切な認証情報で構成されていること
- Gitがインストールされていること

### インストール手順
1. リポジトリをクローン:
   ```bash
   git clone https://github.com/taxi-tabby/studente_aws.git
   cd studente_aws
   ```

2. バックエンドのセットアップ:
   ```bash
   pip install -r requirements.txt
   ```

3. フロントエンドのセットアップ:
   ```bash
   cd frontend
   npm install
   ```

4. AWS認証情報の設定:
   - 認証情報セットアップスクリプトを実行:
     - Windows: `.\build_credential_reset.ps1`
     - Linux/Mac: `./build_executable.sh`
   - 画面の指示に従ってAWSアクセスキーとシークレットを入力

## 開発

### プロジェクト構造
- `core/`: バックエンドPythonモジュール
  - `aws_services.py`: AWSサービス連携ロジック
  - `activity_monitor.py`: システムアクティビティ監視
  - `tcp_server.py` & `udp_server.py`: ネットワーク通信
- `frontend/`: Reactベースのダッシュボード UI
- `main.py`: アプリケーションのエントリポイント

### 開発ワークフロー
1. 適切なモジュールで変更を行う
2. ローカルで実行してテスト:
   ```bash
   python main.py
   ```
3. フロントエンド開発の場合:
   ```bash
   cd frontend
   npm run dev
   ```

### ビルド

> **重要:** 現在はWindowsビルドのみがサポートされています。Linuxビルド機能は開発中であり、まだ利用できません。

- 実行ファイルのビルド:
  - Windows: `.\build_executable.ps1`
  - Linux/Mac: `./build_executable.sh` (まだ機能していません)
- 出力される実行ファイルは `dist/` ディレクトリで利用可能

## 貢献ガイドライン

> **重要:** 詳細な貢献ガイドラインは現在準備中であり、まもなく利用可能になります。

### コードスタイル
- Python: PEP 8に準拠
- TypeScript/React: プロジェクトのESLint構成に準拠
- 意味のある変数名と関数名を使用
- すべての関数とクラスにドキュメント文字列を含める

### プルリクエストのプロセス

> **注意:** プルリクエストプロセスはまだ確定中です。詳細な手順については後ほど再度ご確認ください。

### テスト
- すべての新機能についてテストを作成
- PRを提出する前にすべての既存のテストが通ることを確認
- 適切な場合はユニットテストと統合テストの両方を含める

---

# Studente AWS 贡献指南

> **注意:** 此贡献文档仍在开发中。完整的指南和拉取请求流程尚未提供。我们正在积极完成这份文档。请稍后再回来查看更新。

## 安装与设置

### 先决条件
- 安装 Python 3.9+
- 安装 Node.js 16+ 和 npm（用于前端开发）
- 配置带有适当凭证的 AWS CLI
- 安装 Git

### 安装步骤
1. 克隆仓库:
   ```bash
   git clone https://github.com/taxi-tabby/studente_aws.git
   cd studente_aws
   ```

2. 设置后端:
   ```bash
   pip install -r requirements.txt
   ```

3. 设置前端:
   ```bash
   cd frontend
   npm install
   ```

4. 配置 AWS 凭证:
   - 运行凭证设置脚本:
     - Windows: `.\build_credential_reset.ps1`
     - Linux/Mac: `./build_executable.sh`
   - 按照屏幕提示输入您的 AWS 访问密钥和密钥

## 开发

### 项目结构
- `core/`: 后端 Python 模块
  - `aws_services.py`: AWS 服务交互逻辑
  - `activity_monitor.py`: 系统活动监控
  - `tcp_server.py` 和 `udp_server.py`: 网络通信
- `frontend/`: 基于 React 的仪表板 UI
- `main.py`: 应用程序入口点

### 开发工作流
1. 在相应模块中进行更改
2. 通过运行以下命令在本地测试:
   ```bash
   python main.py
   ```
3. 对于前端开发，运行:
   ```bash
   cd frontend
   npm run dev
   ```

### 构建

> **重要:** 目前仅支持Windows构建。Linux构建功能正在开发中，尚不可用。

- 构建可执行文件:
  - Windows: `.\build_executable.ps1`
  - Linux/Mac: `./build_executable.sh` (尚未功能)
- 输出的可执行文件将在 `dist/` 目录中可用

## 贡献指南

> **重要:** 详细的贡献指南目前正在准备中，不久将会提供。

### 代码风格
- Python: 遵循 PEP 8
- TypeScript/React: 遵循项目 ESLint 配置
- 使用有意义的变量和函数名
- 为所有函数和类包含文档字符串

### 拉取请求流程

> **注意:** 拉取请求流程仍在敲定中。请稍后再查看详细说明。

### 测试
- 为所有新功能编写测试
- 确保在提交 PR 之前通过所有现有测试
- 在适当情况下包括单元测试和集成测试