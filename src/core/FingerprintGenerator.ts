import { FingerprintConfig, BrowserTypeEnum } from '../types';
import { v4 as uuidv4 } from 'uuid';

/**
 * 浏览器指纹生成器
 * 用于生成随机的浏览器指纹配置，模拟真实用户环境
 */
export class FingerprintGenerator {
  // 常见分辨率
  private static readonly VIEWPORTS = [
    { width: 1920, height: 1080 },
    { width: 1366, height: 768 },
    { width: 1536, height: 864 },
    { width: 1440, height: 900 },
    { width: 1280, height: 720 },
    { width: 2560, height: 1440 },
    { width: 3840, height: 2160 }
  ];

  // 常见 User-Agent
  private static readonly USER_AGENTS = {
    chromium: [
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
      'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
      'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    ],
    firefox: [
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
      'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0',
      'Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0'
    ],
    webkit: [
      'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
      'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1'
    ]
  };

  // 常用时区
  private static readonly TIMEZONES = [
    'America/New_York',
    'America/Los_Angeles',
    'America/Chicago',
    'Europe/London',
    'Europe/Paris',
    'Europe/Berlin',
    'Asia/Tokyo',
    'Asia/Shanghai',
    'Asia/Singapore',
    'Australia/Sydney'
  ];

  // 常用语言环境
  private static readonly LOCALES = [
    'en-US',
    'en-GB',
    'zh-CN',
    'zh-TW',
    'ja-JP',
    'ko-KR',
    'de-DE',
    'fr-FR',
    'es-ES',
    'pt-BR'
  ];

  /**
   * 生成随机指纹配置
   */
  static generate(type: BrowserTypeEnum = BrowserTypeEnum.CHROMIUM, customConfig?: Partial<FingerprintConfig>): FingerprintConfig {
    const viewport = this.getRandomItem(this.VIEWPORTS);
    const userAgents = this.USER_AGENTS[type] || this.USER_AGENTS.chromium;
    
    const config: FingerprintConfig = {
      viewport,
      userAgent: this.getRandomItem(userAgents),
      timezone: this.getRandomItem(this.TIMEZONES),
      locale: this.getRandomItem(this.LOCALES),
      language: this.getRandomItem(this.LOCALES).split('-')[0],
      colorScheme: this.getRandomItem(['light', 'dark', 'no-preference'] as const),
      deviceScaleFactor: this.getRandomItem([1, 1.25, 1.5, 2, 3]),
      permissions: ['geolocation', 'notifications', 'camera', 'microphone'],
      referer: 'https://www.google.com/'
    };

    // 合并自定义配置
    if (customConfig) {
      Object.assign(config, customConfig);
    }

    return config;
  }

  /**
   * 生成特定的指纹配置（用于测试反检测）
   */
  static generateStealth(): FingerprintConfig {
    return {
      viewport: { width: 1920, height: 1080 },
      userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
      timezone: 'Asia/Shanghai',
      locale: 'zh-CN',
      language: 'zh-CN',
      colorScheme: 'light',
      deviceScaleFactor: 1,
      permissions: [],
      referer: 'https://www.google.com/'
    };
  }

  /**
   * 生成移动端指纹
   */
  static generateMobile(type: BrowserTypeEnum = BrowserTypeEnum.CHROMIUM): FingerprintConfig {
    const mobileViewports = [
      { width: 390, height: 844 },  // iPhone 14
      { width: 412, height: 915 },  // Pixel 7
      { width: 375, height: 812 },  // iPhone X
      { width: 360, height: 800 },  // Samsung Galaxy
      { width: 414, height: 896 }   // iPhone 11
    ];
    
    const viewport = this.getRandomItem(mobileViewports);
    const userAgents = type === BrowserTypeEnum.WEBKIT 
      ? ['Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1']
      : ['Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36'];

    return {
      viewport,
      userAgent: this.getRandomItem(userAgents),
      timezone: 'Asia/Shanghai',
      locale: 'zh-CN',
      language: 'zh-CN',
      isMobile: true,
      hasTouch: true,
      deviceScaleFactor: type === BrowserTypeEnum.WEBKIT ? 3 : 2.625,
      colorScheme: 'light'
    };
  }

  /**
   * 从数组中随机获取一项
   */
  private static getRandomItem<T>(arr: T[]): T {
    return arr[Math.floor(Math.random() * arr.length)];
  }

  /**
   * 生成用于特定网站的指纹（可自定义优化）
   */
  static generateForSite(site: string): FingerprintConfig {
    // 根据目标网站类型优化指纹
    if (site.includes('google')) {
      return {
        viewport: { width: 1920, height: 1080 },
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        timezone: 'America/New_York',
        locale: 'en-US',
        language: 'en-US',
        colorScheme: 'light',
        deviceScaleFactor: 1,
        permissions: []
      };
    }
    
    if (site.includes('taobao') || site.includes('tmall') || site.includes('alibaba')) {
      return {
        viewport: { width: 1920, height: 1080 },
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        timezone: 'Asia/Shanghai',
        locale: 'zh-CN',
        language: 'zh-CN',
        colorScheme: 'light',
        deviceScaleFactor: 1,
        permissions: []
      };
    }

    return this.generate(BrowserTypeEnum.CHROMIUM);
  }
}

export default FingerprintGenerator;
