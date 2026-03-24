import * as os from 'os';
import { Page } from 'playwright';
import winston from 'winston';
import { PerformanceMetrics } from '../types';

/**
 * 性能监控器
 * 监控浏览器和系统的性能指标
 */
export class PerformanceMonitor {
  private logger: winston.Logger;
  private metricsHistory: PerformanceMetrics[] = [];
  private maxHistorySize: number;
  private monitorInterval: NodeJS.Timeout | null = null;
  private static instance: PerformanceMonitor;

  private constructor(maxHistorySize: number = 1000, logger?: winston.Logger) {
    this.maxHistorySize = maxHistorySize;
    this.logger = logger || winston.createLogger({
      level: 'info',
      format: winston.format.simple(),
      transports: [new winston.transports.Console()]
    });
  }

  /**
   * 获取单例实例
   */
  static getInstance(maxHistorySize?: number, logger?: winston.Logger): PerformanceMonitor {
    if (!PerformanceMonitor.instance) {
      PerformanceMonitor.instance = new PerformanceMonitor(maxHistorySize, logger);
    }
    return PerformanceMonitor.instance;
  }

  /**
   * 获取系统性能指标
   */
  getSystemMetrics(): PerformanceMetrics {
    const memUsage = process.memoryUsage();
    const cpuUsage = process.cpuUsage();

    return {
      timestamp: new Date(),
      memoryUsage: memUsage,
      cpuUsage,
      activePages: 0,
      activeContexts: 0
    };
  }

  /**
   * 获取页面性能指标
   */
  async getPageMetrics(page: Page): Promise<any> {
    try {
      const metrics = await page.evaluate(() => {
        const timing = performance.timing;
        const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
        
        return {
          // 页面加载时间
          loadTime: timing.loadEventEnd - timing.navigationStart,
          domReadyTime: timing.domContentLoadedEventEnd - timing.navigationStart,
          firstPaint: performance.getEntriesByType('paint')[0]?.startTime || 0,
          firstContentfulPaint: performance.getEntriesByType('paint')[1]?.startTime || 0,
          
          // 资源信息
          resources: performance.getEntriesByType('resource').length,
          
          // 内存信息（仅部分浏览器支持）
          memory: (performance as any).memory ? {
            usedJSHeapSize: (performance as any).memory.usedJSHeapSize,
            totalJSHeapSize: (performance as any).memory.totalJSHeapSize,
            jsHeapSizeLimit: (performance as any).memory.jsHeapSizeLimit
          } : null,
          
          // 网络状态
          connection: (navigator as any).connection ? {
            effectiveType: (navigator as any).connection.effectiveType,
            downlink: (navigator as any).connection.downlink,
            rtt: (navigator as any).connection.rtt
          } : null
        };
      });

      return metrics;
    } catch (error) {
      this.logger.error('获取页面性能指标失败:', error);
      return null;
    }
  }

  /**
   * 获取浏览器内存使用情况（通过 CDP）
   */
  async getBrowserMemory(page: Page): Promise<number | null> {
    try {
      const client = await page.context().newCDPSession(page);
      const result = await client.send('Runtime.evaluate', {
        expression: 'performance.memory.usedJSHeapSize',
        returnByValue: true
      });
      await client.detach();
      
      if (result && result.result && result.result.value) {
        return result.result.value;
      }
      return null;
    } catch {
      // CDP 不可用时返回 null
      return null;
    }
  }

  /**
   * 记录系统性能指标
   */
  recordMetrics(activeBrowsers: number = 0, activeContexts: number = 0): PerformanceMetrics {
    const metrics: PerformanceMetrics = {
      timestamp: new Date(),
      memoryUsage: process.memoryUsage(),
      cpuUsage: process.cpuUsage(),
      activePages: activeBrowsers,
      activeContexts
    };

    this.metricsHistory.push(metrics);

    // 限制历史记录大小
    if (this.metricsHistory.length > this.maxHistorySize) {
      this.metricsHistory.shift();
    }

    return metrics;
  }

  /**
   * 开始定期监控
   */
  startMonitoring(intervalMs: number = 5000, getActiveCounts?: () => { pages: number; contexts: number }): void {
    if (this.monitorInterval) {
      this.stopMonitoring();
    }

    this.monitorInterval = setInterval(() => {
      const counts = getActiveCounts ? getActiveCounts() : { pages: 0, contexts: 0 };
      this.recordMetrics(counts.pages, counts.contexts);
    }, intervalMs);

    this.logger.info(`性能监控已启动，间隔: ${intervalMs}ms`);
  }

  /**
   * 停止定期监控
   */
  stopMonitoring(): void {
    if (this.monitorInterval) {
      clearInterval(this.monitorInterval);
      this.monitorInterval = null;
      this.logger.info('性能监控已停止');
    }
  }

  /**
   * 获取性能统计摘要
   */
  getSummary(): {
    current: PerformanceMetrics | null;
    history: PerformanceMetrics[];
    averageMemory: number;
    peakMemory: number;
    uptime: number;
  } {
    const history = this.metricsHistory;
    
    if (history.length === 0) {
      return {
        current: null,
        history: [],
        averageMemory: 0,
        peakMemory: 0,
        uptime: process.uptime()
      };
    }

    const current = history[history.length - 1];
    const memoryValues = history.map(m => m.memoryUsage.heapUsed);
    const avgMemory = memoryValues.reduce((a, b) => a + b, 0) / memoryValues.length;
    const peakMemory = Math.max(...memoryValues);

    return {
      current,
      history: history.slice(-100), // 最近 100 条
      averageMemory: avgMemory,
      peakMemory,
      uptime: process.uptime()
    };
  }

  /**
   * 获取性能历史数据
   */
  getHistory(limit?: number): PerformanceMetrics[] {
    if (limit) {
      return this.metricsHistory.slice(-limit);
    }
    return [...this.metricsHistory];
  }

  /**
   * 清理历史数据
   */
  clearHistory(): void {
    this.metricsHistory = [];
    this.logger.info('性能历史数据已清理');
  }

  /**
   * 检查是否处于高负载状态
   */
  isHighLoad(thresholdMB: number = 500): boolean {
    const current = this.metricsHistory[this.metricsHistory.length - 1];
    if (!current) return false;
    
    const heapUsedMB = current.memoryUsage.heapUsed / 1024 / 1024;
    return heapUsedMB > thresholdMB;
  }

  /**
   * 获取系统信息
   */
  getSystemInfo() {
    return {
      platform: os.platform(),
      arch: os.arch(),
      cpus: os.cpus().length,
      totalMemory: os.totalmem(),
      freeMemory: os.freemem(),
      homedir: os.homedir(),
      hostname: os.hostname(),
      type: os.type(),
      version: os.version()
    };
  }
}

export default PerformanceMonitor;
