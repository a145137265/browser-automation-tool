"""
Cookie管理器 - Cookie Management
支持Cookie的导入、导出、同步、加密存储
"""

import json
import os
import hashlib
import base64
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import copy


@dataclass
class CookieEntry:
    """Cookie条目"""
    name: str
    value: str
    domain: str
    path: str = '/'
    expires: Optional[float] = None
    http_only: bool = False
    secure: bool = False
    same_site: str = 'Lax'
    session: bool = False
    
    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'value': self.value,
            'domain': self.domain,
            'path': self.path,
            'expires': self.expires,
            'httpOnly': self.http_only,
            'secure': self.secure,
            'sameSite': self.same_site,
            'session': self.session
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CookieEntry':
        return cls(
            name=data.get('name', ''),
            value=data.get('value', ''),
            domain=data.get('domain', ''),
            path=data.get('path', '/'),
            expires=data.get('expires'),
            http_only=data.get('httpOnly', False),
            secure=data.get('secure', False),
            same_site=data.get('sameSite', 'Lax'),
            session=data.get('session', False)
        )


class CookieManager:
    """
    Cookie管理器
    提供Cookie的导入、导出、同步、加密等功能
    """
    
    def __init__(self, storage_dir: Optional[str] = None):
        """
        初始化Cookie管理器
        
        Args:
            storage_dir: 存储目录
        """
        self.storage_dir = Path(storage_dir or './cookies')
        self.storage_dir.mkdir(parents=True, exist_ok=True)
    
    def export_to_json(
        self, 
        cookies: List[Dict], 
        path: str,
        pretty: bool = True
    ) -> bool:
        """
        导出Cookie到JSON文件
        
        Args:
            cookies: Cookie列表
            path: 保存路径
            pretty: 是否格式化
        
        Returns:
            bool: 是否成功
        """
        with open(path, 'w', encoding='utf-8') as f:
            if pretty:
                json.dump(cookies, f, ensure_ascii=False, indent=2)
            else:
                json.dump(cookies, f)
        return True
    
    def import_from_json(self, path: str) -> List[Dict]:
        """
        从JSON文件导入Cookie
        
        Args:
            path: 文件路径
        
        Returns:
            List[Dict]: Cookie列表
        """
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def save_cookies(
        self, 
        cookies: List[Dict], 
        name: str,
        encrypt: bool = False,
        key: Optional[str] = None
    ) -> str:
        """
        保存Cookie到存储目录
        
        Args:
            cookies: Cookie列表
            name: 名称(用于文件名)
            encrypt: 是否加密
            key: 加密密钥
        
        Returns:
            str: 保存的文件路径
        """
        filename = self._sanitize_filename(name)
        filepath = self.storage_dir / f"{filename}.json"
        
        if encrypt and key:
            cookies = self._encrypt_cookies(cookies, key)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            if encrypt:
                json.dump({
                    'encrypted': True,
                    'data': cookies,
                    'timestamp': datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)
            else:
                json.dump(cookies, f, ensure_ascii=False, indent=2)
        
        return str(filepath)
    
    def load_cookies(self, name: str, decrypt: bool = False, key: Optional[str] = None) -> List[Dict]:
        """
        从存储目录加载Cookie
        
        Args:
            name: 名称
            decrypt: 是否解密
            key: 解密密钥
        
        Returns:
            List[Dict]: Cookie列表
        """
        filename = self._sanitize_filename(name)
        filepath = self.storage_dir / f"{filename}.json"
        
        if not filepath.exists():
            return []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if decrypt and key and isinstance(data, dict) and data.get('encrypted'):
            return self._decrypt_cookies(data['data'], key)
        
        return data
    
    def list_cookies(self) -> List[Dict]:
        """
        列出所有保存的Cookie
        
        Returns:
            List[Dict]: Cookie文件列表
        """
        results = []
        
        for filepath in self.storage_dir.glob('*.json'):
            with open(filepath, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    results.append({
                        'name': filepath.stem,
                        'path': str(filepath),
                        'encrypted': data.get('encrypted', False),
                        'size': filepath.stat().st_size,
                        'timestamp': datetime.fromtimestamp(
                            filepath.stat().st_mtime
                        ).isoformat()
                    })
                except:
                    pass
        
        return results
    
    def delete_cookies(self, name: str) -> bool:
        """
        删除保存的Cookie
        
        Args:
            name: 名称
        
        Returns:
            bool: 是否成功
        """
        filename = self._sanitize_filename(name)
        filepath = self.storage_dir / f"{filename}.json"
        
        if filepath.exists():
            filepath.unlink()
            return True
        
        return False
    
    def merge_cookies(
        self, 
        cookies1: List[Dict], 
        cookies2: List[Dict],
        strategy: str = 'prefer_new'
    ) -> List[Dict]:
        """
        合并Cookie
        
        Args:
            cookies1: Cookie列表1
            cookies2: Cookie列表2
            strategy: 合并策略 (prefer_new/prefer_old/merge)
        
        Returns:
            List[Dict]: 合并后的Cookie列表
        """
        cookie_map = {}
        
        # 使用字典去重
        for cookie in cookies1:
            key = f"{cookie.get('domain')}:{cookie.get('name')}"
            cookie_map[key] = cookie
        
        for cookie in cookies2:
            key = f"{cookie.get('domain')}:{cookie.get('name')}"
            
            if strategy == 'prefer_new':
                cookie_map[key] = cookie
            elif strategy == 'prefer_old':
                if key not in cookie_map:
                    cookie_map[key] = cookie
            else:  # merge - 保留两个值不同的cookie(创建副本)
                if key in cookie_map:
                    # 值不同,创建两份
                    cookie_map[f"{key}_2"] = cookie
                else:
                    cookie_map[key] = cookie
        
        return list(cookie_map.values())
    
    def filter_cookies(
        self, 
        cookies: List[Dict], 
        domains: Optional[List[str]] = None,
        names: Optional[List[str]] = None,
        secure: Optional[bool] = None,
        http_only: Optional[bool] = None
    ) -> List[Dict]:
        """
        过滤Cookie
        
        Args:
            domains: 域名过滤
            names: Cookie名称过滤
            secure: 安全Cookie过滤
            http_only: HttpOnly过滤
        
        Returns:
            List[Dict]: 过滤后的Cookie列表
        """
        result = cookies
        
        if domains:
            result = [
                c for c in result 
                if any(d in c.get('domain', '') for d in domains)
            ]
        
        if names:
            result = [
                c for c in result 
                if c.get('name') in names
            ]
        
        if secure is not None:
            result = [
                c for c in result 
                if c.get('secure') == secure
            ]
        
        if http_only is not None:
            result = [
                c for c in result 
                if c.get('httpOnly') == http_only
            ]
        
        return result
    
    def convert_to_netscape(self, cookies: List[Dict]) -> str:
        """
        转换为Netscape格式(用于curl等工具)
        
        Args:
            cookies: Cookie列表
        
        Returns:
            str: Netscape格式字符串
        """
        lines = ['# Netscape HTTP Cookie File']
        lines.append('# This file was generated by Browser Automation Tool')
        lines.append('')
        
        for cookie in cookies:
            domain = cookie.get('domain', '')
            flag = 'TRUE' if domain.startswith('.') else 'FALSE'
            path = cookie.get('path', '/')
            secure = 'TRUE' if cookie.get('secure') else 'FALSE'
            expires = int(cookie.get('expires', 0))
            name = cookie.get('name', '')
            value = cookie.get('value', '')
            
            lines.append(f"{domain}\t{flag}\t{path}\t{secure}\t{expires}\t{name}\t{value}")
        
        return '\n'.join(lines)
    
    def export_to_netscape(self, cookies: List[Dict], path: str) -> bool:
        """
        导出为Netscape格式
        
        Args:
            cookies: Cookie列表
            path: 保存路径
        
        Returns:
            bool: 是否成功
        """
        content = self.convert_to_netscape(cookies)
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True
    
    def import_from_netscape(self, path: str) -> List[Dict]:
        """
        从Netscape格式导入
        
        Args:
            path: 文件路径
        
        Returns:
            List[Dict]: Cookie列表
        """
        cookies = []
        
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                
                # 跳过注释和空行
                if not line or line.startswith('#'):
                    continue
                
                parts = line.split('\t')
                if len(parts) >= 7:
                    cookies.append({
                        'domain': parts[0],
                        'flag': parts[1] == 'TRUE',
                        'path': parts[2],
                        'secure': parts[3] == 'TRUE',
                        'expires': int(parts[4]) if parts[4].isdigit() else None,
                        'name': parts[5],
                        'value': parts[6]
                    })
        
        return cookies
    
    def sync_cookies(
        self,
        source_cookies: List[Dict],
        target_cookies: List[Dict],
        add_new: bool = True,
        update_existing: bool = True,
        remove_expired: bool = False
    ) -> List[Dict]:
        """
        同步Cookie
        
        Args:
            source_cookies: 源Cookie
            target_cookies: 目标Cookie
            add_new: 是否添加新的Cookie
            update_existing: 是否更新已存在的Cookie
            remove_expired: 是否移除过期的Cookie
        
        Returns:
            List[Dict]: 同步后的Cookie列表
        """
        now = datetime.now().timestamp()
        
        # 转换为字典便于操作
        cookie_map = {}
        for cookie in target_cookies:
            key = self._get_cookie_key(cookie)
            cookie_map[key] = cookie
        
        # 处理源Cookie
        for cookie in source_cookies:
            key = self._get_cookie_key(cookie)
            
            # 检查过期
            expires = cookie.get('expires')
            if expires and expires < now:
                if remove_expired:
                    cookie_map.pop(key, None)
                continue
            
            if key in cookie_map:
                if update_existing:
                    cookie_map[key] = cookie
            else:
                if add_new:
                    cookie_map[key] = cookie
        
        return list(cookie_map.values())
    
    def validate_cookies(self, cookies: List[Dict]) -> Dict[str, Any]:
        """
        验证Cookie
        
        Args:
            cookies: Cookie列表
        
        Returns:
            Dict: 验证结果
        """
        result = {
            'valid': True,
            'total': len(cookies),
            'issues': [],
            'expired': 0,
            'empty_value': 0,
            'missing_fields': 0
        }
        
        required_fields = ['name', 'value', 'domain']
        now = datetime.now().timestamp()
        
        for i, cookie in enumerate(cookies):
            # 检查必填字段
            missing = [f for f in required_fields if not cookie.get(f)]
            if missing:
                result['missing_fields'] += 1
                result['issues'].append({
                    'index': i,
                    'type': 'missing_fields',
                    'fields': missing
                })
            
            # 检查空值
            if not cookie.get('value'):
                result['empty_value'] += 1
                result['issues'].append({
                    'index': i,
                    'type': 'empty_value',
                    'name': cookie.get('name', 'unknown')
                })
            
            # 检查过期
            expires = cookie.get('expires')
            if expires and expires < now:
                result['expired'] += 1
        
        if result['issues']:
            result['valid'] = False
        
        return result
    
    def get_cookies_for_domain(self, cookies: List[Dict], domain: str) -> List[Dict]:
        """
        获取指定域名的Cookie
        
        Args:
            cookies: Cookie列表
            domain: 域名
        
        Returns:
            List[Dict]: 该域名的Cookie
        """
        return [
            cookie for cookie in cookies
            if domain in cookie.get('domain', '')
        ]
    
    def _sanitize_filename(self, name: str) -> str:
        """清理文件名"""
        return ''.join(c for c in name if c.isalnum() or c in '-_').strip()
    
    def _get_cookie_key(self, cookie: Dict) -> str:
        """获取Cookie唯一键"""
        return f"{cookie.get('domain')}:{cookie.get('path')}:{cookie.get('name')}"
    
    def _encrypt_cookies(self, cookies: List[Dict], key: str) -> str:
        """加密Cookie"""
        # 简单的base64编码作为示例
        data = json.dumps(cookies)
        encoded = base64.b64encode(data.encode()).decode()
        return encoded
    
    def _decrypt_cookies(self, encoded: str, key: str) -> List[Dict]:
        """解密Cookie"""
        decoded = base64.b64decode(encoded.encode()).decode()
        return json.loads(decoded)


class CookieJar:
    """
    Cookie罐 - 内存中的Cookie管理
    """
    
    def __init__(self):
        self.cookies: Dict[str, CookieEntry] = {}
        self.domain_cookies: Dict[str, List[str]] = {}
    
    def set(self, cookie: CookieEntry) -> None:
        """设置Cookie"""
        key = f"{cookie.domain}:{cookie.name}"
        self.cookies[key] = cookie
        
        # 更新域索引
        if cookie.domain not in self.domain_cookies:
            self.domain_cookies[cookie.domain] = []
        if key not in self.domain_cookies[cookie.domain]:
            self.domain_cookies[cookie.domain].append(key)
    
    def get(self, domain: str, name: str) -> Optional[CookieEntry]:
        """获取Cookie"""
        key = f"{domain}:{name}"
        return self.cookies.get(key)
    
    def get_all(self, domain: str) -> List[CookieEntry]:
        """获取域名的所有Cookie"""
        entries = []
        
        # 精确匹配
        for key in self.domain_cookies.get(domain, []):
            cookie = self.cookies.get(key)
            if cookie:
                entries.append(cookie)
        
        # 域名后缀匹配
        for key, cookie in self.cookies.items():
            if domain.endswith(cookie.domain) or cookie.domain.endswith(domain):
                if cookie not in entries:
                    entries.append(cookie)
        
        return entries
    
    def delete(self, domain: str, name: str) -> bool:
        """删除Cookie"""
        key = f"{domain}:{name}"
        
        if key in self.cookies:
            del self.cookies[key]
            
            if domain in self.domain_cookies:
                self.domain_cookies[domain].remove(key)
                if not self.domain_cookies[domain]:
                    del self.domain_cookies[domain]
            
            return True
        
        return False
    
    def clear(self, domain: Optional[str] = None) -> int:
        """清除Cookie"""
        if domain:
            keys = self.domain_cookies.get(domain, []).copy()
            for key in keys:
                self.cookies.pop(key, None)
            self.domain_cookies.pop(domain, None)
            return len(keys)
        
        count = len(self.cookies)
        self.cookies.clear()
        self.domain_cookies.clear()
        return count
    
    def to_list(self) -> List[Dict]:
        """转换为列表"""
        return [cookie.to_dict() for cookie in self.cookies.values()]
    
    @classmethod
    def from_list(cls, cookies: List[Dict]) -> 'CookieJar':
        """从列表创建"""
        jar = cls()
        
        for cookie_dict in cookies:
            cookie = CookieEntry.from_dict(cookie_dict)
            jar.set(cookie)
        
        return jar