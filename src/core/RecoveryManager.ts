import { Browser, BrowserContext, Page } from 'playwright';
import winston from 'winston';
import { BrowserTypeEnum, BrowserInstanceConfig } from '../types';
import { BrowserManager } from './BrowserManager';

/**
 * 恢复策略类型
 */
export enum RecoveryStrategy {
  RESTART_BROWSER = 'restart_browser',
  RESTART_CONTEXT = 'restart_context',
  REFRESH_PAGE = 'refresh_page',
  RECREATE_PAGE = 'recreate_page',
  IGNORE = 'ignore'
}

/**
 * 异常信息
 */
export interface ExceptionInfo {
  error: Error;
  context: string;
  timestamp: Date;
  recoverable: boolean;
}

/**
 * 恢复配置
 */
export interface RecoveryConfig {
  maxRetries: number;
  retryDelay: number;
  enableAutoRecovery: boolean;
  strategies: RecoveryStrategy[];
}

/**
 * 异常恢复管理器
 * 自动检测并恢复浏览器异常
 */
export class RecoveryManager {
  private logger: winston.Logger;
  private browserManager: BrowserManager;
  private errorHistory: ExceptionInfo[] = new Map();
  private config: RecoveryConfig;
  private static instance: RecoveryManager;

  private constructor(
    browserManager: BrowserManager,
    config?: Partial<RecoveryConfig>,
    logger?: winston.Logger
  ) {
    this.browserManager = browserManager;
    this.config = {
      maxRetries: config?.maxRetries ?? 3,
      retryDelay: config?.retryDelay ?? 2000,
      enableAutoRecovery: config?.enableAutoRecovery ?? true,
      strategies: config?.strategies ?? [
        RecoveryStrategy.REFRESH_PAGE,
        RecoveryStrategy.RECREATE_PAGE,
        RecoveryStrategy.RESTART_CONTEXT,
        RecoveryStrategy.RESTART_BROWSER
      ]
    };

    this.logger = logger || winston.createLogger({
      level: 'info',
      format: winston.format.simple(),
      transports: [new winston.transports.Console()]
    });
  }

  /**
   * 获取单例实例
   */
  static getInstance(browserManager: BrowserManager, config?: Partial<RecoveryConfig>, logger?: winston.Logger): RecoveryManager {
    if (!RecoveryManager.instance) {
      RecoveryManager.instance = new RecoveryManager(browserManager, config, logger);
    }
    return RecoveryManager.instance;
  }

  /**
   * 记录异常
   */
  recordError(context: string, error: Error, recoverable: boolean = true): void {
    const info: ExceptionInfo = {
      error,
      context,
      timestamp: new Date(),
      recoverable
    };
    
    // 记录到错误历史
    const key = `${context}_${Date.now()}`;
    this.errorHistory.push(info);
    
    // 限制历史大小
    if (this.errorHistory.length > 1000) {
      this.errorHistory.shift();
    }

    this.logger.warn(`捕获异常 [${context}]: ${error.message}`);
  }

  /**
   * 判断错误是否可恢复
   */
  isRecoverable(error: Error): boolean {
    const errorMessages = [
      'Target closed',
      'Browser closed',
      'Context closed',
      'Page closed',
      'Navigation failed',
      'Timeout',
      'net::ERR_',
      'Protocol error',
      'Execution context was destroyed'
    ];

    const errorStr = error.message || error.toString();
    return errorMessages.some(msg => errorStr.includes(msg));
  }

  /**
   * 执行恢复策略
   */
  async executeRecovery(
    browserId: string,
    contextId: string,
    page: Page,
    strategy: RecoveryStrategy
  ): Promise<boolean> {
    try {
      switch (strategy) {
        case RecoveryStrategy.REFRESH_PAGE:
          this.logger.info(`执行策略: 刷新页面`);
          await page.reload({ waitUntil: 'domcontentloaded' });
          return true;

        case RecoveryStrategy.RECREATE_PAGE:
          this.logger.info(`执行策略: 重新创建页面`);
          const instance = this.browserManager.getInstance(browserId);
          if (instance) {
            const context = instance.getContext(contextId);
            if (context) {
              await page.close();
              await instance.createPage(contextId);
              return true;
            }
          }
          return false;

        case RecoveryStrategy.RESTART_CONTEXT:
          this.logger.info(`执行策略: 重启上下文`);
          const inst = this.browserManager.getInstance(browserId);
          if (inst) {
            await inst.closeContext(contextId);
            await inst.createContext(undefined, contextId);
            await inst.createPage(contextId);
            return true;
          }
          return false;

        case RecoveryStrategy.RESTART_BROWSER:
          this.logger.info(`执行策略: 重启浏览器`);
          await this.browserManager.restartInstance(browserId);
          return true;

        case RecoveryStrategy.IGNORE:
          this.logger.info(`执行策略: 忽略错误`);
          return true;

        default:
          return false;
      }
    } catch (error) {
      this.logger.error(`恢复策略执行失败: ${strategy}`, error);
      return false;
    }
  }

  /**
   * 尝试自动恢复
   */
  async tryAutoRecovery(
    browserId: string,
    contextId: string,
    page: Page,
    error: Error
  ): Promise<{ success: boolean; finalStrategy: RecoveryStrategy | null }> {
    if (!this.config.enableAutoRecovery) {
      return { success: false, finalStrategy: null };
    }

    // 检查是否可恢复
    if (!this.isRecoverable(error)) {
      this.logger.warn('错误不可恢复');
      return { success: false, finalStrategy: null };
    }

    // 遍历恢复策略
    for (const strategy of this.config.strategies) {
      this.logger.info(`尝试恢复策略: ${strategy}`);
      
      const success = await this.executeRecovery(browserId, contextId, page, strategy);
      
      if (success) {
        this.logger.info(`恢复成功: ${strategy}`);
        return { success: true, finalStrategy: strategy };
      }

      // 等待后重试下一个策略
      await new Promise(resolve => setTimeout(resolve, this.config.retryDelay));
    }

    this.logger.error('所有恢复策略均失败');
    return { success: false, finalStrategy: null };
  }

  /**
   * 带重试的页面操作
   */
  async withRetry<T>(
    operation: () => Promise<T>,
    context: string,
    maxRetries: number = this.config.maxRetries
  ): Promise<T> {
    let lastError: Error | null = null;

    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        return await operation();
      } catch (error) {
        lastError = error as Error;
        this.recordError(context, lastError, this.isRecoverable(lastError));
        
        if (attempt < maxRetries) {
          this.logger.info(`重试 ${attempt}/${maxRetries}: ${lastError.message}`);
          await new Promise(resolve => setTimeout(resolve, this.config.retryDelay));
        }
      }
    }

    throw lastError;
  }

  /**
   * 获取错误历史统计
   */
  getErrorStats(): {
    total: number;
    recent: ExceptionInfo[];
    byContext: Record<string, number>;
    recoverable: number;
  } {
    const recent = this.errorHistory.slice(-100);
    const byContext: Record<string, number> = {};
    let recoverable = 0;

    for (const error of this.errorHistory) {
      byContext[error.context] = (byContext[error.context] || 0) + 1;
      if (error.recoverable) recoverable++;
    }

    return {
      total: this.errorHistory.length,
      recent,
      byContext,
      recoverable
    };
  }

  /**
   * 清理错误历史
   */
  clearErrorHistory(): void {
    this.errorHistory = [];
    this.logger.info('错误历史已清理');
  }

  /**
   * 设置配置
   */
  setConfig(config: Partial<RecoveryConfig>): void {
    this.config = { ...this.config, ...config };
  }
}

export default RecoveryManager;
