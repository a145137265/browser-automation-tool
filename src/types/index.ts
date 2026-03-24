import { Browser, BrowserContext, Page, BrowserType } from 'playwright';

/**
 * 浏览器类型枚举
 */
export enum BrowserTypeEnum {
  CHROMIUM = 'chromium',
  FIREFOX = 'firefox',
  WEBKIT = 'webkit'
}

/**
 * 支持的浏览器映射到 Playwright
 */
export const BrowserMapping: Record<BrowserTypeEnum, BrowserType<any>> = {
  [BrowserTypeEnum.CHROMIUM]: null as any,
  [BrowserTypeEnum.FIREFOX]: null as any,
  [BrowserTypeEnum.WEBKIT]: null as any
};

/**
 * 浏览器指纹配置
 */
export interface FingerprintConfig {
  userAgent?: string;
  viewport?: {
    width: number;
    height: number;
  };
  timezone?: string;
  locale?: string;
  language?: string;
  permissions?: string[];
  colorScheme?: 'light' | 'dark' | 'no-preference';
  deviceScaleFactor?: number;
  hasTouch?: boolean;
  isMobile?: boolean;
  referer?: string;
  extraHTTPHeaders?: Record<string, string>";
}

/**
 * 浏览器实例配置
 */
export interface BrowserInstanceConfig {
  id: string;
  type: BrowserTypeEnum;
  headless?: boolean;
  fingerprint?: FingerprintConfig;
  stealth?: boolean;
  proxy?: {
    server: string;
    username?: string;
    password?: string;
  };
  args?: string[];
  userDataDir?: string;
}

/**
 * 浏览器实例状态
 */
export interface BrowserInstanceState {
  id: string;
  type: BrowserTypeEnum;
  createdAt: Date;
  lastActiveAt: Date;
  status: 'created' | 'ready' | 'busy' | 'error' | 'closed';
  pageCount: number;
  contextCount: number;
}

/**
 * 会话数据
 */
export interface SessionData {
  id: string;
  name: string;
  browserId: string;
  cookies: any[];
  localStorage: Record<string, string>;
  sessionStorage: Record<string, string>;
  createdAt: Date;
  updatedAt: Date;
  metadata?: Record<string, any>;
}

/**
 * 性能指标
 */
export interface PerformanceMetrics {
  timestamp: Date;
  memoryUsage: NodeJS.MemoryUsage;
  cpuUsage: NodeJS.CpuUsage;
  browserMemory?: number;
  activePages: number;
  activeContexts: number;
}

/**
 * 批量操作任务
 */
export interface BatchTask {
  id: string;
  type: 'navigate' | 'screenshot' | 'click' | 'fill' | 'evaluate' | 'custom';
  browserIds: string[];
  params: any;
  status: 'pending' | 'running' | 'completed' | 'failed';
  results: Map<string, any>;
  createdAt: Date;
  completedAt?: Date;
  error?: string;
}

/**
 * API 请求/响应类型
 */
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface NavigateOptions {
  url: string;
  waitUntil?: 'load' | 'domcontentloaded' | 'networkidle' | 'commit';
  timeout?: number;
}

export interface ClickOptions {
  selector: string;
  options?: {
    button?: 'left' | 'right' | 'middle';
    modifiers?: ('Alt' | 'Control' | 'Meta' | 'Shift')[];
    position?: { x: number; y: number };
    delay?: number;
    force?: boolean;
  };
}

export interface FillOptions {
  selector: string;
  value: string;
}

export interface EvaluateOptions {
  script: string;
}

export interface ScreenshotOptions {
  fullPage?: boolean;
  type?: 'png' | 'jpeg';
  quality?: number;
  path?: string;
}

/**
 * 记录选项
 */
export interface RecordOptions {
  outputPath?: string;
  format?: 'mp4' | 'webm';
  fps?: number;
  videoCodec?: string;
}
