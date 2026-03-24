"""
指纹生成器 - Fingerprint Customization
支持生成各种浏览器指纹配置
"""

import random
import json
import hashlib
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime


# 常用User-Agent列表
USER_AGENTS = {
    'windows': [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
    ],
    'mac': [
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    ],
    'linux': [
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0',
    ],
    'android': [
        'Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
        'Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36',
    ],
    'ios': [
        'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1',
        'Mozilla/5.0 (iPad; CPU OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1',
    ]
}

# 时区映射
TIMEZONES = [
    'Asia/Shanghai', 'Asia/Tokyo', 'Asia/Seoul', 'Asia/Singapore',
    'Asia/Dubai', 'Europe/London', 'Europe/Paris', 'Europe/Berlin',
    'America/New_York', 'America/Los_Angeles', 'America/Chicago',
    'Australia/Sydney', 'Pacific/Auckland'
]

# 语言设置
LOCALES = [
    'zh-CN', 'zh-TW', 'en-US', 'en-GB', 'ja-JP', 'ko-KR',
    'fr-FR', 'de-DE', 'es-ES', 'pt-BR', 'ru-RU', 'ar-SA'
]

# 屏幕分辨率
VIEWPORTS = [
    {'width': 1920, 'height': 1080},
    {'width': 1440, 'height': 900},
    {'width': 1366, 'height': 768},
    {'width': 1536, 'height': 864},
    {'width': 1280, 'height': 720},
    {'width': 2560, 'height': 1440},
    {'width': 375, 'height': 667},   # iPhone SE
    {'width': 390, 'height': 844},   # iPhone 12/13/14
    {'width': 414, 'height': 896},   # iPhone XR
    {'width': 428, 'height': 926},   # iPhone 14 Pro Max
    {'width': 360, 'height': 800},   # Android
]


@dataclass
class FingerprintConfig:
    """指纹配置数据类"""
    user_agent: str
    platform: str
    viewport: Dict[str, int]
    locale: str
    timezone: str
    color_scheme: str
    device_scale_factor: int
    is_mobile: bool
    has_touch: bool
    hardware_concurrency: int
    device_memory: int
    languages: List[str]
    plugins: List[Dict]
    webgl_vendor: str
    webgl_renderer: str
    screen_resolution: Dict[str, int]
    platform_arch: str
    proxy: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            'user_agent': self.user_agent,
            'platform': self.platform,
            'viewport': self.viewport,
            'locale': self.locale,
            'timezone': self.timezone,
            'color_scheme': self.color_scheme,
            'device_scale_factor': self.device_scale_factor,
            'is_mobile': self.is_mobile,
            'has_touch': self.has_touch,
            'hardware_concurrency': self.hardware_concurrency,
            'device_memory': self.device_memory,
            'languages': self.languages,
            'plugins': self.plugins,
            'webgl_vendor': self.webgl_vendor,
            'webgl_renderer': self.webgl_renderer,
            'screen_resolution': self.screen_resolution,
            'platform_arch': self.platform_arch,
            'proxy': self.proxy
        }


class FingerprintGenerator:
    """
    浏览器指纹生成器
    生成随机但一致的浏览器指纹配置
    """
    
    def __init__(self, seed: Optional[str] = None):
        """
        初始化指纹生成器
        
        Args:
            seed: 随机种子,用于生成一致的指纹
        """
        self.seed = seed or self._generate_seed()
        self._random = random.Random(self.seed)
    
    def _generate_seed(self) -> str:
        """生成随机种子"""
        return hashlib.md5(str(datetime.now()).encode()).hexdigest()[:16]
    
    def generate(
        self,
        platform: str = 'windows',
        locale: Optional[str] = None,
        timezone: Optional[str] = None,
        viewport: Optional[Dict[str, int]] = None,
        is_mobile: bool = False,
        proxy: Optional[str] = None
    ) -> FingerprintConfig:
        """
        生成指纹配置
        
        Args:
            platform: 平台类型 (windows/mac/linux/android/ios)
            locale: 语言设置
            timezone: 时区
            viewport: 视口大小
            is_mobile: 是否移动设备
            proxy: 代理服务器
        
        Returns:
            FingerprintConfig: 指纹配置
        """
        # 选择User-Agent
        user_agent = self._random.choice(USER_AGENTS.get(platform, USER_AGENTS['windows']))
        
        # 选择视口
        if not viewport:
            viewport = self._random.choice(VIEWPORTS)
        
        # 语言和时区
        if not locale:
            locale = self._random.choice(LOCALES)
        if not timezone:
            timezone = self._random.choice(TIMEZONES)
        
        # 平台信息
        platform_info = self._get_platform_info(platform, is_mobile)
        
        # 生成WebGL指纹
        webgl = self._generate_webgl()
        
        # 屏幕分辨率
        screen = viewport.copy()
        
        # 插件列表
        plugins = self._generate_plugins()
        
        return FingerprintConfig(
            user_agent=user_agent,
            platform=platform_info['platform'],
            viewport=viewport,
            locale=locale,
            timezone=timezone,
            color_scheme=self._random.choice(['light', 'dark', 'no-preference']),
            device_scale_factor=self._random.choice([1, 1.25, 1.5, 2, 2.5, 3]),
            is_mobile=is_mobile,
            has_touch=is_mobile or self._random.choice([True, False]),
            hardware_concurrency=self._random.choice([2, 4, 8, 12, 16]),
            device_memory=self._random.choice([2, 4, 8, 16]),
            languages=[locale, 'en-US'],
            plugins=plugins,
            webgl_vendor=webgl['vendor'],
            webgl_renderer=webgl['renderer'],
            screen_resolution=screen,
            platform_arch=platform_info['arch'],
            proxy=proxy
        )
    
    def generate_for_profile(self, profile_id: str) -> FingerprintConfig:
        """
        为特定配置文件生成一致指纹
        
        Args:
            profile_id: 配置文件ID
        
        Returns:
            FingerprintConfig: 指纹配置
        """
        # 使用profile_id作为种子确保一致性
        profile_seed = hashlib.md5(profile_id.encode()).hexdigest()
        profile_random = random.Random(profile_seed)
        
        # 随机选择平台
        platform = profile_random.choice(['windows', 'mac', 'windows', 'mac', 'linux'])
        is_mobile = platform in ['android', 'ios']
        
        # 预定义的profile配置
        platforms_map = {
            'windows': 'Win32',
            'mac': 'MacIntel', 
            'linux': 'Linux x86_64'
        }
        
        user_agents = USER_AGENTS.get(platform, USER_AGENTS['windows'])
        user_agent = user_agents[int(profile_id, 16) % len(user_agents)]
        
        return FingerprintConfig(
            user_agent=user_agent,
            platform=platforms_map.get(platform, 'Win32'),
            viewport=VIEWPORTS[int(profile_id, 16) % len(VIEWPORTS)],
            locale=LOCALES[int(profile_id, 16) % len(LOCALES)],
            timezone=TIMEZONES[int(profile_id, 16) % len(TIMEZONES)],
            color_scheme='light',
            device_scale_factor=1,
            is_mobile=is_mobile,
            has_touch=is_mobile,
            hardware_concurrency=8,
            device_memory=8,
            languages=[LOCALES[int(profile_id, 16) % len(LOCALES)], 'en-US'],
            plugins=self._generate_plugins(),
            webgl_vendor='Google Inc. (Intel)',
            webgl_renderer='ANGLE (Intel, Intel(R) UHD Graphics Direct3D11 vs_5_0 ps_5_0)',
            screen_resolution=VIEWPORTS[int(profile_id, 16) % len(VIEWPORTS)],
            platform_arch='x64'
        )
    
    def _get_platform_info(self, platform: str, is_mobile: bool) -> Dict:
        """获取平台信息"""
        platforms = {
            'windows': {'platform': 'Win32', 'arch': 'x64'},
            'mac': {'platform': 'MacIntel', 'arch': 'x64'},
            'linux': {'platform': 'Linux x86_64', 'arch': 'x64'},
            'android': {'platform': 'Linux armv7l', 'arch': 'arm'},
            'ios': {'platform': 'iPhone', 'arch': 'arm64'}
        }
        
        info = platforms.get(platform, platforms['windows'])
        if is_mobile and platform not in ['android', 'ios']:
            info['platform'] = 'iPhone'
            info['arch'] = 'arm64'
        
        return info
    
    def _generate_webgl(self) -> Dict:
        """生成WebGL指纹"""
        vendors = [
            'Google Inc. (Intel)',
            'Google Inc. (NVIDIA)',
            'Google Inc. (AMD)',
            'Intel Inc.',
            'NVIDIA Corporation',
            'AMD'
        ]
        
        renderers = [
            'ANGLE (Intel, Intel(R) UHD Graphics Direct3D11 vs_5_0 ps_5_0)',
            'ANGLE (NVIDIA, NVIDIA GeForce RTX 3080 Direct3D11 vs_5_0 ps_5_0)',
            'ANGLE (AMD, AMD Radeon RX 6800 XT Direct3D11 vs_5_0 ps_5_0)',
            'Intel Iris OpenGL Engine',
            'ANGLE (Intel, Intel(R) UHD Graphics 620 Direct3D11 vs_5_0 ps_5_0)',
            'SwiftShader for Google Inc.'
        ]
        
        return {
            'vendor': self._random.choice(vendors),
            'renderer': self._random.choice(renderers)
        }
    
    def _generate_plugins(self) -> List[Dict]:
        """生成浏览器插件列表"""
        return [
            {'name': 'PDF Viewer', 'description': 'Portable Document Format'},
            {'name': 'Chrome PDF Viewer', 'description': 'Portable Document Format'},
            {'name': 'Native Client', 'description': 'Native Client executable'}
        ]
    
    def export_fingerprint(self, config: FingerprintConfig, path: str) -> bool:
        """
        导出指纹配置到文件
        
        Args:
            config: 指纹配置
            path: 保存路径
        
        Returns:
            bool: 是否成功
        """
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(config.to_dict(), f, ensure_ascii=False, indent=2)
        return True
    
    def import_fingerprint(self, path: str) -> Optional[FingerprintConfig]:
        """
        从文件导入指纹配置
        
        Args:
            path: 文件路径
        
        Returns:
            FingerprintConfig: 指纹配置
        """
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return FingerprintConfig(**data)
    
    @staticmethod
    def get_random_ua(platform: str = 'windows') -> str:
        """获取随机User-Agent"""
        return random.choice(USER_AGENTS.get(platform, USER_AGENTS['windows']))
    
    @staticmethod
    def detect_fingerprint(page) -> Dict:
        """
        检测页面指纹
        
        Args:
            page: Playwright Page对象
        
        Returns:
            Dict: 检测到的指纹信息
        """
        import asyncio
        
        script = """
        () => {
            const getWebGL = () => {
                const canvas = document.createElement('canvas');
                const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
                if (!gl) return {};
                
                const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
                if (!debugInfo) return {};
                
                return {
                    vendor: gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL),
                    renderer: gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL)
                };
            };
            
            const webgl = getWebGL();
            
            return {
                userAgent: navigator.userAgent,
                platform: navigator.platform,
                language: navigator.language,
                languages: navigator.languages,
                colorDepth: screen.colorDepth,
                screenResolution: `${screen.width}x${screen.height}`,
                timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
                hardwareConcurrency: navigator.hardwareConcurrency,
                deviceMemory: navigator.deviceMemory,
                webglVendor: webgl.vendor,
                webglRenderer: webgl.renderer,
                plugins: Array.from(navigator.plugins).map(p => p.name),
                doNotTrack: navigator.doNotTrack,
                cookiesEnabled: navigator.cookieEnabled,
                touchSupport: 'ontouchstart' in window,
                maxTouchPoints: navigator.maxTouchPoints
            };
        }
        """
        
        return asyncio.run(page.evaluate(script))


# 预设指纹配置
class PresetFingerprints:
    """预设指纹配置"""
    
    @staticmethod
    def windows_chrome() -> Dict:
        """Windows Chrome 指纹"""
        generator = FingerprintGenerator()
        config = generator.generate(platform='windows', is_mobile=False)
        return config.to_dict()
    
    @staticmethod
    def mac_safari() -> Dict:
        """Mac Safari 指纹"""
        generator = FingerprintGenerator()
        return {
            'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
            'platform': 'MacIntel',
            'viewport': {'width': 1920, 'height': 1080},
            'locale': 'zh-CN',
            'timezone': 'Asia/Shanghai',
            'color_scheme': 'light',
            'device_scale_factor': 2,
            'is_mobile': False,
            'has_touch': False,
            'hardware_concurrency': 8,
            'device_memory': 8
        }
    
    @staticmethod
    def android_chrome() -> Dict:
        """Android Chrome 指纹"""
        generator = FingerprintGenerator()
        config = generator.generate(platform='android', is_mobile=True)
        return config.to_dict()
    
    @staticmethod
    def stealth() -> Dict:
        """防检测指纹"""
        generator = FingerprintGenerator()
        return generator.generate(
            platform='windows',
            locale='zh-CN',
            timezone='Asia/Shanghai',
            viewport={'width': 1920, 'height': 1080}
        ).to_dict()