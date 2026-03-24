import { chromium, firefox, webkit, Browser, BrowserContext, BrowserType, Page, LaunchOptions, ContextOptions } from 'playwright';
import { v4 as uuidv4 } from 'uuid';
import * as fs from 'fs';
import * as path from 'path';
import winston from 'winston';
import { BrowserInstanceConfig, BrowserInstanceState, BrowserTypeEnum, FingerprintConfig, SessionData } from '../types';
import { FingerprintGenerator } from './FingerprintGenerator';

/**
 * 浏览器实例封装
 */
class BrowserInstance {
  public id: string;
  public browser: Browser | null = null;
  public contexts: Map<string, BrowserContext> = new Map();
  public pages: Map<string, Page[]> = new Map();
  public config: BrowserInstanceConfig;
  public state: BrowserInstanceState;
  private logger: winston.Logger;

  constructor(config: BrowserInstanceConfig, logger: winston.Logger) {
    this.id = config.id || uuidv4();
    this.config = config;
    this.logger = logger;
    this.state = {
      id: this.id,
      type: config.type,
      createdAt: new Date(),
      lastActiveAt: new Date(),
      status: 'created',
      pageCount: 0,
      contextCount: 0
    };
  }

  /**
   * 获取 BrowserType
   */
  private getBrowserType(): BrowserType<Browser> {
    switch (this.config.type) {
      case BrowserTypeEnum.CHROMIUM:
        return chromium;
      case BrowserTypeEnum.FIREFOX:
        return firefox;
      case BrowserTypeEnum.WEBKIT:
        return webkit;
      default:
        return chromium;
    }
  }

  /**
   * 启动浏览器
   */
  async launch(): Promise<void> {
    try {
      const browserType = this.getBrowserType();
      const launchOptions: LaunchOptions = {
        headless: this.config.headless ?? true,
        args: [
          '--disable-blink-features=AutomationControlled',
          '--disable-dev-shm-usage',
          '--no-sandbox',
          '--disable-setuid-sandbox',
          '--disable-web-security',
          ...(this.config.args || [])
        ]
      };

      // 添加代理配置
      if (this.config.proxy) {
        launchOptions.proxy = {
          server: this.config.proxy.server
        };
      }

      // 使用已有用户数据目录或创建新的
      if (this.config.userDataDir) {
        launchOptions.userDataDir = this.config.userDataDir;
      }

      this.browser = await browserType.launch(launchOptions);
      this.state.status = 'ready';
      this.logger.info(`浏览器实例 ${this.id} 启动成功`);
    } catch (error) {
      this.state.status = 'error';
      this.logger.error(`浏览器实例 ${this.id} 启动失败:`, error);
      throw error;
    }
  }

  /**
   * 创建浏览器上下文
   */
  async createContext(fingerprint?: FingerprintConfig, contextId?: string): Promise<BrowserContext> {
    if (!this.browser) {
      throw new Error('浏览器未启动');
    }

    const id = contextId || uuidv4();
    const fp = fingerprint || this.config.fingerprint || FingerprintGenerator.generate(this.config.type);

    const contextOptions: ContextOptions = {
      viewport: fp.viewport,
      userAgent: fp.userAgent,
      locale: fp.locale,
      timezoneId: fp.timezone,
      colorScheme: fp.colorScheme,
      deviceScaleFactor: fp.deviceScaleFactor,
      isMobile: fp.isMobile || false,
      hasTouch: fp.hasTouch || false,
      permissions: fp.permissions,
      extraHTTPHeaders: fp.extraHTTPHeaders,
      ignoreHTTPSErrors: true
    };

    // 代理配置
    if (this.config.proxy) {
      contextOptions.proxy = {
        server: this.config.proxy.server,
        username: this.config.proxy.username,
        password: this.config.proxy.password
      };
    }

    const context = await this.browser.newContext(contextOptions);
    this.contexts.set(id, context);
    this.pages.set(id, []);
    this.state.contextCount = this.contexts.size;
    this.state.lastActiveAt = new Date();

    this.logger.info(`创建浏览器上下文 ${id}`);
    return context;
  }

  /**
   * 在指定上下文中创建页面
   */
  async createPage(contextId: string): Promise<Page> {
    const context = this.contexts.get(contextId);
    if (!context) {
      throw new Error(`上下文 ${contextId} 不存在`);
    }

    const page = await context.newPage();
    const pages = this.pages.get(contextId) || [];
    pages.push(page);
    this.pages.set(contextId, pages);
    this.state.pageCount = this.pages.get(contextId)?.length || 0;
    this.state.lastActiveAt = new Date();

    return page;
  }

  /**
   * 获取指定上下文的所有页面
   */
  getPages(contextId: string): Page[] {
    return this.pages.get(contextId) || [];
  }

  /**
   * 获取指定上下文
   */
  getContext(contextId: string): BrowserContext | undefined {
    return this.contexts.get(contextId);
  }

  /**
   * 关闭指定上下文
   */
  async closeContext(contextId: string): Promise<void> {
    const context = this.contexts.get(contextId);
    if (context) {
      const pages = this.pages.get(contextId) || [];
      for (const page of pages) {
        await page.close();
      }
      await context.close();
      this.contexts.delete(contextId);
      this.pages.delete(contextId);
      this.state.contextCount = this.contexts.size;
      this.logger.info(`关闭浏览器上下文 ${contextId}`);
    }
  }

  /**
   * 关闭浏览器实例
   */
  async close(): Promise<void> {
    // 关闭所有上下文
    for (const contextId of this.contexts.keys()) {
      await this.closeContext(contextId);
    }

    if (this.browser) {
      await this.browser.close();
      this.browser = null;
    }

    this.state.status = 'closed';
    this.logger.info(`浏览器实例 ${this.id} 已关闭`);
  }

  /**
   * 获取浏览器实例状态
   */
  getState(): BrowserInstanceState {
    return { ...this.state };
  }

  /**
   * 检查浏览器是否正常
   */
  async isHealthy(): Promise<boolean> {
    if (!this.browser || this.state.status === 'closed') {
      return false;
    }

    try {
      const contexts = this.browser.contexts();
      // 简单检查浏览器连接
      return contexts !== undefined;
    } catch {
      return false;
    }
  }
}

/**
 * 浏览器管理器
 * 统一管理多个浏览器实例
 */
export class BrowserManager {
  private instances: Map<string, BrowserInstance> = new Map();
  private logger: winston.Logger;
  private static instance: BrowserManager;

  private constructor(logger?: winston.Logger) {
    this.logger = logger || winston.createLogger({
      level: 'info',
      format: winston.format.simple(),
      transports: [new winston.transports.Console()]
    });
  }

  /**
   * 获取单例实例
   */
  static getInstance(logger?: winston.Logger): BrowserManager {
    if (!BrowserManager.instance) {
      BrowserManager.instance = new BrowserManager(logger);
    }
    return BrowserManager.instance;
  }

  /**
   * 创建浏览器实例
   */
  async createInstance(config: BrowserInstanceConfig): Promise<string> {
    const instance = new BrowserInstance(config, this.logger);
    await instance.launch();
    this.instances.set(instance.id, instance);
    this.logger.info(`创建浏览器实例: ${instance.id} (${config.type})`);
    return instance.id;
  }

  /**
   * 获取浏览器实例
   */
  getInstance(id: string): BrowserInstance | undefined {
    return this.instances.get(id);
  }

  /**
   * 获取所有实例
   */
  getAllInstances(): BrowserInstanceState[] {
    return Array.from(this.instances.values()).map(inst => inst.getState());
  }

  /**
   * 关闭指定实例
   */
  async closeInstance(id: string): Promise<void> {
    const instance = this.instances.get(id);
    if (instance) {
      await instance.close();
      this.instances.delete(id);
      this.logger.info(`关闭浏览器实例: ${id}`);
    }
  }

  /**
   * 关闭所有实例
   */
  async closeAll(): Promise<void> {
    for (const id of this.instances.keys()) {
      await this.closeInstance(id);
    }
  }

  /**
   * 重新启动指定实例
   */
  async restartInstance(id: string): Promise<void> {
    const instance = this.instances.get(id);
    if (instance) {
      const config = instance.config;
      await instance.close();
      await this.createInstance(config);
      this.logger.info(`重启浏览器实例: ${id}`);
    }
  }

  /**
   * 检查所有实例健康状态
   */
  async healthCheck(): Promise<Map<string, boolean>> {
    const results = new Map<string, boolean>();
    for (const [id, instance] of this.instances.entries()) {
      results.set(id, await instance.isHealthy());
    }
    return results;
  }

  /**
   * 获取实例统计信息
   */
  getStats() {
    const stats = {
      totalInstances: this.instances.size,
      instances: [] as any[]
    };

    for (const [id, instance] of this.instances.entries()) {
      const state = instance.getState();
      stats.instances.push({
        id: state.id,
        type: state.type,
        status: state.status,
        contexts: state.contextCount,
        pages: state.pageCount,
        createdAt: state.createdAt,
        lastActiveAt: state.lastActiveAt
      });
    }

    return stats;
  }
}

export default BrowserManager;
