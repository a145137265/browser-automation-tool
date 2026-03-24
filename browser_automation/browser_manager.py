"""
浏览器管理器 - 多实例管理
Browser Manager - Multi-instance Management
"""

import asyncio
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import json
import os

try:
    from playwright.async_api import async_playwright, Browser, BrowserContext, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("Warning: Playwright not installed. Install with: pip install playwright && playwright install")


@dataclass
class BrowserInstance:
    """浏览器实例"""
    instance_id: str
    name: str
    browser: Optional[Browser] = None
    context: Optional[BrowserContext] = None
    page: Optional[Page] = None
    fingerprint: Dict[str, Any] = field(default_factory=dict)
    cookies: List[Dict] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)
    custom_args: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            'instance_id': self.instance_id,
            'name': self.name,
            'fingerprint': self.fingerprint,
            'cookies': self.cookies,
            'created_at': self.created_at.isoformat(),
            'tags': self.tags,
            'custom_args': self.custom_args
        }


class BrowserManager:
    """
    浏览器管理器
    支持多实例管理、指纹定制、代理配置
    """
    
    def __init__(self, playwright=None):
        self.playwright = playwright
        self.instances: Dict[str, BrowserInstance] = {}
        self._is_initialized = False
    
    async def initialize(self):
        """初始化浏览器管理器"""
        if not PLAYWRIGHT_AVAILABLE:
            raise RuntimeError("Playwright is not installed")
        
        if not self._is_initialized:
            self.playwright = await async_playwright().start()
            self._is_initialized = True
    
    async def close(self):
        """关闭所有浏览器实例"""
        for instance in self.instances.values():
            await self.close_instance(instance.instance_id)
        
        if self.playwright:
            await self.playwright.stop()
            self._is_initialized = False
    
    def create_instance(
        self,
        name: str,
        fingerprint: Optional[Dict] = None,
        proxy: Optional[str] = None,
        headless: bool = False,
        tags: Optional[List[str]] = None,
        custom_args: Optional[List[str]] = None
    ) -> BrowserInstance:
        """
        创建新的浏览器实例
        
        Args:
            name: 实例名称
            fingerprint: 指纹配置
            proxy: 代理服务器地址 (如: "http://proxy:port" 或 "socks5://proxy:port")
            headless: 是否无头模式
            tags: 实例标签
            custom_args: 自定义浏览器参数
        
        Returns:
            BrowserInstance: 浏览器实例对象
        """
        instance_id = str(uuid.uuid4())[:8]
        instance = BrowserInstance(
            instance_id=instance_id,
            name=name,
            fingerprint=fingerprint or {},
            tags=tags or [],
            custom_args=custom_args or []
        )
        self.instances[instance_id] = instance
        return instance
    
    async def launch_instance(
        self,
        instance_id: str,
        headless: bool = False,
        timeout: int = 30000
    ) -> bool:
        """
        启动浏览器实例
        
        Args:
            instance_id: 实例ID
            headless: 是否无头模式
            timeout: 超时时间(毫秒)
        
        Returns:
            bool: 是否启动成功
        """
        if instance_id not in self.instances:
            raise ValueError(f"Instance {instance_id} not found")
        
        instance = self.instances[instance_id]
        
        # 构建浏览器启动参数
        launch_options = {
            'headless': headless,
            'args': self._get_browser_args(instance)
        }
        
        # 添加代理配置
        if instance.fingerprint.get('proxy'):
            launch_options['proxy'] = {
                'server': instance.fingerprint['proxy']
            }
        
        # 启动浏览器
        instance.browser = await self.playwright.chromium.launch(**launch_options)
        
        # 创建上下文(应用指纹)
        context_options = self._get_context_options(instance)
        instance.context = await instance.browser.new_context(**context_options)
        
        # 创建页面
        instance.page = await instance.context.new_page()
        
        return True
    
    def _get_browser_args(self, instance: BrowserInstance) -> List[str]:
        """获取浏览器参数"""
        args = [
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-web-security',
            '--disable-features=IsolateOrigins,site-per-process',
        ]
        
        # 添加自定义参数
        args.extend(instance.custom_args)
        
        return args
    
    def _get_context_options(self, instance: BrowserInstance) -> Dict:
        """获取上下文配置(指纹)"""
        fp = instance.fingerprint
        
        options = {
            'viewport': {
                'width': fp.get('viewport_width', 1920),
                'height': fp.get('viewport_height', 1080)
            },
            'user_agent': fp.get('user_agent', ''),
            'locale': fp.get('locale', 'zh-CN'),
            'timezone_id': fp.get('timezone', 'Asia/Shanghai'),
            'geolocation': fp.get('geolocation', {'latitude': 0, 'longitude': 0}),
            'permissions': fp.get('permissions', ['geolocation']),
            'color_scheme': fp.get('color_scheme', 'light'),
            'device_scale_factor': fp.get('device_scale_factor', 1),
            'is_mobile': fp.get('is_mobile', False),
            'has_touch': fp.get('has_touch', False),
        }
        
        # 过滤掉空值
        options = {k: v for k, v in options.items() if v}
        
        return options
    
    async def close_instance(self, instance_id: str) -> bool:
        """
        关闭浏览器实例
        
        Args:
            instance_id: 实例ID
        
        Returns:
            bool: 是否关闭成功
        """
        if instance_id not in self.instances:
            return False
        
        instance = self.instances[instance_id]
        
        # 保存cookies
        if instance.context:
            instance.cookies = await instance.context.cookies()
        
        # 关闭页面
        if instance.page:
            await instance.page.close()
        
        # 关闭上下文
        if instance.context:
            await instance.context.close()
        
        # 关闭浏览器
        if instance.browser:
            await instance.browser.close()
        
        del self.instances[instance_id]
        return True
    
    async def navigate(self, instance_id: str, url: str, wait_until: str = 'load') -> Optional[str]:
        """
        导航到指定URL
        
        Args:
            instance_id: 实例ID
            url: 目标URL
            wait_until: 等待策略
        
        Returns:
            str: 页面标题
        """
        instance = self.instances.get(instance_id)
        if not instance or not instance.page:
            raise ValueError(f"Instance {instance_id} not running")
        
        response = await instance.page.goto(url, wait_until=wait_until)
        
        if response:
            # 保存状态码
            instance.fingerprint['last_status'] = response.status
        
        return await instance.page.title()
    
    async def execute_script(self, instance_id: str, script: str) -> Any:
        """
        在页面执行JavaScript
        
        Args:
            instance_id: 实例ID
            script: JavaScript代码
        
        Returns:
            Any: 执行结果
        """
        instance = self.instances.get(instance_id)
        if not instance or not instance.page:
            raise ValueError(f"Instance {instance_id} not running")
        
        return await instance.page.evaluate(script)
    
    async def take_screenshot(self, instance_id: str, path: str, full_page: bool = False) -> bool:
        """
        截图
        
        Args:
            instance_id: 实例ID
            path: 保存路径
            full_page: 是否截取整个页面
        
        Returns:
            bool: 是否成功
        """
        instance = self.instances.get(instance_id)
        if not instance or not instance.page:
            raise ValueError(f"Instance {instance_id} not running")
        
        await instance.page.screenshot(path=path, full_page=full_page)
        return True
    
    def get_instance(self, instance_id: str) -> Optional[BrowserInstance]:
        """获取实例"""
        return self.instances.get(instance_id)
    
    def list_instances(self) -> List[Dict]:
        """列出所有实例"""
        return [inst.to_dict() for inst in self.instances.values()]
    
    async def clone_instance(
        self, 
        source_id: str, 
        new_name: str,
        copy_cookies: bool = True
    ) -> Optional[BrowserInstance]:
        """
        克隆浏览器实例
        
        Args:
            source_id: 源实例ID
            new_name: 新实例名称
            copy_cookies: 是否复制Cookie
        
        Returns:
            BrowserInstance: 新实例
        """
        source = self.instances.get(source_id)
        if not source:
            return None
        
        # 创建新实例
        new_instance = self.create_instance(
            name=new_name,
            fingerprint=source.fingerprint.copy(),
            tags=source.tags.copy(),
            custom_args=source.custom_args.copy()
        )
        
        # 复制cookies
        if copy_cookies:
            new_instance.cookies = source.cookies.copy()
        
        return new_instance
    
    async def import_cookies(self, instance_id: str, cookies: List[Dict]) -> bool:
        """
        导入Cookie
        
        Args:
            instance_id: 实例ID
            cookies: Cookie列表
        
        Returns:
            bool: 是否成功
        """
        instance = self.instances.get(instance_id)
        if not instance or not instance.context:
            raise ValueError(f"Instance {instance_id} not running")
        
        await instance.context.add_cookies(cookies)
        instance.cookies = cookies
        return True
    
    async def export_cookies(self, instance_id: str) -> List[Dict]:
        """
        导出Cookie
        
        Args:
            instance_id: 实例ID
        
        Returns:
            List[Dict]: Cookie列表
        """
        instance = self.instances.get(instance_id)
        if not instance or not instance.context:
            raise ValueError(f"Instance {instance_id} not running")
        
        return await instance.context.cookies()
    
    def save_instances_config(self, path: str) -> bool:
        """保存实例配置到文件"""
        config = {
            'instances': self.list_instances(),
            'saved_at': datetime.now().isoformat()
        }
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        return True
    
    def load_instances_config(self, path: str) -> bool:
        """从文件加载实例配置"""
        if not os.path.exists(path):
            return False
        
        with open(path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 恢复实例配置(不恢复运行的浏览器)
        for inst_config in config.get('instances', []):
            self.create_instance(
                name=inst_config['name'],
                fingerprint=inst_config.get('fingerprint', {}),
                tags=inst_config.get('tags', []),
                custom_args=inst_config.get('custom_args', [])
            )
        
        return True


# 便捷函数
async def quick_browse(url: str, fingerprint: Optional[Dict] = None) -> Page:
    """
    快速浏览 - 创建临时浏览器访问URL
    
    Args:
        url: 目标URL
        fingerprint: 指纹配置
    
    Returns:
        Page: 页面对象
    """
    manager = BrowserManager()
    await manager.initialize()
    
    instance = manager.create_instance(
        name="temp",
        fingerprint=fingerprint
    )
    
    await manager.launch_instance(instance.instance_id)
    await manager.navigate(instance.instance_id, url)
    
    # 返回页面但保持管理器引用
    manager._temp_instance = instance
    manager._temp_manager = manager
    
    return instance.page