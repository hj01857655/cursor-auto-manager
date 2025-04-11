import json
import os
import platform
import sqlite3
import shutil
import subprocess
from typing import Dict, Any, Optional, List
from utils.logger import LoggerManager

class ConfigManager:
    """配置管理器类，用于管理应用程序的配置"""
    
    # 单例模式
    _instances = {}
    
    def __new__(cls, config_file: str = "config/config.json"):
        if config_file not in cls._instances:
            cls._instances[config_file] = super(ConfigManager, cls).__new__(cls)
            cls._instances[config_file]._initialized = False
        return cls._instances[config_file]
    
    def __init__(self, config_file: str = "config/config.json"):
        """初始化配置管理器
        
        Args:
            config_file: 配置文件路径
        """
        # 避免重复初始化
        if self._initialized:
            return
            
        self.config_file = config_file
        self.logger = LoggerManager()
        self.config: Dict[str, Any] = {}
        self.load_config()
        
        # 如果是系统配置文件，加载默认配置
        if "system_config.json" in config_file and not self.has_config("cursor"):
            self._create_default_config()
            
        # 初始化完成标记
        self._initialized = True
        
    def load_config(self) -> bool:
        """加载配置文件
        
        Returns:
            bool: 是否成功加载
        """
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                self.logger.info(f"成功加载配置文件: {self.config_file}")
                return True
            else:
                self.config = {}
                self.logger.warning(f"配置文件不存在: {self.config_file}")
                return False
        except Exception as e:
            self.logger.error(f"加载配置文件失败: {str(e)}")
            return False
            
    def save_config(self) -> bool:
        """保存配置到文件
        
        Returns:
            bool: 是否成功保存
        """
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            self.logger.info(f"成功保存配置文件: {self.config_file}")
            return True
        except Exception as e:
            self.logger.error(f"保存配置文件失败: {str(e)}")
            return False
            
    def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置值
        
        Args:
            key: 配置键，支持点号分隔的多级键（如 "database.host"）
            default: 默认值
            
        Returns:
            Any: 配置值
        """
        try:
            keys = key.split('.')
            value = self.config
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
            
    def set_config(self, key: str, value: Any) -> bool:
        """设置配置值
        
        Args:
            key: 配置键，支持点号分隔的多级键
            value: 配置值
            
        Returns:
            bool: 是否成功设置
        """
        try:
            keys = key.split('.')
            current = self.config
            for k in keys[:-1]:
                if k not in current:
                    current[k] = {}
                current = current[k]
            current[keys[-1]] = value
            self.logger.info(f"设置配置 {key} = {value}")
            return self.save_config()
        except Exception as e:
            self.logger.error(f"设置配置失败: {str(e)}")
            return False
            
    def update_config(self, updates: Dict[str, Any]) -> bool:
        """批量更新配置
        
        Args:
            updates: 要更新的配置字典
            
        Returns:
            bool: 是否成功更新
        """
        try:
            for key, value in updates.items():
                self.set_config(key, value)
            self.logger.info("批量更新配置成功")
            return True
        except Exception as e:
            self.logger.error(f"批量更新配置失败: {str(e)}")
            return False
            
    def delete_config(self, key: str) -> bool:
        """删除配置项
        
        Args:
            key: 要删除的配置键
            
        Returns:
            bool: 是否成功删除
        """
        try:
            keys = key.split('.')
            current = self.config
            for k in keys[:-1]:
                if k not in current:
                    return True
                current = current[k]
            if keys[-1] in current:
                del current[keys[-1]]
                self.logger.info(f"删除配置项: {key}")
                return self.save_config()
            return True
        except Exception as e:
            self.logger.error(f"删除配置项失败: {str(e)}")
            return False
            
    def get_all_config(self) -> Dict[str, Any]:
        """获取所有配置
        
        Returns:
            Dict[str, Any]: 所有配置的字典
        """
        return self.config.copy()
        
    def reset_config(self) -> bool:
        """重置配置为默认值
        
        Returns:
            bool: 是否成功重置
        """
        try:
            self.config = {}
            self.logger.info("配置已重置")
            return self.save_config()
        except Exception as e:
            self.logger.error(f"重置配置失败: {str(e)}")
            return False
            
    def has_config(self, key: str) -> bool:
        """检查配置项是否存在
        
        Args:
            key: 配置键
            
        Returns:
            bool: 是否存在
        """
        try:
            keys = key.split('.')
            current = self.config
            for k in keys:
                if k not in current:
                    return False
                current = current[k]
            return True
        except Exception:
            return False
            
    def get_config_keys(self, prefix: str = "") -> List[str]:
        """获取所有配置键
        
        Args:
            prefix: 键的前缀
            
        Returns:
            List[str]: 配置键列表
        """
        def _get_keys(d: Dict[str, Any], prefix: str) -> List[str]:
            keys = []
            for k, v in d.items():
                current_key = f"{prefix}.{k}" if prefix else k
                keys.append(current_key)
                if isinstance(v, dict):
                    keys.extend(_get_keys(v, current_key))
            return keys
            
        return _get_keys(self.config, prefix)
        
    # 系统特定配置方法
    def _create_default_config(self):
        """创建默认配置"""
        try:
            # 创建默认配置
            default_config = {
                "cursor": {
                    "executable_path": self._find_cursor_exe() or "",
                    "data_dir": self._find_cursor_data_dir() or "",
                    "config_file": self._find_cursor_config_file() or "",
                    "db_file": self._find_cursor_db_file() or ""
                },
                "chrome": {
                    "executable_path": self._find_chrome_exe() or "",
                    "user_data_dir": self._find_chrome_user_data_dir() or ""
                },
                "backup": {
                    "enabled": True,
                    "interval_days": 7,
                    "max_backups": 5,
                    "backup_dir": "backups"
                }
            }
            
            # 更新配置
            self.config.update(default_config)
            self.save_config()
            self.logger.info("已创建默认配置")
            
        except Exception as e:
            self.logger.error(f"创建默认配置失败: {str(e)}")
        
    def _find_cursor_exe(self):
        """查找Cursor可执行文件路径"""
        try:
            if platform.system() == "Windows":
                possible_paths = [
                    os.path.expandvars("%LOCALAPPDATA%\\Programs\\cursor\\Cursor.exe"),
                    os.path.expandvars("%LOCALAPPDATA%\\Programs\\Cursor\\Cursor.exe"),
                    os.path.expandvars("%USERPROFILE%\\AppData\\Local\\Programs\\cursor\\Cursor.exe"),
                    os.path.expandvars("%USERPROFILE%\\AppData\\Local\\Programs\\Cursor\\Cursor.exe"),
                    "C:\\Users\\Administrator\\AppData\\Local\\Programs\\cursor\\Cursor.exe",
                    "C:\\Program Files\\Cursor\\Cursor.exe",
                    "C:\\Program Files (x86)\\Cursor\\Cursor.exe"
                ]
            elif platform.system() == "Darwin":
                possible_paths = [
                    "/Applications/Cursor.app/Contents/MacOS/Cursor",
                    os.path.expanduser("~/Applications/Cursor.app/Contents/MacOS/Cursor")
                ]
            else:
                possible_paths = [
                    "/usr/bin/cursor",
                    "/usr/local/bin/cursor",
                    os.path.expanduser("~/.local/bin/cursor")
                ]
                
            for path in possible_paths:
                if os.path.exists(path):
                    self.logger.info(f"找到Cursor可执行文件: {path}")
                    return path
                    
            self.logger.warning("未找到Cursor可执行文件")
            return ""
        except Exception as e:
            self.logger.error(f"查找Cursor可执行文件失败: {str(e)}")
            return ""
        
    def _find_cursor_data_dir(self):
        """查找Cursor数据目录"""
        if platform.system() == "Windows":
            possible_paths = [
                os.path.expandvars("%APPDATA%\\Cursor"),
                os.path.expandvars("%USERPROFILE%\\AppData\\Roaming\\Cursor")
            ]
        elif platform.system() == "Darwin":
            possible_paths = [
                os.path.expanduser("~/Library/Application Support/Cursor")
            ]
        else:
            possible_paths = [
                os.path.expanduser("~/.config/Cursor")
            ]
            
        for path in possible_paths:
            if os.path.exists(path) and os.path.isdir(path):
                self.logger.info(f"找到Cursor数据目录: {path}")
                return path
                
        self.logger.warning("未找到Cursor数据目录")
        return ""
        
    def _find_cursor_config_file(self):
        """查找Cursor配置文件"""
        data_dir = self._find_cursor_data_dir()
        if not data_dir:
            return ""
            
        specific_paths = [
            os.path.expandvars("%APPDATA%\\Cursor\\User\\globalStorage\\storage.json"),
            os.path.expandvars("%USERPROFILE%\\AppData\\Roaming\\Cursor\\User\\globalStorage\\storage.json"),
            os.path.join(data_dir, "User", "globalStorage", "storage.json")
        ]
        
        for path in specific_paths:
            if os.path.exists(path) and os.path.isfile(path):
                self.logger.info(f"找到Cursor配置文件: {path}")
                return path
                
        possible_files = ["Config", "config.json", "settings.json", "preferences.json", "storage.json"]
        for file_name in possible_files:
            file_path = os.path.join(data_dir, file_name)
            if os.path.exists(file_path) and os.path.isfile(file_path):
                self.logger.info(f"找到Cursor配置文件: {file_path}")
                return file_path
                
        user_storage_dir = os.path.join(data_dir, "User", "globalStorage")
        if os.path.exists(user_storage_dir) and os.path.isdir(user_storage_dir):
            for file_name in os.listdir(user_storage_dir):
                if file_name.endswith(".json"):
                    file_path = os.path.join(user_storage_dir, file_name)
                    self.logger.info(f"找到Cursor配置文件: {file_path}")
                    return file_path
                    
        self.logger.warning("未找到Cursor配置文件")
        return ""
        
    def _find_cursor_db_file(self):
        """查找Cursor数据库文件"""
        data_dir = self._find_cursor_data_dir()
        if not data_dir:
            return ""
            
        specific_paths = [
            os.path.expandvars("%APPDATA%\\Cursor\\User\\globalStorage\\state.vscdb"),
            os.path.expandvars("%USERPROFILE%\\AppData\\Roaming\\Cursor\\User\\globalStorage\\state.vscdb"),
            os.path.join(data_dir, "User", "globalStorage", "state.vscdb")
        ]
        
        for path in specific_paths:
            if os.path.exists(path) and os.path.isfile(path):
                self.logger.info(f"找到Cursor数据库文件: {path}")
                return path
                
        possible_dirs = [
            os.path.join(data_dir, "Local Storage", "leveldb"),
            os.path.join(data_dir, "databases"),
            os.path.join(data_dir, "IndexedDB"),
            os.path.join(data_dir, "User", "globalStorage")
        ]
        
        for path in possible_dirs:
            if os.path.exists(path) and os.path.isdir(path):
                for root, _, files in os.walk(path):
                    for file in files:
                        if file.endswith((".sqlite", ".db", ".vscdb")):
                            file_path = os.path.join(root, file)
                            self.logger.info(f"找到Cursor数据库文件: {file_path}")
                            return file_path
                            
        self.logger.warning("未找到Cursor数据库文件")
        return ""
        
    def _find_chrome_exe(self):
        """查找Chrome浏览器可执行文件"""
        if platform.system() == "Windows":
            possible_paths = [
                "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                os.path.expandvars("%ProgramFiles%\\Google\\Chrome\\Application\\chrome.exe"),
                os.path.expandvars("%ProgramFiles(x86)%\\Google\\Chrome\\Application\\chrome.exe"),
                os.path.expandvars("%LOCALAPPDATA%\\Google\\Chrome\\Application\\chrome.exe")
            ]
        elif platform.system() == "Darwin":
            possible_paths = [
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                os.path.expanduser("~/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
            ]
        else:
            try:
                chrome_path = subprocess.check_output(['which', 'google-chrome'], universal_newlines=True).strip()
                if chrome_path:
                    return chrome_path
            except:
                pass
                
            possible_paths = [
                "/usr/bin/google-chrome",
                "/usr/bin/google-chrome-stable",
                "/usr/bin/chromium",
                "/usr/bin/chromium-browser"
            ]
            
        for path in possible_paths:
            if os.path.exists(path):
                self.logger.info(f"找到Chrome浏览器: {path}")
                return path
                
        self.logger.warning("未找到Chrome浏览器")
        return ""
        
    def _find_chrome_user_data_dir(self):
        """查找Chrome用户数据目录"""
        if platform.system() == "Windows":
            possible_paths = [
                os.path.expandvars("%LOCALAPPDATA%\\Google\\Chrome\\User Data")
            ]
        elif platform.system() == "Darwin":
            possible_paths = [
                os.path.expanduser("~/Library/Application Support/Google/Chrome")
            ]
        else:
            possible_paths = [
                os.path.expanduser("~/.config/google-chrome"),
                os.path.expanduser("~/.config/chromium")
            ]
            
        for path in possible_paths:
            if os.path.exists(path) and os.path.isdir(path):
                self.logger.info(f"找到Chrome用户数据目录: {path}")
                return path
                
        self.logger.warning("未找到Chrome用户数据目录")
        return ""
        
    def _find_backup_dir(self):
        """查找备份目录路径"""
        cursor_data_dir = self._find_cursor_data_dir()
        specific_paths = [
            os.path.expandvars("%APPDATA%\\Cursor\\User\\globalStorage\\backups"),
            os.path.expandvars("%USERPROFILE%\\AppData\\Roaming\\Cursor\\User\\globalStorage\\backups"),
            os.path.join(cursor_data_dir, "User", "globalStorage", "backups") if cursor_data_dir else None
        ]
        
        for path in specific_paths:
            if path and os.path.exists(path) and os.path.isdir(path):
                self.logger.info(f"找到备份目录: {path}")
                return path
                
        backup_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backups")
        if not os.path.exists(backup_dir):
            try:
                os.makedirs(backup_dir, exist_ok=True)
                self.logger.info(f"已创建备份目录: {backup_dir}")
            except Exception as e:
                self.logger.error(f"创建备份目录失败: {e}")
                
        return backup_dir
        
    def check_cursor_db_status(self):
        """检查Cursor数据库状态
        
        Returns:
            dict: 数据库状态信息
        """
        db_file = self.get_config("cursor.db_file", "")
        if not db_file or not os.path.exists(db_file):
            return {
                "status": "未找到数据库文件",
                "size": "0 KB",
                "tables": [],
                "valid": False
            }
            
        try:
            file_size = os.path.getsize(db_file)
            if file_size < 1024:
                size_str = f"{file_size} B"
            elif file_size < 1024 * 1024:
                size_str = f"{file_size / 1024:.2f} KB"
            else:
                size_str = f"{file_size / (1024 * 1024):.2f} MB"
                
            try:
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = [row[0] for row in cursor.fetchall()]
                conn.close()
                
                return {
                    "status": "正常",
                    "size": size_str,
                    "tables": tables,
                    "valid": True
                }
            except Exception as e:
                self.logger.error(f"连接数据库失败: {e}")
                return {
                    "status": f"无法连接: {str(e)}",
                    "size": size_str,
                    "tables": [],
                    "valid": False
                }
        except Exception as e:
            self.logger.error(f"检查数据库状态失败: {e}")
            return {
                "status": f"检查失败: {str(e)}",
                "size": "未知",
                "tables": [],
                "valid": False
            }
            
    def create_backup(self, backup_name=None):
        """创建数据库和配置文件备份
        
        Args:
            backup_name: 备份名称，如果为None则使用时间戳
            
        Returns:
            dict: 备份结果
        """
        try:
            backup_dir = self.get_config("backup.backup_dir", "backups")
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir, exist_ok=True)
                
            if not backup_name:
                import datetime
                backup_name = f"backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
            backup_path = os.path.join(backup_dir, backup_name)
            if not os.path.exists(backup_path):
                os.makedirs(backup_path, exist_ok=True)
                
            config_file = self.get_config("cursor.config_file", "")
            if config_file and os.path.exists(config_file):
                config_backup = os.path.join(backup_path, os.path.basename(config_file))
                shutil.copy2(config_file, config_backup)
                
            db_file = self.get_config("cursor.db_file", "")
            if db_file and os.path.exists(db_file):
                db_backup = os.path.join(backup_path, os.path.basename(db_file))
                shutil.copy2(db_file, db_backup)
                
            self.logger.info(f"已创建备份: {backup_path}")
            return {
                "success": True,
                "backup_path": backup_path,
                "message": f"已创建备份: {backup_path}"
            }
        except Exception as e:
            self.logger.error(f"创建备份失败: {e}")
            return {
                "success": False,
                "message": f"创建备份失败: {str(e)}"
            }
            
    def get_backups(self):
        """获取所有备份列表
        
        Returns:
            list: 备份列表
        """
        backup_dir = self.get_config("backup.backup_dir", "backups")
        if not os.path.exists(backup_dir):
            return []
            
        backups = []
        try:
            for item in os.listdir(backup_dir):
                item_path = os.path.join(backup_dir, item)
                if os.path.isdir(item_path):
                    has_backup_files = False
                    for root, _, files in os.walk(item_path):
                        if files:
                            has_backup_files = True
                            break
                            
                    if has_backup_files:
                        mtime = os.path.getmtime(item_path)
                        import datetime
                        mtime_str = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
                        
                        total_size = 0
                        for root, _, files in os.walk(item_path):
                            for file in files:
                                file_path = os.path.join(root, file)
                                total_size += os.path.getsize(file_path)
                                
                        if total_size < 1024:
                            size_str = f"{total_size} B"
                        elif total_size < 1024 * 1024:
                            size_str = f"{total_size / 1024:.2f} KB"
                        else:
                            size_str = f"{total_size / (1024 * 1024):.2f} MB"
                            
                        backups.append({
                            "name": item,
                            "path": item_path,
                            "time": mtime_str,
                            "size": size_str
                        })
                        
            backups.sort(key=lambda x: os.path.getmtime(x["path"]), reverse=True)
            return backups
        except Exception as e:
            self.logger.error(f"获取备份列表失败: {e}")
            return []
            
    def restore_backup(self, backup_path):
        """还原备份
        
        Args:
            backup_path: 备份路径
            
        Returns:
            dict: 还原结果
        """
        try:
            if not os.path.exists(backup_path) or not os.path.isdir(backup_path):
                return {
                    "success": False,
                    "message": "备份路径不存在"
                }
                
            config_backup = None
            db_backup = None
            
            for root, _, files in os.walk(backup_path):
                for file in files:
                    if file.endswith((".sqlite", ".db")):
                        db_backup = os.path.join(root, file)
                    elif file in ["Config", "config.json", "settings.json", "preferences.json"]:
                        config_backup = os.path.join(root, file)
                        
            if config_backup:
                config_file = self.get_config("cursor.config_file", "")
                if config_file and os.path.exists(os.path.dirname(config_file)):
                    shutil.copy2(config_backup, config_file)
                    self.logger.info(f"已还原配置文件: {config_file}")
                    
            if db_backup:
                db_file = self.get_config("cursor.db_file", "")
                if db_file and os.path.exists(os.path.dirname(db_file)):
                    shutil.copy2(db_backup, db_file)
                    self.logger.info(f"已还原数据库文件: {db_file}")
                    
            return {
                "success": True,
                "message": "备份还原成功"
            }
        except Exception as e:
            self.logger.error(f"还原备份失败: {e}")
            return {
                "success": False,
                "message": f"还原备份失败: {str(e)}"
            } 