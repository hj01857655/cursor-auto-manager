from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, 
                        QDialogButtonBox, QFormLayout, QGroupBox, QCheckBox)
from PyQt5.QtCore import Qt
import json
import os

class SettingsDialog(QDialog):
    """设置对话框"""
    
    def __init__(self, parent=None):
        """初始化对话框
        
        Args:
            parent: 父窗口
        """
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.resize(400, 300)
        
        # 加载配置
        self.config = self.load_config()
        
        self.setup_ui()
        
    def load_config(self):
        """加载配置文件"""
        try:
            config_path = os.path.join("config", "config.json")
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"加载配置失败: {e}")
            return {}
            
    def save_config(self):
        """保存配置文件"""
        try:
            config_path = os.path.join("config", "config.json")
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False
        
    def setup_ui(self):
        """设置界面元素"""
        layout = QVBoxLayout(self)
        
        # 用户设置
        self.user_group = QGroupBox("用户设置")
        user_layout = QFormLayout()
        
        # 自动登录选项
        self.auto_login_check = QCheckBox("自动登录")
        self.auto_login_check.setChecked(self.config.get("user", {}).get("auto_login", False))
        user_layout.addRow("", self.auto_login_check)
        
        # 用户名密码
        self.username_input = QLineEdit(self.config.get("user", {}).get("username", ""))
        self.password_input = QLineEdit(self.config.get("user", {}).get("password", ""))
        self.password_input.setEchoMode(QLineEdit.Password)
        
        user_layout.addRow("用户名:", self.username_input)
        user_layout.addRow("密码:", self.password_input)
        
        self.user_group.setLayout(user_layout)
        layout.addWidget(self.user_group)
        
        # 浏览器设置
        self.browser_group = QGroupBox("浏览器设置")
        browser_layout = QFormLayout()
        
        self.default_url_input = QLineEdit(self.config.get("browser", {}).get("default_url", "https://cursor.com"))
        self.headless_check = QCheckBox("无头模式")
        self.headless_check.setChecked(self.config.get("browser", {}).get("headless", False))
        
        browser_layout.addRow("默认URL:", self.default_url_input)
        browser_layout.addRow("", self.headless_check)
        
        self.browser_group.setLayout(browser_layout)
        layout.addWidget(self.browser_group)
        
        # 按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel,
            Qt.Horizontal, self)
        buttons.accepted.connect(self.save_settings)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
    def save_settings(self):
        """保存设置"""
        # 更新用户配置
        if "user" not in self.config:
            self.config["user"] = {}
            
        self.config["user"]["auto_login"] = self.auto_login_check.isChecked()
        self.config["user"]["username"] = self.username_input.text()
        self.config["user"]["password"] = self.password_input.text()
        
        # 更新浏览器配置
        if "browser" not in self.config:
            self.config["browser"] = {}
            
        self.config["browser"]["default_url"] = self.default_url_input.text()
        self.config["browser"]["headless"] = self.headless_check.isChecked()
        
        # 保存配置文件
        if self.save_config():
            self.accept()
        else:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "错误", "保存配置失败") 