import os
import json
from pathlib import Path

class Settings:
    """应用设置类"""
    
    def __init__(self):
        """初始化设置"""
        self.config_file = Path(os.path.dirname(os.path.abspath(__file__))) / "config.json"
        self.settings = self._load_settings()
    
    def _load_settings(self):
        """加载设置
        
        Returns:
            dict: 设置字典
        """
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as file:
                    return json.load(file)
            except Exception as e:
                print(f"加载设置失败: {e}")
                return self._get_default_settings()
        else:
            # 如果设置文件不存在，创建默认设置
            default_settings = self._get_default_settings()
            self.save_settings(default_settings)
            return default_settings
    
    def _get_default_settings(self):
        """获取默认设置
        
        Returns:
            dict: 默认设置字典
        """
        return {
            "browser": {
                "type": "chromium",
                "headless": False,
                "default_url": "https://cursor.sh"
            },
            "tasks": {
                "auto_run": False,
                "schedule": []
            }
        }
    
    def save_settings(self, settings=None):
        """保存设置
        
        Args:
            settings: 要保存的设置字典，如果为None则保存当前设置
        """
        if settings is None:
            settings = self.settings
        
        try:
            with open(self.config_file, "w", encoding="utf-8") as file:
                json.dump(settings, file, indent=4)
            self.settings = settings
            return True
        except Exception as e:
            print(f"保存设置失败: {e}")
            return False
    
    def get(self, key, default=None):
        """获取设置值
        
        Args:
            key: 设置键，支持层级访问，如 "browser.type"
            default: 默认值
            
        Returns:
            设置值
        """
        keys = key.split(".")
        value = self.settings
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key, value):
        """设置值
        
        Args:
            key: 设置键，支持层级访问，如 "browser.type"
            value: 设置值
            
        Returns:
            bool: 是否设置成功
        """
        keys = key.split(".")
        settings = self.settings
        
        # 遍历到最后一层
        for i, k in enumerate(keys[:-1]):
            if k not in settings:
                settings[k] = {}
            settings = settings[k]
        
        # 设置最后一层的值
        settings[keys[-1]] = value
        
        # 保存设置
        return self.save_settings() 