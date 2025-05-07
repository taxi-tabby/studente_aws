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
    stop: 'Stop'
  },
  header: {
    language: 'Language',
    about: 'About',
    license: 'License'
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
    stop: '중지'
  },
  header: {
    language: '언어',
    about: '소개',
    license: '라이선스'
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
    stop: '停止'
  },
  header: {
    language: '言語',
    about: '概要',
    license: 'ライセンス'
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
    stop: '停止'
  },
  header: {
    language: '语言',
    about: '关于',
    license: '许可证'
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