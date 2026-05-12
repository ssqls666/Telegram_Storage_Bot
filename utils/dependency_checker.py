import sys
import os
import subprocess


REQUIRED_PACKAGES = {
    'PyQt5': 'PyQt5',
    'telegram': 'python-telegram-bot',
    'matplotlib': 'matplotlib',
    'aiofiles': 'aiofiles',
}

CHINA_MIRRORS = [
    'https://pypi.tuna.tsinghua.edu.cn/simple',
    'https://mirrors.aliyun.com/pypi/simple/',
    'https://pypi.mirrors.ustc.edu.cn/simple/',
]


def check_dependencies():
    missing = []
    for import_name, package_name in REQUIRED_PACKAGES.items():
        try:
            __import__(import_name)
        except ImportError:
            missing.append(package_name)
    return missing


def generate_install_bat(missing_packages):
    bat_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'install_deps.bat')
    mirror = CHINA_MIRRORS[0]

    lines = ['@echo off', 'echo ========================================',
             'echo 清风网盘 - 安装依赖库', 'echo ========================================',
             'echo.', 'echo 正在升级pip...',
             f'python -m pip install --upgrade pip -i {mirror}',
             'echo.', 'echo 正在安装所需依赖库...']

    for pkg in missing_packages:
        lines.append(f'python -m pip install {pkg} -i {mirror}')

    lines.extend(['echo.', 'echo ========================================',
                  'echo 安装完成! 请重新运行主程序。',
                  'echo ========================================',
                  'pause'])

    with open(bat_path, 'w', encoding='gbk') as f:
        f.write('\n'.join(lines))

    return bat_path


def check_and_install():
    missing = check_dependencies()
    if not missing:
        return True, []

    bat_path = generate_install_bat(missing)
    return False, missing
