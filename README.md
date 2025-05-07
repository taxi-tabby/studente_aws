# Studente AWS

![AWS Monitoring](./readmeasset/s1.gif)

*Read this in: [English](#studente-aws) | [한국어](#studente-aws-1) | [日本語](#studente-aws-2) | [中文](#studente-aws-3)*

## Overview

Studente AWS is a comprehensive tool for real-time monitoring and management of AWS resources designed specifically for budget-conscious developers. This solution helps developers manage and optimize AWS resource usage to reduce costs while maintaining necessary services. The application provides a user-friendly interface to track EC2 instances, ECS clusters, and EKS clusters across multiple regions, combined with local system activity monitoring capabilities.

## Features

- **Real-time AWS Resource Monitoring**:
  - EC2 Instances: Track instance status, type, and availability zone
  - ECS Clusters: Monitor service count, task count, and status
  - EKS Clusters: View version information, node count, and health status

- **System Activity Monitoring**:
  - Keyboard and mouse activity detection
  - Screen state monitoring
  - Audio activity detection
  - Active window tracking

- **Interactive Dashboard**:
  - WebSocket-based real-time updates
  - Interactive resource management interface
  - Custom filter and search capabilities

## Usage Guide

### System Requirements
- Currently supports Windows operating systems only
- Internet connection for accessing the dashboard

### How to Use
1. Run the application by double-clicking `dist/main.exe`
2. Access the dashboard at [https://taxi-tabby.github.io/studente_aws/](https://taxi-tabby.github.io/studente_aws/)
3. The dashboard will automatically connect to the running application
4. Start monitoring your AWS resources and local system activity

### Note
- A VS Code Extension is planned for future releases
- The backend service must be running (main.exe) for the dashboard to display data

## Getting Started

### Prerequisites

- Python 3.9+
- Node.js 16+
- AWS credentials configured

### Installation

1. Set up the backend:
   ```bash
   pip install -r requirements.txt
   python setup.py install
   ```

2. Set up the frontend:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. Reset AWS credentials if needed:
   ```bash
   python reset_credentials.py
   ```

### Building Executable

For Windows:
```
.\build_executable.ps1
```

For Linux/MacOS:
```
./build_executable.sh
```

---

# Studente AWS

## 개요

Studente AWS는 예산이 제한된 개발자를 위한 AWS 리소스 요금 관리 솔루션입니다. 이 도구는 개발자들이 필요한 서비스를 유지하면서 AWS 리소스 사용을 최적화하고 비용을 절감할 수 있도록 도와줍니다. 이 애플리케이션은 여러 리전에 걸쳐 EC2 인스턴스, ECS 클러스터 및 EKS 클러스터를 추적할 수 있는 사용자 친화적인 인터페이스를 제공하며, 로컬 시스템 활동 모니터링 기능이 통합되어 있습니다.

## 기능

- **실시간 AWS 리소스 모니터링**:
  - EC2 인스턴스: 인스턴스 상태, 유형 및 가용 영역 추적
  - ECS 클러스터: 서비스 수, 작업 수 및 상태 모니터링
  - EKS 클러스터: 버전 정보, 노드 수 및 상태 확인

- **시스템 활동 모니터링**:
  - 키보드 및 마우스 활동 감지
  - 화면 상태 모니터링
  - 오디오 활동 감지
  - 활성 창 추적

- **인터랙티브 대시보드**:
  - WebSocket 기반 실시간 업데이트
  - 대화형 리소스 관리 인터페이스
  - 사용자 정의 필터 및 검색 기능

## 사용 가이드

### 시스템 요구사항
- 현재 Windows 운영체제만 지원됨
- 대시보드 접근을 위한 인터넷 연결 필요

### 사용 방법
1. `dist/main.exe` 파일을 더블클릭하여 애플리케이션 실행
2. [https://taxi-tabby.github.io/studente_aws/](https://taxi-tabby.github.io/studente_aws/) 에서 대시보드 접속
3. 대시보드가 실행 중인 애플리케이션에 자동으로 연결됨
4. AWS 리소스 및 로컬 시스템 활동 모니터링 시작

### 참고사항
- VS Code 확장 프로그램은 향후 출시 예정
- 대시보드에 데이터가 표시되려면 백엔드 서비스(main.exe)가 실행 중이어야 함

## 시작하기

### 필수 조건

- Python 3.9 이상
- Node.js 16 이상
- AWS 자격 증명 구성

### 설치

1. 백엔드 설정:
   ```bash
   pip install -r requirements.txt
   python setup.py install
   ```

2. 프론트엔드 설정:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. 필요한 경우 AWS 자격 증명 재설정:
   ```bash
   python reset_credentials.py
   ```

---

# Studente AWS

## 概要

Studente AWSは、予算の限られた開発者のためのAWSリソース料金管理ソリューションです。このツールは、開発者が必要なサービスを維持しながらAWSリソースの使用を最適化し、コストを削減するのに役立ちます。このアプリケーションは、複数のリージョンにわたるEC2インスタンス、ECSクラスター、およびEKSクラスターを追跡するためのユーザーフレンドリーなインターフェースを提供し、ローカルシステムのアクティビティ監視機能も統合されています。

## 特徴

- **リアルタイムAWSリソース監視**:
  - EC2インスタンス: インスタンスの状態、タイプ、可用ゾーンの追跡
  - ECSクラスター: サービス数、タスク数、状態の監視
  - EKSクラスター: バージョン情報、ノード数、健全性状態の表示

- **システムアクティビティ監視**:
  - キーボードとマウスの活動検出
  - 画面状態のモニタリング
  - 音声アクティビティの検出
  - アクティブウィンドウの追跡

- **インタラクティブダッシュボード**:
  - WebSocketベースのリアルタイム更新
  - インタラクティブなリソース管理インターフェース
  - カスタムフィルターと検索機能

## 使用ガイド

### システム要件
- 現在はWindowsオペレーティングシステムのみをサポート
- ダッシュボードへのアクセスにはインターネット接続が必要

### 使用方法
1. `dist/main.exe`をダブルクリックしてアプリケーションを実行
2. [https://taxi-tabby.github.io/studente_aws/](https://taxi-tabby.github.io/studente_aws/)でダッシュボードにアクセス
3. ダッシュボードは実行中のアプリケーションに自動的に接続
4. AWSリソースとローカルシステムのアクティビティの監視を開始

### 注意
- VS Code拡張機能は今後リリース予定
- ダッシュボードにデータを表示するには、バックエンドサービス(main.exe)が実行されている必要があります

## 始め方

### 前提条件

- Python 3.9以上
- Node.js 16以上
- AWS認証情報の設定

### インストール

1. バックエンドのセットアップ:
   ```bash
   pip install -r requirements.txt
   python setup.py install
   ```

2. フロントエンドのセットアップ:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. 必要に応じてAWS認証情報のリセット:
   ```bash
   python reset_credentials.py
   ```

---

# Studente AWS

## 概述

Studente AWS是为预算有限的开发人员设计的AWS资源费用管理解决方案。该工具帮助开发人员在维持必要服务的同时优化AWS资源使用并降低成本。该应用程序提供了用户友好的界面，可跟踪多个区域的EC2实例、ECS集群和EKS集群，并结合本地系统活动监控功能。

## 功能

- **实时AWS资源监控**:
  - EC2实例: 跟踪实例状态、类型和可用区
  - ECS集群: 监控服务数量、任务数量和状态
  - EKS集群: 查看版本信息、节点数和健康状态

- **系统活动监控**:
  - 键盘和鼠标活动检测
  - 屏幕状态监控
  - 音频活动检测
  - 活动窗口跟踪

- **交互式仪表板**:
  - 基于WebSocket的实时更新
  - 交互式资源管理界面
  - 自定义筛选和搜索功能

## 使用指南

### 系统要求
- 目前仅支持Windows操作系统
- 访问仪表板需要互联网连接

### 使用方法
1. 双击`dist/main.exe`运行应用程序
2. 在[https://taxi-tabby.github.io/studente_aws/](https://taxi-tabby.github.io/studente_aws/)访问仪表板
3. 仪表板将自动连接到正在运行的应用程序
4. 开始监控您的AWS资源和本地系统活动

### 注意
- 计划在未来版本中提供VS Code扩展
- 仪表板显示数据需要后端服务(main.exe)正在运行

## 开始使用

### 先决条件

- Python 3.9+
- Node.js 16+
- 已配置AWS凭证

### 安装

1. 设置后端:
   ```bash
   pip install -r requirements.txt
   python setup.py install
   ```

2. 设置前端:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. 如需重置AWS凭证:
   ```bash
   python reset_credentials.py
   ```

