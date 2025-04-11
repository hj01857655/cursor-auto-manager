from typing import Any, List, Dict
from utils.config_manager import ConfigManager
import os
import time
import sqlite3
import platform
import logging

class SystemConfigManager(ConfigManager):
    """系统配置管理器类，继承自 ConfigManager"""
    
    def __init__(self, config_file: str = "config/system_config.json"):
        """初始化系统配置管理器
        
        Args:
            config_file: 配置文件路径
        """
        # 先调用父类的初始化
        super().__init__(config_file)
        
        # 设置日志记录器
        self.logger = logging.getLogger("SystemConfigManager")
        
        # 设置默认路径
        try:
            # 设置Cursor可执行文件路径
            if not self.get_config("cursor", "executable_path"):
                cursor_exe = self._find_cursor_exe()
                if cursor_exe:
                    self.set_config("cursor", "executable_path", cursor_exe)
                    self.logger.info(f"设置Cursor可执行文件路径: {cursor_exe}")
                else:
                    self.logger.warning("未找到Cursor可执行文件")
                    
            # 设置Cursor数据目录
            if not self.get_config("cursor", "data_dir"):
                cursor_data = self._find_cursor_data_dir()
                if cursor_data:
                    self.set_config("cursor", "data_dir", cursor_data)
                    self.logger.info(f"设置Cursor数据目录: {cursor_data}")
                else:
                    self.logger.warning("未找到Cursor数据目录")
                    
            # 设置Cursor配置文件
            if not self.get_config("cursor", "config_file"):
                cursor_config = self._find_cursor_config_file()
                if cursor_config:
                    self.set_config("cursor", "config_file", cursor_config)
                    self.logger.info(f"设置Cursor配置文件: {cursor_config}")
                else:
                    self.logger.warning("未找到Cursor配置文件")
                    
            # 设置Cursor数据库文件
            if not self.get_config("cursor", "db_file"):
                cursor_db = self._find_cursor_db_file()
                if cursor_db:
                    self.set_config("cursor", "db_file", cursor_db)
                    self.logger.info(f"设置Cursor数据库文件: {cursor_db}")
                else:
                    self.logger.warning("未找到Cursor数据库文件")
                    
            # 设置Chrome可执行文件路径
            if not self.get_config("chrome", "executable_path"):
                chrome_exe = self._find_chrome_exe()
                if chrome_exe:
                    self.set_config("chrome", "executable_path", chrome_exe)
                    self.logger.info(f"设置Chrome可执行文件路径: {chrome_exe}")
                else:
                    self.logger.warning("未找到Chrome可执行文件")
                    
            # 设置Chrome用户数据目录
            if not self.get_config("chrome", "user_data_dir"):
                chrome_data = self._find_chrome_user_data_dir()
                if chrome_data:
                    self.set_config("chrome", "user_data_dir", chrome_data)
                    self.logger.info(f"设置Chrome用户数据目录: {chrome_data}")
                else:
                    self.logger.warning("未找到Chrome用户数据目录")
                    
            # 设置Chrome自动化配置
            if not self.has_config("chrome.automation"):
                automation_config = {
                    "headless": False,  # 无头模式
                    "user_agent": {
                        "enabled": False,
                        "type": "default",  # default, custom, random, mobile, tablet
                        "custom": "",       # 自定义UA字符串
                        "presets": {
                            "chrome_windows": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                            "chrome_mac": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                            "chrome_android": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36",
                            "chrome_ios": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/122.0.0.0 Mobile/15E148 Safari/604.1"
                        }
                    },
                    "window_size": {
                        "width": 1920,
                        "height": 1080
                    },
                    "disable_gpu": True,         # 禁用GPU
                    "disable_images": False,     # 禁用图片加载
                    "incognito": False,         # 无痕模式
                    "disable_javascript": False, # 禁用JavaScript
                    "timeout": 30               # 页面加载超时时间(秒)
                }
                self.set_config("chrome", "automation", automation_config)
                self.logger.info("已设置Chrome自动化默认配置")
                    
        except Exception as e:
            self.error(f"初始化系统配置失败: {str(e)}")
        
    def warning(self, message: str):
        """记录警告日志
        
        Args:
            message: 警告消息
        """
        self.logger.warning(message)
        
    def error(self, message: str):
        """记录错误日志
        
        Args:
            message: 错误消息
        """
        self.logger.error(message)
        
    def get_config(self, section: str, key: str, default: Any = None) -> Any:
        """获取配置值
        
        Args:
            section: 配置节
            key: 配置键
            default: 默认值
            
        Returns:
            Any: 配置值
        """
        return super().get_config(f"{section}.{key}", default)
        
    def set_config(self, section: str, key: str, value: Any) -> bool:
        """设置配置值
        
        Args:
            section: 配置节
            key: 配置键
            value: 配置值
            
        Returns:
            bool: 是否成功设置
        """
        return super().set_config(f"{section}.{key}", value)

    def get_backups(self) -> List[Dict[str, str]]:
        """获取备份列表
        
        Returns:
            List[Dict[str, str]]: 备份列表，每个备份包含name、time和size信息
        """
        backup_dir = self.get_config("backup", "backup_dir", "backups")
        backups = []
        
        if os.path.exists(backup_dir):
            for file in os.listdir(backup_dir):
                file_path = os.path.join(backup_dir, file)
                if os.path.isfile(file_path):
                    stat = os.stat(file_path)
                    backups.append({
                        "name": file,
                        "time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime)),
                        "size": f"{stat.st_size / 1024:.1f} KB"
                    })
        
        return sorted(backups, key=lambda x: x["time"], reverse=True)

    def check_cursor_db_status(self) -> Dict[str, Any]:
        """检查Cursor数据库状态
        
        Returns:
            Dict[str, Any]: 包含数据库状态信息的字典
        """
        db_file = self.get_config("cursor", "db_file", "")
        result = {
            "valid": False,
            "status": "未找到数据库",
            "size": "0 KB",
            "tables": []
        }
        
        if not db_file or not os.path.exists(db_file):
            return result
            
        try:
            # 获取文件大小
            size = os.path.getsize(db_file)
            result["size"] = f"{size / 1024:.1f} KB"
            
            # 连接数据库
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            
            # 检查ItemTable表是否存在
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ItemTable'")
            if cursor.fetchone():
                result["tables"] = ["ItemTable"]
                
                # 获取ItemTable的记录数
                cursor.execute("SELECT COUNT(*) FROM ItemTable")
                count = cursor.fetchone()[0]
                result["valid"] = True
                result["status"] = f"正常 (共{count}条记录)"
            else:
                result["status"] = "未找到ItemTable表"
                
            conn.close()
        except sqlite3.Error as e:
            result["status"] = f"数据库错误: {str(e)}"
        except Exception as e:
            result["status"] = f"检查失败: {str(e)}"
            
        return result 