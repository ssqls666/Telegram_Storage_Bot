import sys
import os
import subprocess

sys.path.insert(0, os.path.dirname(__file__))

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt

from utils.dependency_checker import check_dependencies, generate_install_bat
from utils.helpers import load_config, save_config
from utils.logger import logger
from gui.main_window import MainWindow

def main():
    print('=' * 50)
    print('  清风网盘 - Telegram文件储存机器人')
    print('  正在启动...')
    print('=' * 50)

    missing = check_dependencies()
    if missing:
        print(f'\n⚠ 检测到缺失依赖: {", ".join(missing)}')
        bat_path = generate_install_bat(missing)
        print(f'\n已生成安装脚本: {bat_path}')
        print('请双击运行 install_deps.bat 安装依赖后重新启动程序。')

        input('\n按Enter键退出...')
        sys.exit(0)

    print('✅ 所有依赖已就绪')

    config = load_config()
    save_config(config)

    try:
        import matplotlib
        matplotlib.use('Qt5Agg')
    except Exception:
        pass

    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)

    app.setApplicationName('清风网盘')
    app.setOrganizationName('QingFeng')

    window = MainWindow(config)
    window.show()

    logger.info('程序启动完成')

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

# 应该没人会看到这玩意吧
# 咳咳
# 我宣布一个事
# 我是个帅比
