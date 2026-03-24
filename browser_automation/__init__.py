"""
浏览器自动化控制工具
Browser Automation Tool - Multi-instance, Fingerprint Customization, Cookie Management
"""

__version__ = "1.0.0"
__author__ = "Browser Automation Tool"

from .browser_manager import BrowserManager
from .fingerprint import FingerprintGenerator
from .cookie_manager import CookieManager

__all__ = ['BrowserManager', 'FingerprintGenerator', 'CookieManager']