import sys
import os
import logging
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from core.browser import BrowserManager
from core.automation import AutomationManager
from core.process_manager import CursorProcessManager
from utils.system_config import SystemConfigManager
from core.db_manager import DbManager
from core.account_manager_db import AccountManagerDb
from ui.main_window import MainWindow
from utils.logger import LoggerManager

# 初始化日志管理器
log_manager = LoggerManager()
logger = logging.getLogger("main")

# 配置根日志记录器
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# 移除所有现有的处理器
for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)

# 添加日志管理器作为处理器
root_logger.addHandler(log_manager.get_handler())

def main():
    """主程序入口函数"""
    logger.info("程序启动")
    
    # 确保应用程序可以正确找到资源文件
    base_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base_dir)
    logger.info(f"工作目录: {base_dir}")
    
    # 创建Qt应用
    app = QApplication(sys.argv)
    app.setApplicationName("Cursor自动化管理工具")
    logger.info("Qt应用程序初始化完成")
    
    # 设置应用图标（如果有）
    # app.setWindowIcon(QIcon("resources/icons/app_icon.png"))
    
    # 初始化系统配置管理器
    system_config = SystemConfigManager()
    logger.info("系统配置管理器初始化完成")
    
    # 初始化数据库管理器
    db_manager = DbManager()
    cursor_db_path = system_config.get_config("cursor", "db_file", "")
    if cursor_db_path and os.path.exists(cursor_db_path):
        db_manager.set_db_path(cursor_db_path)
        logger.info(f"数据库路径设置为: {cursor_db_path}")
    else:
        logger.warning(f"数据库文件不存在: {cursor_db_path}")
    
    # 初始化进程管理器
    process_manager = CursorProcessManager()
    logger.info("进程管理器初始化完成")
    
    # 初始化浏览器管理器
    browser_manager = BrowserManager(system_config)
    logger.info("浏览器管理器初始化完成")
    
    # 初始化自动化管理器
    automation_manager = AutomationManager(browser_manager)
    logger.info("自动化管理器初始化完成")
    
    # 初始化账号管理器 (使用数据库版本)
    account_manager = AccountManagerDb()
    logger.info("数据库版账号管理器初始化完成")
    
    # 创建并显示主窗口
    main_window = MainWindow(browser_manager, automation_manager)
    # 设置账号管理器
    main_window.account_manager = account_manager
    logger.info("主窗口创建完成")
    
    # 将系统配置和数据库管理器传递给主窗口，用于后续设置各组件
    try:
        # 设置系统配置
        main_window.system_config = system_config
        
        # 设置配置相关组件
        if hasattr(main_window, 'system_config_tab'):
            main_window.system_config_tab.system_config = system_config
        
        # 尝试设置数据库相关组件
        if hasattr(main_window, 'db_tab'):
            # 确保db_tab可以访问数据库管理器和系统配置
            main_window.db_tab.db_manager = db_manager
            # 可选：设置父窗口引用
            main_window.db_tab.parent_window = main_window
        
        # 尝试连接信号
        if hasattr(main_window, 'system_config_tab') and hasattr(main_window, 'db_tab'):
            if hasattr(main_window.system_config_tab, 'config_updated') and hasattr(main_window.db_tab, 'load_db_info'):
                main_window.system_config_tab.config_updated.connect(main_window.db_tab.load_db_info)
                logger.info("组件信号连接完成")
    except Exception as e:
        logger.error(f"设置组件属性时出错: {e}")
    
    # 显示主窗口
    main_window.show()
    logger.info("主窗口显示完成")
    
    # 运行应用程序事件循环
    logger.info("开始运行事件循环")
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 