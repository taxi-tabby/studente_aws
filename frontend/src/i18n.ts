import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

// English translations
const enTranslations = {
  connection: {
    connected: 'Connected',
    connecting: 'Connecting',
    disconnected: 'Disconnected',
    connectionLost: 'Connection lost',
    cannotReceiveMessages: 'Connection is lost. Cannot receive messages.'
  },
  buttons: {
    refresh: 'Refresh',
    retry: 'Retry',
    clearConsole: 'Clear Console',
    start: 'Start',
    stop: 'Stop',
    test: 'Test',
    reset: 'Reset',
    submit: 'Submit'
  },
  password: {
    title: 'Access Password',
    description: 'Enter password to access dashboard.',
    placeholder: 'Enter password',
    submit: 'Confirm',
    verifying: 'Verifying password...',
    creating: 'Setting password...',
    error: {
      empty: 'Please enter a password.',
      invalid: 'Invalid password.',
      mismatch: 'Passwords do not match.',
      tooShort: 'Password must be at least 6 characters.',
      connectionRequired: 'Server connection required. Connecting...',
      connectionFailed: 'Unable to connect to server. Make sure tracker application is running.',
      setup: 'An error occurred while setting the password.'
    },
    setup: {
      title: 'Set Password',
      description: 'Set a password to access the dashboard.',
      new: 'New Password',
      confirm: 'Confirm Password',
      newPlaceholder: 'Enter new password (min. 6 characters)',
      confirmPlaceholder: 'Re-enter password',
      submit: 'Set Password'
    }
  },
  download: {
    title: 'Download Tracker Application (Currently unavailable: under development)',
    description: 'Connect to AWS services, you need to install the Studente AWS Tracker application.',
    windows: 'Download for Windows'
  },  header: {
    language: 'Language',
    about: 'About',
    license: 'License',
    logout: 'Logout'
  },
  aws: {
    instances: 'Instances',
    clusters: 'Clusters',
    services: 'Services',
    noInstances: 'No EC2 instances available',
    noClusters: 'No clusters available',
    noServices: 'No services available'
  },
  activity: {
    keyboard: 'Keyboard',
    mouseMovement: 'Mouse Movement',
    mouseClick: 'Mouse Click',
    screenChange: 'Screen Change',
    audio: 'Audio',
    title: 'Activity',
    status: 'Status'
  },
  table: {
    name: 'Name',
    id: 'ID',
    state: 'State',
    type: 'Type',
    zone: 'Availability Zone',
    actions: 'Actions',
    notAvailable: 'Not available'
  },
  timer: {
    remainingSession: 'Remaining Session Time',
    hours: 'hours',
    minutes: 'minutes',
    seconds: 'seconds'
  },
  console: {
    noMessages: 'No messages received yet.',
    selectMessagePrompt: 'Select a message to view details here.',
    noTimestamp: 'No timestamp',
    filter: 'Filter',
    filterAll: 'All messages',
    filterTest: 'Test messages',
    filterAws: 'AWS services',
    filterActivity: 'Activity',
    filterError: 'Errors'
  },
  interface: {
    title: 'Control Panel',
    textInput: 'Text Input',
    enterText: 'Enter text here...',
    dropdown: 'Dropdown',
    option: 'Option',
    slider: 'Slider',
    checkbox: 'Enable feature',
    radioGroup: 'Select an option',
    action1: 'Action 1',
    action2: 'Action 2',
    action3: 'Action 3'
  }
};

// Korean translations
const koTranslations = {
  connection: {
    connected: '연결됨',
    connecting: '연결 중',
    disconnected: '연결 끊김',
    connectionLost: '연결 끊김',
    cannotReceiveMessages: '연결이 끊어져 있습니다. 메시지를 수신할 수 없습니다.'
  },
  buttons: {
    refresh: '새로고침',
    retry: '재시도',
    clearConsole: '콘솔 지우기',
    start: '시작',
    stop: '중지',
    test: '테스트',
    reset: '초기화',
    submit: '제출'
  },
  password: {
    title: '접근 비밀번호',
    description: '대시보드에 접근하려면 비밀번호를 입력하세요.',
    placeholder: '비밀번호 입력',
    submit: '확인',
    verifying: '비밀번호 확인 중...',
    creating: '비밀번호 설정 중...',
    error: {
      empty: '비밀번호를 입력해주세요.',
      invalid: '잘못된 비밀번호입니다.',
      mismatch: '비밀번호가 일치하지 않습니다.',
      tooShort: '비밀번호는 최소 6자 이상이어야 합니다.',
      connectionRequired: '서버 연결이 필요합니다. 연결 중입니다...',
      connectionFailed: '서버에 연결할 수 없습니다. 트래커 애플리케이션이 실행 중인지 확인하세요.',
      setup: '비밀번호 설정 중 오류가 발생했습니다.'
    },
    setup: {
      title: '비밀번호 설정',
      description: '대시보드 접근을 위한 비밀번호를 설정하세요.',
      new: '새 비밀번호',
      confirm: '비밀번호 확인',
      newPlaceholder: '새 비밀번호 입력 (6자 이상)',
      confirmPlaceholder: '비밀번호 재입력',
      submit: '비밀번호 설정'
    }
  },
  download: {
    title: '트래커 애플리케이션 다운로드 (Currently unavailable: under development)',
    description: 'AWS 서비스에 연결하려면 Studente AWS 트래커 애플리케이션을 설치해야 합니다.',
    windows: '윈도우용 다운로드'
  },  header: {
    language: '언어',
    about: '소개',
    license: '라이선스',
    logout: '로그아웃'
  },
  aws: {
    instances: '인스턴스',
    clusters: '클러스터',
    services: '서비스',
    noInstances: '사용 가능한 EC2 인스턴스가 없습니다',
    noClusters: '사용 가능한 클러스터가 없습니다',
    noServices: '사용 가능한 서비스가 없습니다'
  },
  activity: {
    keyboard: '키보드',
    mouseMovement: '마우스 이동',
    mouseClick: '마우스 클릭',
    screenChange: '화면 변화',
    audio: '오디오',
    title: '활동',
    status: '상태'
  },
  table: {
    name: '이름',
    id: '아이디',
    state: '상태',
    type: '유형',
    zone: '가용 영역',
    actions: '작업',
    notAvailable: '사용 불가'
  },
  timer: {
    remainingSession: '남은 세션 시간',
    hours: '시간',
    minutes: '분',
    seconds: '초'
  },
  console: {
    noMessages: '아직 수신된 메시지가 없습니다.',
    selectMessagePrompt: '메시지를 선택하면 상세 내용이 여기에 표시됩니다.',
    noTimestamp: '타임스탬프 없음',
    filter: '필터',
    filterAll: '모든 메시지',
    filterTest: '테스트 메시지',
    filterAws: 'AWS 서비스',
    filterActivity: '활동',
    filterError: '오류'
  },
  interface: {
    title: '제어판',
    textInput: '텍스트 입력',
    enterText: '여기에 텍스트 입력...',
    dropdown: '드롭다운',
    option: '옵션',
    slider: '슬라이더',
    checkbox: '기능 활성화',
    radioGroup: '옵션 선택',
    action1: '작업 1',
    action2: '작업 2',
    action3: '작업 3'
  }
};

// Japanese translations
const jaTranslations = {
  connection: {
    connected: '接続済み',
    connecting: '接続中',
    disconnected: '切断',
    connectionLost: '接続が切れました',
    cannotReceiveMessages: '接続が切断されています。メッセージを受信できません。'
  },
  buttons: {
    refresh: '更新',
    retry: '再試行',
    clearConsole: 'コンソールをクリア',
    start: '開始',
    stop: '停止',
    test: 'テスト',
    reset: 'リセット',
    submit: '送信'
  },
  password: {
    title: 'アクセスパスワード',
    description: 'ダッシュボードにアクセスするにはパスワードを入力してください。',
    placeholder: 'パスワードを入力',
    submit: '確認',
    verifying: 'パスワードを確認中...',
    creating: 'パスワードを設定中...',
    error: {
      empty: 'パスワードを入力してください。',
      invalid: 'パスワードが正しくありません。',
      mismatch: 'パスワードが一致しません。',
      tooShort: 'パスワードは6文字以上である必要があります。',
      connectionRequired: 'サーバー接続が必要です。接続中...',
      connectionFailed: 'サーバーに接続できません。トラッカーアプリケーションが実行中か確認してください。',
      setup: 'パスワードの設定中にエラーが発生しました。'
    },
    setup: {
      title: 'パスワード設定',
      description: 'ダッシュボードアクセス用のパスワードを設定してください。',
      new: '新しいパスワード',
      confirm: 'パスワード確認',
      newPlaceholder: '新しいパスワードを入力（6文字以上）',
      confirmPlaceholder: 'パスワードを再入力',
      submit: 'パスワードを設定'
    }
  },
  download: {
    title: 'トラッカーアプリケーションのダウンロード (Currently unavailable: under development)',
    description: 'AWSサービスに接続するには、Studente AWSトラッカーアプリケーションをインストールする必要があります。',
    windows: 'Windows版をダウンロード'
  },  header: {
    language: '言語',
    about: '概要',
    license: 'ライセンス',
    logout: 'ログアウト'
  },
  aws: {
    instances: 'インスタンス',
    clusters: 'クラスター',
    services: 'サービス',
    noInstances: 'EC2インスタンスがありません',
    noClusters: '利用可能なクラスターがありません',
    noServices: '利用可能なサービスがありません'
  },
  activity: {
    keyboard: 'キーボード',
    mouseMovement: 'マウス移動',
    mouseClick: 'マウスクリック',
    screenChange: '画面変更',
    audio: 'オーディオ',
    title: 'アクティビティ',
    status: 'ステータス'
  },
  table: {
    name: '名前',
    id: 'ID',
    state: '状態',
    type: 'タイプ',
    zone: 'アベイラビリティゾーン',
    actions: 'アクション',
    notAvailable: '使用不可'
  },
  timer: {
    remainingSession: '残りセッション時間',
    hours: '時間',
    minutes: '分',
    seconds: '秒'
  },
  console: {
    noMessages: 'メッセージはまだ受信されていません。',
    selectMessagePrompt: 'メッセージを選択すると、ここに詳細が表示されます。',
    noTimestamp: 'タイムスタンプなし',
    filter: 'フィルター',
    filterAll: 'すべてのメッセージ',
    filterTest: 'テストメッセージ',
    filterAws: 'AWSサービス',
    filterActivity: 'アクティビティ',
    filterError: 'エラー'
  },
  interface: {
    title: 'コントロールパネル',
    textInput: 'テキスト入力',
    enterText: 'ここにテキストを入力...',
    dropdown: 'ドロップダウン',
    option: 'オプション',
    slider: 'スライダー',
    checkbox: '機能を有効にする',
    radioGroup: 'オプションを選択',
    action1: 'アクション 1',
    action2: 'アクション 2',
    action3: 'アクション 3'
  }
};

// Chinese translations
const zhTranslations = {
  connection: {
    connected: '已连接',
    connecting: '连接中',
    disconnected: '已断开',
    connectionLost: '连接已断开',
    cannotReceiveMessages: '连接已断开。无法接收消息。'
  },
  buttons: {
    refresh: '刷新',
    retry: '重试',
    clearConsole: '清除控制台',
    start: '启动',
    stop: '停止',
    test: '测试',
    reset: '重置',
    submit: '提交'
  },
  password: {
    title: '访问密码',
    description: '请输入密码以访问仪表板。',
    placeholder: '输入密码',
    submit: '确认',
    verifying: '验证密码中...',
    creating: '设置密码中...',
    error: {
      empty: '请输入密码。',
      invalid: '密码无效。',
      mismatch: '密码不匹配。',
      tooShort: '密码必须至少6个字符。',
      connectionRequired: '需要服务器连接。连接中...',
      connectionFailed: '无法连接到服务器。请确认跟踪应用程序正在运行。',
      setup: '设置密码时发生错误。'
    },
    setup: {
      title: '设置密码',
      description: '设置密码以访问仪表板。',
      new: '新密码',
      confirm: '确认密码',
      newPlaceholder: '输入新密码（至少6个字符）',
      confirmPlaceholder: '再次输入密码',
      submit: '设置密码'
    }
  },
  download: {
    title: '下载跟踪器应用程序 (Currently unavailable: under development)',
    description: '要连接到 AWS 服务，您需要安装 Studente AWS 跟踪器应用程序。',
    windows: '下载 Windows 版'
  },  header: {
    language: '语言',
    about: '关于',
    license: '许可证',
    logout: '退出登录'
  },
  aws: {
    instances: '实例',
    clusters: '集群',
    services: '服务',
    noInstances: '没有可用的EC2实例',
    noClusters: '没有可用的集群',
    noServices: '没有可用的服务'
  },
  activity: {
    keyboard: '键盘',
    mouseMovement: '鼠标移动',
    mouseClick: '鼠标点击',
    screenChange: '屏幕变化',
    audio: '音频',
    title: '活动',
    status: '状态'
  },
  table: {
    name: '名称',
    id: '标识',
    state: '状态',
    type: '类型',
    zone: '可用区',
    actions: '操作',
    notAvailable: '不可用'
  },
  timer: {
    remainingSession: '剩余会话时间',
    hours: '小时',
    minutes: '分钟',
    seconds: '秒'
  },
  console: {
    noMessages: '尚未收到消息。',
    selectMessagePrompt: '选择一条消息以在此处查看详细信息。',
    noTimestamp: '无时间戳',
    filter: '筛选',
    filterAll: '所有消息',
    filterTest: '测试消息',
    filterAws: 'AWS服务',
    filterActivity: '活动',
    filterError: '错误'
  },
  interface: {
    title: '控制面板',
    textInput: '文本输入',
    enterText: '在这里输入文本...',
    dropdown: '下拉菜单',
    option: '选项',
    slider: '滑块',
    checkbox: '启用功能',
    radioGroup: '选择一个选项',
    action1: '操作 1',
    action2: '操作 2',
    action3: '操作 3'
  }
};

// Initialize i18next
i18n
  .use(initReactI18next)
  .init({
    resources: {
      en: { translation: enTranslations },
      ko: { translation: koTranslations },
      ja: { translation: jaTranslations },
      zh: { translation: zhTranslations }
    },
    lng: 'en', // default language
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false, // react already safes from xss
    }
  });

export default i18n;