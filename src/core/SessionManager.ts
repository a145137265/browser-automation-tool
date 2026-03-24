import { BrowserContext, Page } from 'playwright';
import * as fs from 'fs';
import * as path from 'path';
import { v4 as uuidv4 } from 'uuid';
import winston from 'winston';
import { SessionData } from '../types';

/**
 * 会话管理器
 * 负责保存和恢复浏览器会话状态（Cookie、LocalStorage、SessionStorage）
 */
export class SessionManager {
  private sessions: Map<string, SessionData> = new Map();
  private storageDir: string;
  private logger: winston.Logger;
  private static instance: SessionManager;

  private constructor(storageDir: string = './sessions', logger?: winston.Logger) {
    this.storageDir = storageDir;
    this.logger = logger || winston.createLogger({
      level: 'info',
      format: winston.format.simple(),
      transports: [new winston.transports.Console()]
    });

    // 确保存储目录存在
    if (!fs.existsSync(this.storageDir)) {
      fs.mkdirSync(this.storageDir, { recursive: true });
    }
  }

  /**
   * 获取单例实例
   */
  static getInstance(storageDir?: string, logger?: winston.Logger): SessionManager {
    if (!SessionManager.instance) {
      SessionManager.instance = new SessionManager(storageDir, logger);
    }
    return SessionManager.instance;
  }

  /**
   * 从浏览器上下文保存会话
   */
  async saveSession(
    browserId: string,
    contextId: string,
    name: string,
    page: Page,
    metadata?: Record<string, any>
  ): Promise<SessionData> {
    const context = page.context();
    
    // 获取 Cookies
    const cookies = await context.cookies();
    
    // 获取 LocalStorage 和 SessionStorage
    const localStorage = await page.evaluate(() => {
      const data: Record<string, string> = {};
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key) {
          data[key] = localStorage.getItem(key) || '';
        }
      }
      return data;
    });

    const sessionStorage = await page.evaluate(() => {
      const data: Record<string, string> = {};
      for (let i = 0; i < sessionStorage.length; i++) {
        const key = sessionStorage.key(i);
        if (key) {
          data[key] = sessionStorage.getItem(key) || '';
        }
      }
      return data;
    });

    const sessionData: SessionData = {
      id: uuidv4(),
      name,
      browserId,
      cookies,
      localStorage,
      sessionStorage,
      createdAt: new Date(),
      updatedAt: new Date(),
      metadata
    };

    this.sessions.set(sessionData.id, sessionData);
    
    // 持久化到磁盘
    await this.persistSession(sessionData);
    
    this.logger.info(`保存会话: ${sessionData.name} (${sessionData.id})`);
    return sessionData;
  }

  /**
   * 从磁盘加载会话
   */
  async loadSession(sessionId: string): Promise<SessionData | null> {
    // 先从内存查找
    const inMemory = this.sessions.get(sessionId);
    if (inMemory) {
      return inMemory;
    }

    // 从磁盘加载
    const filePath = path.join(this.storageDir, `${sessionId}.json`);
    if (fs.existsSync(filePath)) {
      try {
        const data = fs.readFileSync(filePath, 'utf-8');
        const sessionData = JSON.parse(data) as SessionData;
        sessionData.createdAt = new Date(sessionData.createdAt);
        sessionData.updatedAt = new Date(sessionData.updatedAt);
        this.sessions.set(sessionId, sessionData);
        return sessionData;
      } catch (error) {
        this.logger.error(`加载会话失败: ${sessionId}`, error);
        return null;
      }
    }

    return null;
  }

  /**
   * 将会话应用到浏览器上下文
   */
  async applySession(page: Page, sessionId: string): Promise<boolean> {
    const session = await this.loadSession(sessionId);
    if (!session) {
      this.logger.error(`会话不存在: ${sessionId}`);
      return false;
    }

    const context = page.context();

    try {
      // 恢复 Cookies
      if (session.cookies && session.cookies.length > 0) {
        await context.addCookies(session.cookies);
        this.logger.info(`恢复 ${session.cookies.length} 个 Cookies`);
      }

      // 恢复 LocalStorage
      if (session.localStorage && Object.keys(session.localStorage).length > 0) {
        await page.evaluate((storage) => {
          for (const [key, value] of Object.entries(storage)) {
            localStorage.setItem(key, value);
          }
        }, session.localStorage);
        this.logger.info(`恢复 LocalStorage: ${Object.keys(session.localStorage).length} 项`);
      }

      // 恢复 SessionStorage
      if (session.sessionStorage && Object.keys(session.sessionStorage).length > 0) {
        await page.evaluate((storage) => {
          for (const [key, value] of Object.entries(storage)) {
            sessionStorage.setItem(key, value);
          }
        }, session.sessionStorage);
        this.logger.info(`恢复 SessionStorage: ${Object.keys(session.sessionStorage).length} 项`);
      }

      this.logger.info(`应用会话成功: ${session.name}`);
      return true;
    } catch (error) {
      this.logger.error(`应用会话失败: ${sessionId}`, error);
      return false;
    }
  }

  /**
   * 持久化会话到磁盘
   */
  private async persistSession(session: SessionData): Promise<void> {
    const filePath = path.join(this.storageDir, `${session.id}.json`);
    const data = JSON.stringify(session, null, 2);
    fs.writeFileSync(filePath, data, 'utf-8');
  }

  /**
   * 删除会话
   */
  async deleteSession(sessionId: string): Promise<boolean> {
    // 从内存删除
    this.sessions.delete(sessionId);

    // 从磁盘删除
    const filePath = path.join(this.storageDir, `${sessionId}.json`);
    if (fs.existsSync(filePath)) {
      fs.unlinkSync(filePath);
      this.logger.info(`删除会话: ${sessionId}`);
      return true;
    }

    return false;
  }

  /**
   * 列出所有会话
   */
  listSessions(): SessionData[] {
    const sessions: SessionData[] = [];
    
    // 读取磁盘上的所有会话文件
    const files = fs.readdirSync(this.storageDir);
    for (const file of files) {
      if (file.endsWith('.json')) {
        try {
          const data = fs.readFileSync(path.join(this.storageDir, file), 'utf-8');
          sessions.push(JSON.parse(data));
        } catch (error) {
          this.logger.warn(`读取会话文件失败: ${file}`);
        }
      }
    }

    return sessions.sort((a, b) => 
      new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
    );
  }

  /**
   * 获取会话信息
   */
  getSession(sessionId: string): SessionData | undefined {
    return this.sessions.get(sessionId);
  }

  /**
   * 更新会话元数据
   */
  async updateSessionMetadata(sessionId: string, metadata: Record<string, any>): Promise<boolean> {
    const session = await this.loadSession(sessionId);
    if (!session) {
      return false;
    }

    session.metadata = { ...session.metadata, ...metadata };
    session.updatedAt = new Date();
    
    this.sessions.set(sessionId, session);
    await this.persistSession(session);
    
    return true;
  }

  /**
   * 导出会话（可用于迁移）
   */
  exportSession(sessionId: string): string | null {
    const session = this.sessions.get(sessionId);
    if (!session) {
      // 尝试从磁盘加载
      const filePath = path.join(this.storageDir, `${sessionId}.json`);
      if (fs.existsSync(filePath)) {
        return fs.readFileSync(filePath, 'utf-8');
      }
      return null;
    }
    return JSON.stringify(session, null, 2);
  }

  /**
   * 导入会话
   */
  async importSession(jsonData: string): Promise<SessionData | null> {
    try {
      const session = JSON.parse(jsonData) as SessionData;
      session.id = uuidv4(); // 生成新的 ID
      session.createdAt = new Date();
      session.updatedAt = new Date();
      
      this.sessions.set(session.id, session);
      await this.persistSession(session);
      
      this.logger.info(`导入会话: ${session.name} (${session.id})`);
      return session;
    } catch (error) {
      this.logger.error('导入会话失败:', error);
      return null;
    }
  }

  /**
   * 清理过期会话
   */
  cleanExpiredSessions(maxAgeDays: number = 30): number {
    const cutoff = new Date();
    cutoff.setDate(cutoff.getDate() - maxAgeDays);
    
    let cleaned = 0;
    const sessions = this.listSessions();
    
    for (const session of sessions) {
      if (new Date(session.updatedAt) < cutoff) {
        this.deleteSession(session.id);
        cleaned++;
      }
    }

    this.logger.info(`清理了 ${cleaned} 个过期会话`);
    return cleaned;
  }
}

export default SessionManager;
