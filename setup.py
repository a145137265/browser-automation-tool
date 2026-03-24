from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="browser-automation-tool",
    version="1.0.0",
    author="Browser Automation Tool",
    author_email="contact@example.com",
    description="专业的浏览器自动化控制工具 - 多实例管理、指纹定制、Cookie管理",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/a145137265/browser-automation-tool",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "browser-automation=browser_automation.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "browser_automation": ["*.json", "*.txt"],
    },
)