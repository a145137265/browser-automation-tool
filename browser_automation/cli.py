"""
浏览器自动化工具 - CLI 入口
Browser Automation Tool - CLI Entry
"""

import asyncio
import argparse
import json
import sys
from typing import Optional
from pathlib import Path

from browser_automation import BrowserManager, FingerprintGenerator, CookieManager
from browser_automation.fingerprint import PresetFingerprints


class AutomationCLI:
    """命令行工具"""
    
    def __init__(self):
        self.manager = None
        self.cookie_manager = CookieManager()
    
    async def initialize(self):
        """初始化"""
        self.manager = BrowserManager()
        await self.manager.initialize()
    
    async def cleanup(self):
        """清理资源"""
        if self.manager:
            await self.manager.close()
    
    async def create_browser(
        self,
        name: str,
        platform: str = 'windows',
        headless: bool = False,
        proxy: Optional[str] = None
    ):
        """创建浏览器实例"""
        fp_generator = FingerprintGenerator()
        fingerprint = fp_generator.generate(platform=platform)
        
        instance = self.manager.create_instance(
            name=name,
            fingerprint=fingerprint.to_dict(),
            proxy=proxy
        )
        
        await self.manager.launch_instance(instance.instance_id, headless=headless)
        
        print(f"✓ 浏览器实例 '{name}' 已创建 (ID: {instance.instance_id})")
        return instance
    
    async def browse(self, instance_id: str, url: str):
        """浏览网页"""
        title = await self.manager.navigate(instance_id, url)
        print(f"✓ 已导航到: {title}")
    
    async def screenshot(self, instance_id: str, path: str):
        """截图"""
        await self.manager.take_screenshot(instance_id, path)
        print(f"✓ 截图已保存到: {path}")
    
    async def execute_js(self, instance_id: str, script: str):
        """执行JavaScript"""
        result = await self.manager.execute_script(instance_id, script)
        print(result)
    
    async def get_cookies(self, instance_id: str):
        """获取Cookie"""
        cookies = await self.manager.export_cookies(instance_id)
        print(json.dumps(cookies, ensure_ascii=False, indent=2))
    
    async def set_cookies(self, instance_id: str, cookies_file: str):
        """设置Cookie"""
        with open(cookies_file, 'r', encoding='utf-8') as f:
            cookies = json.load(f)
        await self.manager.import_cookies(instance_id, cookies)
        print(f"✓ 已导入 {len(cookies)} 个Cookie")
    
    def list_instances(self):
        """列出实例"""
        instances = self.manager.list_instances()
        for inst in instances:
            print(f"- {inst['name']} (ID: {inst['instance_id']}, Tags: {inst['tags']})")
    
    def export_config(self, path: str):
        """导出配置"""
        self.manager.save_instances_config(path)
        print(f"✓ 配置已保存到: {path}")


async def main():
    parser = argparse.ArgumentParser(
        description='浏览器自动化控制工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 启动浏览器并访问网站
  python -m browser_automation browse -n my-browser -u https://example.com
  
  # 创建无头浏览器
  python -m browser_automation create -n test --headless
  
  # 使用代理
  python -m browser_automation create -n proxy-test --proxy http://127.0.0.1:7890
  
  # 查看已保存的Cookie
  python -m browser_automation cookies -i instance_id
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='命令')
    
    # 创建浏览器
    create_parser = subparsers.add_parser('create', help='创建浏览器实例')
    create_parser.add_argument('-n', '--name', required=True, help='实例名称')
    create_parser.add_argument('--platform', default='windows', choices=['windows', 'mac', 'linux', 'android', 'ios'])
    create_parser.add_argument('--headless', action='store_true', help='无头模式')
    create_parser.add_argument('--proxy', help='代理服务器')
    create_parser.add_argument('--mobile', action='store_true', help='移动设备')
    
    # 浏览网页
    browse_parser = subparsers.add_parser('browse', help='浏览网页')
    browse_parser.add_argument('-n', '--name', help='实例名称(新建)')
    browse_parser.add_argument('-i', '--instance', help='实例ID')
    browse_parser.add_argument('-u', '--url', required=True, help='目标URL')
    browse_parser.add_argument('--platform', default='windows')
    browse_parser.add_argument('--headless', action='store_true')
    browse_parser.add_argument('--proxy')
    
    # 截图
    screenshot_parser = subparsers.add_parser('screenshot', help='截图')
    screenshot_parser.add_argument('-i', '--instance', required=True, help='实例ID')
    screenshot_parser.add_argument('-o', '--output', required=True, help='输出路径')
    
    # 执行脚本
    js_parser = subparsers.add_parser('js', help='执行JavaScript')
    js_parser.add_argument('-i', '--instance', required=True, help='实例ID')
    js_parser.add_argument('-s', '--script', required=True, help='JavaScript代码')
    
    # Cookie管理
    cookie_parser = subparsers.add_parser('cookies', help='Cookie管理')
    cookie_parser.add_argument('-i', '--instance', help='实例ID')
    cookie_parser.add_argument('-g', '--get', action='store_true', help='获取Cookie')
    cookie_parser.add_argument('-s', '--set', help='导入Cookie文件')
    
    # 列出实例
    list_parser = subparsers.add_parser('list', help='列出所有实例')
    
    # 指纹生成
    fp_parser = subparsers.add_parser('fingerprint', help='指纹操作')
    fp_parser.add_argument('--generate', action='store_true', help='生成指纹')
    fp_parser.add_argument('--preset', choices=['windows', 'mac', 'android', 'stealth'], help='预设指纹')
    fp_parser.add_argument('-o', '--output', help='输出文件')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = AutomationCLI()
    
    try:
        if args.command == 'fingerprint':
            # 指纹生成
            if args.preset:
                fp = getattr(PresetFingerprints, f'{args.preset}_chrome')()
            else:
                gen = FingerprintGenerator()
                fp = gen.generate(platform='windows')
            
            print(json.dumps(fp, ensure_ascii=False, indent=2))
            
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(fp, f, ensure_ascii=False, indent=2)
                print(f"✓ 已保存到: {args.output}")
            
            return
        
        await cli.initialize()
        
        if args.command == 'create':
            instance = await cli.create_browser(
                name=args.name,
                platform=args.platform,
                headless=args.headless,
                proxy=args.proxy
            )
            print(f"实例ID: {instance.instance_id}")
        
        elif args.command == 'browse':
            instance_id = args.instance
            
            if not instance_id:
                instance = await cli.create_browser(
                    name=args.name or 'temp',
                    platform=args.platform,
                    headless=args.headless,
                    proxy=args.proxy
                )
                instance_id = instance.instance_id
            
            await cli.browse(instance_id, args.url)
        
        elif args.command == 'screenshot':
            await cli.screenshot(args.instance, args.output)
        
        elif args.command == 'js':
            await cli.execute_js(args.instance, args.script)
        
        elif args.command == 'cookies':
            if args.get and args.instance:
                await cli.get_cookies(args.instance)
            elif args.set and args.instance:
                await cli.set_cookies(args.instance, args.set)
        
        elif args.command == 'list':
            cli.list_instances()
    
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
    
    finally:
        await cli.cleanup()


if __name__ == '__main__':
    asyncio.run(main())