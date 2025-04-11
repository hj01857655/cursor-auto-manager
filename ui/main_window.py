from PyQt5.QtWidgets import (QMainWindow, QTabWidget, QVBoxLayout, QPushButton, QWidget, 
                        QLabel, QStatusBar, QHBoxLayout, QListWidget, QListWidgetItem, 
                        QGroupBox, QFormLayout, QLineEdit, QCheckBox, QMessageBox, QFileDialog)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QPalette, QColor
from core.browser import BrowserManager
from core.automation import AutomationManager
from core.process_manager import CursorProcessManager
from utils.system_config import SystemConfigManager
from core.db_manager import DbManager
from core.account_manager_db import AccountManagerDb
from utils.logger import LoggerManager
from ui.task_dialog import TaskDialog
from ui.process_tab import ProcessTab
from ui.log_tab import LogTab
from ui.system_config_tab import SystemConfigTab
from ui.db_tab import DbTab
from ui.account_tab import AccountTab
from ui.auth_dialog import AuthDialog
import json
import os
import platform
import webbrowser
import uuid
import datetime
import base64
import json

class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self, browser_manager, automation_manager):
        """初始化主窗口
        
        Args:
            browser_manager: 浏览器管理器实例
            automation_manager: 自动化管理器实例
        """
        super().__init__()
        
        self.browser_manager = browser_manager
        self.automation_manager = automation_manager
        # 创建账号管理器（如果外部没有传入，后续会被覆盖）
        self.account_manager = AccountManagerDb()
        self.logger_manager = LoggerManager()
        
        # 加载配置
        self.config = self.load_config()
        
        # 设置窗口样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
            }
            
            QWidget {
                font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif;
            }
            
            QTabWidget::pane {
                border: 1px solid #ddd;
                border-radius: 4px;
                background: white;
                margin-top: -1px;
            }
            
            QTabBar::tab {
                padding: 8px 16px;
                margin: 4px 2px 0px 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                border: 1px solid #ddd;
                border-bottom: none;
                background: #f8f9fa;
                min-width: 80px;
            }
            
            QTabBar::tab:selected {
                background: white;
                margin-bottom: -1px;
                padding-bottom: 9px;
                font-weight: bold;
                color: #4a90e2;
                border: 1px solid #ddd;
                border-bottom: 2px solid white;
            }
            
            QTabBar::tab:hover {
                background: #e9ecef;
                border: 1px solid #ccc;
                border-bottom: none;
            }
            
            QGroupBox {
                border: 2px solid #4a90e2;
                border-radius: 8px;
                margin-top: 12px;
                padding: 15px;
                background: white;
            }
            
            QGroupBox::title {
                color: #4a90e2;
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                background: white;
                font-weight: bold;
            }
            
            QPushButton {
                padding: 8px 16px;
                border-radius: 4px;
                border: none;
                color: white;
                font-weight: bold;
                min-width: 80px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4a90e2, stop:1 #357abd);
            }
            
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #357abd, stop:1 #2d6da3);
            }
            
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2d6da3, stop:1 #357abd);
            }
            
            QPushButton:disabled {
                background: #cccccc;
            }
            
            QLabel {
                color: #333333;
            }
            
            QLineEdit {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background: white;
                min-height: 20px;
            }
            
            QLineEdit:focus {
                border-color: #4a90e2;
            }
            
            QLineEdit:hover {
                border-color: #357abd;
            }
            
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                background: white;
            }
            
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #eee;
            }
            
            QListWidget::item:selected {
                background: #e7f1ff;
                color: #004085;
            }
            
            QListWidget::item:hover {
                background: #f8f9fa;
            }
            
            QStatusBar {
                background: #f8f9fa;
                color: #666666;
                border-top: 1px solid #ddd;
                padding: 5px;
            }
            
            QStatusBar QLabel {
                color: #666666;
            }
            
            QScrollBar:vertical {
                border: none;
                background: #f8f9fa;
                width: 10px;
                margin: 0px;
            }
            
            QScrollBar::handle:vertical {
                background: #c1c1c1;
                border-radius: 5px;
                min-height: 20px;
            }
            
            QScrollBar::handle:vertical:hover {
                background: #a8a8a8;
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            
            QScrollBar:horizontal {
                border: none;
                background: #f8f9fa;
                height: 10px;
                margin: 0px;
            }
            
            QScrollBar::handle:horizontal {
                background: #c1c1c1;
                border-radius: 5px;
                min-width: 20px;
            }
            
            QScrollBar::handle:horizontal:hover {
                background: #a8a8a8;
            }
            
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
        """)
        
        # 设置字体
        font = QFont("Microsoft YaHei UI", 9)
        self.setFont(font)
        
        self.setWindowTitle("Cursor自动化管理工具")
        self.setMinimumSize(1024, 800)  # 设置最小尺寸
        self.resize(1280, 960)  # 设置默认尺寸，增加高度
        
        # 创建主布局
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setSpacing(10)
        self.layout.setContentsMargins(10, 10, 10, 10)
        
        # 创建选项卡
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)
        self.tabs.setDocumentMode(True)
        self.layout.addWidget(self.tabs)
        
        # 创建授权登录选项卡
        self.auth_tab = QWidget()
        self.auth_tab_layout = QVBoxLayout(self.auth_tab)
        self.auth_tab_layout.setSpacing(10)
        self.auth_tab_layout.setContentsMargins(10, 10, 10, 10)
        self.tabs.addTab(self.auth_tab, "授权登录")
        
        # 添加账号信息显示区域
        self.account_info_group = QGroupBox("当前账号信息")
        account_info_layout = QFormLayout()
        account_info_layout.setSpacing(10)
        account_info_layout.setContentsMargins(10, 10, 10, 10)
        
        # 账号信息字段
        self.email_label = QLabel("未登录")
        self.status_label = QLabel("未知")
        self.last_login_label = QLabel("未知")
        self.expire_time_label = QLabel("未知")
        self.membership_label = QLabel("未知")
        
        account_info_layout.addRow("邮箱:", self.email_label)
        account_info_layout.addRow("状态:", self.status_label)
        account_info_layout.addRow("会员类型:", self.membership_label)
        account_info_layout.addRow("最后登录:", self.last_login_label)
        account_info_layout.addRow("过期时间:", self.expire_time_label)
        
        # 添加令牌信息文本框
        self.token_group = QGroupBox("令牌信息")
        token_layout = QVBoxLayout()
        
        self.refresh_token_text = QLineEdit()
        self.refresh_token_text.setReadOnly(True)
        self.refresh_token_text.setPlaceholderText("刷新令牌")
        token_layout.addWidget(self.refresh_token_text)
        
        self.access_token_text = QLineEdit()
        self.access_token_text.setReadOnly(True)
        self.access_token_text.setPlaceholderText("访问令牌")
        token_layout.addWidget(self.access_token_text)
        
        self.token_group.setLayout(token_layout)
        
        self.account_info_group.setLayout(account_info_layout)
        self.auth_tab_layout.addWidget(self.account_info_group)
        self.auth_tab_layout.addWidget(self.token_group)
        
        # 添加功能按钮区域
        self.functions_group = QGroupBox("功能操作")
        functions_layout = QVBoxLayout()
        functions_layout.setSpacing(10)
        functions_layout.setContentsMargins(10, 10, 10, 10)
        
        # 第一行按钮
        buttons_row1 = QHBoxLayout()
        buttons_row1.setSpacing(10)
        
        self.register_btn = QPushButton("注册账号")
        self.register_btn.clicked.connect(self.handle_register)
        buttons_row1.addWidget(self.register_btn)
        
        self.auth_btn = QPushButton("授权登录")
        self.auth_btn.clicked.connect(self.handle_auth)
        buttons_row1.addWidget(self.auth_btn)
        
        self.refresh_btn = QPushButton("刷新状态")
        self.refresh_btn.clicked.connect(self.refresh_account_status)
        buttons_row1.addWidget(self.refresh_btn)
        
        functions_layout.addLayout(buttons_row1)
        
        # 第二行按钮
        buttons_row2 = QHBoxLayout()
        buttons_row2.setSpacing(10)
        
        self.logout_btn = QPushButton("退出登录")
        self.logout_btn.clicked.connect(self.handle_logout)
        buttons_row2.addWidget(self.logout_btn)
        
        self.clear_cache_btn = QPushButton("清除缓存")
        self.clear_cache_btn.clicked.connect(self.handle_clear_cache)
        buttons_row2.addWidget(self.clear_cache_btn)
        
        functions_layout.addLayout(buttons_row2)
        
        self.functions_group.setLayout(functions_layout)
        self.auth_tab_layout.addWidget(self.functions_group)
        
        # 添加状态显示
        self.auth_status_label = QLabel("就绪")
        self.auth_status_label.setAlignment(Qt.AlignCenter)
        self.auth_tab_layout.addWidget(self.auth_status_label)
        
        # 连接信号
        self.account_manager.account_list_updated.connect(self.update_account_info)
        
        # 创建其他选项卡
        self.setup_other_tabs()
        
        # 初始化状态栏
        self.statusBar().showMessage("就绪")
        
        # 设置状态栏样式
        self.statusBar().setStyleSheet("""
            QStatusBar {
                background-color: #f0f0f0;
                color: #666666;
                border-top: 1px solid #cccccc;
            }
        """)
        
        # 加载授权数据 - 在UI组件创建完成后再加载
        self.load_auth_data()
    
    def setup_other_tabs(self):
        """设置其他选项卡"""
        # 创建账号管理选项卡
        self.account_tab = AccountTab(self.account_manager)
        self.tabs.addTab(self.account_tab, "账号管理")
        
        # 创建进程管理选项卡
        self.process_tab = ProcessTab()
        self.tabs.addTab(self.process_tab, "进程管理")
        
        # 创建日志管理选项卡
        self.log_tab = LogTab(self.logger_manager)
        self.tabs.addTab(self.log_tab, "日志管理")
        
        # 创建系统配置选项卡
        self.system_config_tab = SystemConfigTab()
        self.tabs.addTab(self.system_config_tab, "系统配置")
        
        # 创建数据库管理选项卡
        self.db_tab = DbTab()
        self.tabs.addTab(self.db_tab, "数据库管理")
    
    def load_config(self):
        """加载配置文件"""
        try:
            config_path = os.path.join("config", "config.json")
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"加载配置失败: {e}")
            return {}
    
    def load_auth_data(self):
        """加载授权数据"""
        try:
            # 从JSON文件加载授权数据
            auth_data = self.account_manager.load_cursor_auth_from_json()
            
            if not auth_data:
                self.logger_manager.info("未找到授权数据文件，将尝试从数据库加载")
                return
                
            # 从授权数据中提取信息
            email = auth_data.get("cursorAuth/cachedEmail", "未知")
            signup_type = auth_data.get("cursorAuth/cachedSignUpType", "未知")
            membership = auth_data.get("cursorAuth/stripeMembershipType", "未知")
            
            # 解析过期时间
            expire_date = None
            refresh_token = auth_data.get("cursorAuth/refreshToken")
            access_token = auth_data.get("cursorAuth/accessToken")
            
            if refresh_token or access_token:
                token = refresh_token or access_token
                try:
                    # 获取JWT有效载荷部分
                    payload = token.split('.')[1]
                    # 添加padding
                    payload += '=' * (4 - len(payload) % 4)
                    # 解码
                    decoded = base64.b64decode(payload).decode('utf-8')
                    # 解析JSON
                    payload_data = json.loads(decoded)
                    
                    # 获取过期时间
                    if 'exp' in payload_data:
                        exp_timestamp = payload_data['exp']
                        expire_date = datetime.datetime.fromtimestamp(exp_timestamp)
                except Exception as e:
                    self.logger_manager.error(f"解析令牌失败: {e}")
            
            # 构建用户信息
            user_info = {
                "id": str(uuid.uuid4()),
                "email": email,
                "auth_source": signup_type,
                "membership": membership,
                "last_login": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # 添加令牌信息
            if refresh_token:
                user_info["refresh_token"] = refresh_token
            if access_token:
                user_info["access_token"] = access_token
                
            # 添加过期时间和状态
            if expire_date:
                user_info["expire_time"] = expire_date.strftime("%Y-%m-%d %H:%M:%S")
                
                # 计算剩余天数
                days_left = (expire_date - datetime.datetime.now()).days
                if days_left <= 0:
                    user_info["status"] = "已过期"
                elif days_left <= 7:
                    user_info["status"] = f"即将过期({days_left}天)"
                else:
                    user_info["status"] = "正常"
            elif membership == "pro":
                user_info["expire_time"] = "永久"
                user_info["status"] = "永久有效"
            elif membership == "free_trial":
                # 设置试用期为14天
                trial_expire_date = datetime.datetime.now() + datetime.timedelta(days=14)
                user_info["expire_time"] = trial_expire_date.strftime("%Y-%m-%d")
                user_info["status"] = "试用期"
            else:
                user_info["expire_time"] = "未知"
                user_info["status"] = "未知期限"
                
            # 使用授权码
            user_info["auth_code"] = "从配置文件加载"
                
            # 添加账号到账号管理器
            self.account_manager.add_account(user_info)
            
            # 更新UI显示
            self.auth_status_label.setText(f"已从配置文件加载账号: {email}")
            self.auth_status_label.setStyleSheet("color: #28a745;")  # 绿色，表示成功
            
            self.logger_manager.info(f"从配置文件成功加载授权数据: {email}")
            
        except Exception as e:
            import traceback
            print(f"加载授权数据失败: {str(e)}")
            print(traceback.format_exc())
            self.logger_manager.error(f"加载授权数据失败: {e}")
        
    def update_account_info(self, accounts):
        """更新账号信息显示"""
        current_account = self.account_manager.get_current_account()
        
        if current_account:
            # 获取并显示邮箱与账号来源
            email = current_account.get('email', '未知')
            source = current_account.get('auth_source', '')
            if source:
                self.email_label.setText(f"{email} ({source})")
            else:
                self.email_label.setText(email)
            
            # 设置状态标签的颜色
            status = current_account.get('status', '未知')
            
            # 如果有会员信息，添加到状态中
            membership = current_account.get('membership', '')
            if membership:
                if membership == 'pro':
                    status_text = f"{status} (Pro会员)"
                    self.membership_label.setText("Pro会员 (永久)")
                    self.membership_label.setStyleSheet("color: #28a745; font-weight: bold;")  # 绿色加粗
                elif membership == 'free_trial':
                    status_text = f"{status} (试用版)"
                    self.membership_label.setText("试用版")
                    self.membership_label.setStyleSheet("color: #17a2b8;")  # 蓝色
                else:
                    status_text = f"{status} ({membership})"
                    self.membership_label.setText(membership)
                    self.membership_label.setStyleSheet("")  # 默认样式
            else:
                status_text = status
                self.membership_label.setText("未知")
                self.membership_label.setStyleSheet("color: #ffc107;")  # 黄色
                
            self.status_label.setText(status_text)
            
            # 根据状态设置颜色
            if status == "正常" or status == "已登录" or status == "永久有效":
                self.status_label.setStyleSheet("color: #28a745;")  # 绿色
            elif status == "试用期":
                self.status_label.setStyleSheet("color: #17a2b8;")  # 蓝色
            elif status == "未登录" or status == "未知" or status == "未知期限":
                self.status_label.setStyleSheet("color: #ffc107;")  # 黄色
            elif "过期" in status or "错误" in status:
                self.status_label.setStyleSheet("color: #dc3545;")  # 红色
            elif "即将过期" in status:
                self.status_label.setStyleSheet("color: #fd7e14;")  # 橙色
            
            # 显示会员类型和过期时间
            expire_time = current_account.get('expire_time', '未知')
            
            self.last_login_label.setText(current_account.get('last_login', '未知'))
            
            # 根据会员类型设置不同的显示
            if membership == 'pro':
                self.expire_time_label.setText("永久 (Pro会员)")
                self.expire_time_label.setStyleSheet("color: #28a745; font-weight: bold;")  # 绿色加粗
            elif membership == 'free_trial':
                self.expire_time_label.setText(f"{expire_time} (试用版)")
                self.expire_time_label.setStyleSheet("color: #17a2b8;")  # 蓝色
            elif "过期" in status:
                self.expire_time_label.setText(f"{expire_time} (已过期)")
                self.expire_time_label.setStyleSheet("color: #dc3545;")  # 红色
            elif "即将过期" in status:
                self.expire_time_label.setText(f"{expire_time} (即将过期)")
                self.expire_time_label.setStyleSheet("color: #fd7e14;")  # 橙色
            else:
                self.expire_time_label.setText(expire_time)
                self.expire_time_label.setStyleSheet("")  # 默认样式
                
            # 显示令牌信息
            access_token = current_account.get('access_token', '')
            refresh_token = current_account.get('refresh_token', '')
            
            if refresh_token:
                self.refresh_token_text.setText(refresh_token)
            else:
                self.refresh_token_text.setText("")
                self.refresh_token_text.setPlaceholderText("无刷新令牌")
                
            if access_token:
                self.access_token_text.setText(access_token)
            else:
                self.access_token_text.setText("")
                self.access_token_text.setPlaceholderText("无访问令牌")
                
            # 如果有令牌信息，更新到状态栏
            if access_token or refresh_token:
                token_info = ""
                if refresh_token:
                    token_info += f"刷新令牌: {refresh_token[:20]}...{refresh_token[-10:]}"
                if access_token:
                    if token_info:
                        token_info += " | "
                    token_info += f"访问令牌: {access_token[:20]}...{access_token[-10:]}"
                
                self.statusBar().showMessage(token_info)
                
        else:
            self.email_label.setText("未登录")
            self.status_label.setText("未知")
            self.status_label.setStyleSheet("color: #ffc107;")  # 黄色
            self.last_login_label.setText("未知")
            self.expire_time_label.setText("未知")
            self.expire_time_label.setStyleSheet("")  # 重置样式
            self.membership_label.setText("未知")
            self.membership_label.setStyleSheet("color: #ffc107;")  # 黄色
            self.refresh_token_text.setText("")
            self.refresh_token_text.setPlaceholderText("无刷新令牌")
            self.access_token_text.setText("")
            self.access_token_text.setPlaceholderText("无访问令牌")
            self.statusBar().showMessage("就绪")
        
    def handle_register(self):
        """处理注册账号"""
        try:
            # 先跳转到首页
            home_url = AuthDialog.BASE_URL
            self.auth_status_label.setText("正在跳转到首页...")
            self.auth_status_label.setStyleSheet("color: #17a2b8;")  # 蓝色，表示进行中
            webbrowser.open(home_url)
            
            # 创建一个短暂的延迟，让浏览器有时间加载首页
            QTimer.singleShot(1500, lambda: self._redirect_to_register())
        except Exception as e:
            QMessageBox.warning(self, "错误", f"打开首页失败: {str(e)}")
            self.auth_status_label.setText("打开首页失败")
            self.auth_status_label.setStyleSheet("color: #dc3545;")  # 红色，表示失败
            
    def _redirect_to_register(self):
        """重定向到注册页面"""
        try:
            # 打开注册页面
            register_url = AuthDialog.REGISTER_URL
            webbrowser.open(register_url)
            self.auth_status_label.setText("已打开注册页面")
            self.auth_status_label.setStyleSheet("color: #17a2b8;")  # 蓝色，表示进行中
        except Exception as e:
            QMessageBox.warning(self, "错误", f"打开注册页面失败: {str(e)}")
            self.auth_status_label.setText("打开注册页面失败")
            self.auth_status_label.setStyleSheet("color: #dc3545;")  # 红色，表示失败
        
    def handle_auth(self):
        """处理授权登录"""
        dialog = AuthDialog(self)
        dialog.auth_success.connect(self.on_auth_success)
        dialog.exec_()
        
    def on_auth_success(self, user_info):
        """授权成功回调
        
        Args:
            user_info: 用户信息字典
        """
        self.auth_status_label.setText("授权登录成功")
        self.auth_status_label.setStyleSheet("color: #28a745;")  # 绿色，表示成功
        
        # 更新账号信息显示
        self.email_label.setText(user_info.get("email", "未知"))
        self.status_label.setText(user_info.get("status", "未知"))
        self.last_login_label.setText("刚刚")
        self.expire_time_label.setText(user_info.get("expire_time", "未知"))
        
        # 根据状态设置颜色
        status = user_info.get("status", "未知")
        if status == "正常":
            self.status_label.setStyleSheet("color: #28a745;")  # 绿色
        elif status == "未知":
            self.status_label.setStyleSheet("color: #ffc107;")  # 黄色
        else:
            self.status_label.setStyleSheet("color: #dc3545;")  # 红色
            
        # 将用户信息添加到账号管理器
        try:
            # 确保用户信息包含唯一ID
            if "id" not in user_info:
                user_info["id"] = str(uuid.uuid4())
                
            # 添加当前时间作为最后登录时间
            user_info["last_login"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 添加账号到账号管理器
            self.account_manager.add_account(user_info)
            
            # 通知成功
            self.auth_status_label.setText(f"授权登录成功，账号已添加: {user_info.get('email')}")
        except Exception as e:
            import traceback
            print(f"添加账号到账号管理器失败: {str(e)}")
            print(traceback.format_exc())
            self.auth_status_label.setText(f"授权登录成功，但添加账号失败: {str(e)}")
            self.auth_status_label.setStyleSheet("color: #ffc107;")  # 黄色，表示警告
        
    def handle_logout(self):
        """处理退出登录"""
        self.auth_status_label.setText("正在退出登录...")
        self.auth_status_label.setStyleSheet("color: #17a2b8;")  # 蓝色，表示进行中
        
        # 获取当前账号
        current_account = self.account_manager.get_current_account()
        if not current_account:
            self.auth_status_label.setText("退出失败：当前未登录任何账号")
            self.auth_status_label.setStyleSheet("color: #ffc107;")  # 黄色，表示警告
            return
            
        # 确认是否退出
        email = current_account.get("email", "未知账号")
        ret = QMessageBox.question(
            self,
            "确认退出",
            f"确定要退出当前账号 {email} 吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if ret == QMessageBox.No:
            self.auth_status_label.setText("已取消退出操作")
            self.auth_status_label.setStyleSheet("color: #17a2b8;")  # 蓝色
            return
            
        # 执行退出操作
        if self.account_manager.logout():
            self.auth_status_label.setText(f"已成功退出账号: {email}")
            self.auth_status_label.setStyleSheet("color: #28a745;")  # 绿色，表示成功
            
            # 刷新账号信息显示
            self.update_account_info([])
        else:
            self.auth_status_label.setText("退出登录失败")
            self.auth_status_label.setStyleSheet("color: #dc3545;")  # 红色，表示失败
        
    def handle_clear_cache(self):
        """处理清除缓存"""
        self.auth_status_label.setText("正在清除缓存...")
        self.auth_status_label.setStyleSheet("color: #17a2b8;")  # 蓝色，表示进行中
        
    def refresh_account_status(self):
        """刷新账号状态"""
        self.account_manager.refresh_account_status()
        self.auth_status_label.setText("已刷新账号状态")
        self.auth_status_label.setStyleSheet("color: #28a745;")  # 绿色，表示成功
        
    def closeEvent(self, event):
        """窗口关闭事件处理"""
        # 保存配置
        try:
            config_path = os.path.join("config", "config.json")
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"保存配置失败: {e}")
            
        event.accept()