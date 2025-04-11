from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                        QLabel, QTableWidget, QTableWidgetItem, QGroupBox,
                        QFormLayout, QLineEdit, QTabWidget, QMessageBox,
                        QFileDialog, QTextEdit, QListWidget, QListWidgetItem,
                        QCheckBox, QSpinBox, QDialog, QDialogButtonBox, QHeaderView,
                        QComboBox)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QSize
from PyQt5.QtGui import QIcon, QFont
from utils.system_config import SystemConfigManager
import os
import platform
import sqlite3

class SystemConfigTab(QWidget):
    """系统配置选项卡"""
    
    # 配置更新信号
    config_updated = pyqtSignal()
    
    def __init__(self, parent=None):
        """初始化系统配置选项卡
        
        Args:
            parent: 父窗口
        """
        super().__init__(parent)
        
        # 获取系统配置管理器
        self.system_config = SystemConfigManager()
        
        # 创建UI
        self.setup_ui()
        
        # 加载配置数据
        self.load_config_data()
        
        # 设置Cursor和Chrome路径的默认值
        self.set_default_paths()
        
        # 创建定时器，定期刷新数据库状态
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.check_db_status)
        self.refresh_timer.start(30000)  # 每30秒更新一次
        
        # 设置主窗口样式
        self.setStyleSheet("""
            QWidget {
                font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif;
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
            
            QLineEdit {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background: white;
                min-height: 20px;
                selection-background-color: #4a90e2;
            }
            
            QLineEdit:focus {
                border: 2px solid #4a90e2;
                background-color: #fafafa;
            }
            
            QLineEdit:hover {
                border-color: #357abd;
            }
            
            QPushButton {
                padding: 8px 16px;
                border-radius: 4px;
                border: 1px solid #357abd;
                color: white;
                font-weight: bold;
                min-width: 80px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4a90e2, stop:1 #357abd);
            }
            
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #357abd, stop:1 #2d6da3);
                border: 1px solid #2d6da3;
            }
            
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2d6da3, stop:1 #357abd);
                border: 1px solid #2d6da3;
                padding: 9px 15px 7px 17px;
            }
            
            QLabel {
                color: #333;
            }
            
            QTabWidget::pane {
                border: 1px solid #ddd;
                border-radius: 4px;
                background: white;
            }
            
            QTabBar::tab {
                padding: 8px 16px;
                margin: 4px 2px 0px 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                border: 1px solid #ddd;
                border-bottom: none;
                background: #f8f9fa;
            }
            
            QTabBar::tab:selected {
                background: white;
                margin-bottom: -1px;
                padding-bottom: 9px;
                border: 1px solid #ddd;
                border-bottom: 2px solid white;
            }
            
            QTabBar::tab:hover {
                background: #e9ecef;
                border: 1px solid #ccc;
            }
            
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                background: white;
            }
            
            QListWidget::item {
                padding: 6px;
                border-bottom: 1px solid #eee;
            }
            
            QListWidget::item:selected {
                background: #e7f1ff;
                color: #004085;
                border: 1px solid #b8daff;
            }
            
            QListWidget::item:hover {
                background: #f8f9fa;
                border: 1px solid #eee;
            }
            
            QSpinBox {
                padding: 5px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background: white;
            }
            
            QSpinBox:hover {
                border-color: #357abd;
            }
            
            QSpinBox:focus {
                border: 2px solid #4a90e2;
                background-color: #fafafa;
            }
            
            QCheckBox {
                spacing: 8px;
            }
            
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #ddd;
                border-radius: 3px;
                background: white;
            }
            
            QCheckBox::indicator:checked {
                background-color: #4a90e2;
                border-color: #4a90e2;
            }
            
            QCheckBox::indicator:hover {
                border-color: #4a90e2;
            }
            
            QComboBox {
                padding: 5px;
                border: 1px solid #ddd;
                border-radius: 4px;
                min-width: 100px;
                background: white;
            }
            
            QComboBox:hover {
                border-color: #357abd;
            }
            
            QComboBox:focus {
                border: 2px solid #4a90e2;
                background-color: #fafafa;
            }
        """)
        
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        
        # 创建顶部按钮行
        buttons_layout = QHBoxLayout()
        
        button_style = """
            QPushButton {
                padding: 8px 16px;
                background-color: #4a90e2;
                color: white;
                border: none;
                border-radius: 4px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #357abd;
            }
            QPushButton:pressed {
                background-color: #2d6da3;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """
        
        self.save_btn = QPushButton("保存配置")
        self.save_btn.clicked.connect(self.save_config)
        self.save_btn.setStyleSheet(button_style)
        buttons_layout.addWidget(self.save_btn)
        
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.clicked.connect(self.load_config_data)
        self.refresh_btn.setStyleSheet(button_style)
        buttons_layout.addWidget(self.refresh_btn)
        
        self.backup_btn = QPushButton("创建备份")
        self.backup_btn.clicked.connect(self.create_backup)
        self.backup_btn.setStyleSheet(button_style)
        buttons_layout.addWidget(self.backup_btn)
        
        # 添加自动检测按钮
        self.detect_paths_btn = QPushButton("自动检测路径")
        self.detect_paths_btn.clicked.connect(self.detect_paths)
        self.detect_paths_btn.setStyleSheet(button_style)
        buttons_layout.addWidget(self.detect_paths_btn)
        
        buttons_layout.addStretch()
        
        layout.addLayout(buttons_layout)
        
        # 创建选项卡样式
        self.config_tabs = QTabWidget()
        self.config_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 10px;
                background: white;
            }
            QTabBar::tab {
                background-color: #f0f0f0;
                border: 1px solid #cccccc;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border: 1px solid #cccccc;
                border-bottom: 2px solid white;
            }
            QTabBar::tab:hover {
                background-color: #e0e0e0;
                border: 1px solid #bbbbbb;
            }
        """)
        layout.addWidget(self.config_tabs)
        
        # Cursor配置选项卡样式
        group_style = """
            QGroupBox {
                border: 2px solid #4a90e2;
                border-radius: 6px;
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
            }
        """
        
        input_style = """
            QLineEdit {
                padding: 5px;
                border: 1px solid #ddd;
                border-radius: 4px;
                min-height: 25px;
                background: white;
            }
            QLineEdit:focus {
                border: 2px solid #4a90e2;
                background-color: #fafafa;
            }
        """
        
        browse_button_style = """
            QPushButton {
                padding: 5px 10px;
                background-color: #f0f0f0;
                border: 1px solid #ddd;
                border-radius: 4px;
                color: #333;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
                border: 1px solid #ccc;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
                border: 1px solid #bbb;
                padding: 6px 9px 4px 11px;
            }
        """
        
        # 创建Cursor配置选项卡
        self.cursor_tab = QWidget()
        cursor_layout = QVBoxLayout(self.cursor_tab)
        
        # Cursor可执行文件路径组
        cursor_path_group = QGroupBox("Cursor可执行文件")
        cursor_path_group.setStyleSheet(group_style)
        cursor_path_layout = QHBoxLayout()
        
        self.cursor_exe_path = QLineEdit()
        self.cursor_exe_path.setPlaceholderText("请选择Cursor可执行文件路径")
        self.cursor_exe_path.setStyleSheet(input_style)
        self.cursor_exe_path.textChanged.connect(lambda: self.save_btn.setEnabled(True))
        cursor_path_layout.addWidget(self.cursor_exe_path)
        
        self.cursor_path_browse_btn = QPushButton("浏览...")
        self.cursor_path_browse_btn.setStyleSheet(browse_button_style)
        self.cursor_path_browse_btn.clicked.connect(self.browse_cursor_path)
        cursor_path_layout.addWidget(self.cursor_path_browse_btn)
        
        cursor_path_group.setLayout(cursor_path_layout)
        cursor_layout.addWidget(cursor_path_group)
        
        # Cursor数据目录
        cursor_data_group = QGroupBox("Cursor数据目录")
        cursor_data_group.setStyleSheet(group_style)
        cursor_data_layout = QHBoxLayout()
        
        self.cursor_data_path = QLineEdit()
        self.cursor_data_path.setPlaceholderText("请选择Cursor数据目录路径")
        self.cursor_data_path.setStyleSheet(input_style)
        self.cursor_data_path.textChanged.connect(lambda: self.save_btn.setEnabled(True))
        cursor_data_layout.addWidget(self.cursor_data_path)
        
        self.cursor_data_browse_btn = QPushButton("浏览...")
        self.cursor_data_browse_btn.setStyleSheet(browse_button_style)
        self.cursor_data_browse_btn.clicked.connect(self.browse_cursor_data)
        cursor_data_layout.addWidget(self.cursor_data_browse_btn)
        
        cursor_data_group.setLayout(cursor_data_layout)
        cursor_layout.addWidget(cursor_data_group)
        
        # Cursor配置文件
        cursor_config_group = QGroupBox("Cursor配置文件")
        cursor_config_group.setStyleSheet(group_style)
        cursor_config_layout = QHBoxLayout()
        
        self.cursor_config_path = QLineEdit()
        self.cursor_config_path.setPlaceholderText("请选择Cursor配置文件路径")
        self.cursor_config_path.setStyleSheet(input_style)
        self.cursor_config_path.textChanged.connect(lambda: self.save_btn.setEnabled(True))
        cursor_config_layout.addWidget(self.cursor_config_path)
        
        self.cursor_config_browse_btn = QPushButton("浏览...")
        self.cursor_config_browse_btn.setStyleSheet(browse_button_style)
        self.cursor_config_browse_btn.clicked.connect(self.browse_cursor_config)
        cursor_config_layout.addWidget(self.cursor_config_browse_btn)
        
        self.cursor_config_view_btn = QPushButton("查看")
        self.cursor_config_view_btn.setStyleSheet(browse_button_style)
        self.cursor_config_view_btn.clicked.connect(self.view_cursor_config)
        cursor_config_layout.addWidget(self.cursor_config_view_btn)
        
        cursor_config_group.setLayout(cursor_config_layout)
        cursor_layout.addWidget(cursor_config_group)
        
        # Cursor数据库文件
        cursor_db_group = QGroupBox("Cursor数据库")
        cursor_db_group.setStyleSheet(group_style)
        cursor_db_layout = QVBoxLayout()
        
        cursor_db_path_layout = QHBoxLayout()
        
        self.cursor_db_path = QLineEdit()
        self.cursor_db_path.setPlaceholderText("请选择Cursor数据库文件路径")
        self.cursor_db_path.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                min-height: 25px;
                background: white;
            }
            QLineEdit:focus {
                border: 2px solid #4a90e2;
                background-color: #fafafa;
            }
            QLineEdit:hover {
                border: 1px solid #4a90e2;
            }
        """)
        self.cursor_db_path.textChanged.connect(lambda: self.save_btn.setEnabled(True))
        cursor_db_path_layout.addWidget(self.cursor_db_path)
        
        self.cursor_db_browse_btn = QPushButton("浏览...")
        self.cursor_db_browse_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                background-color: #f0f0f0;
                border: 1px solid #ddd;
                border-radius: 4px;
                color: #333;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
                border: 1px solid #4a90e2;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
                border: 1px solid #357abd;
                padding: 9px 15px 7px 17px;
            }
        """)
        self.cursor_db_browse_btn.clicked.connect(self.browse_cursor_db)
        cursor_db_path_layout.addWidget(self.cursor_db_browse_btn)
        
        cursor_db_layout.addLayout(cursor_db_path_layout)
        
        # 数据库状态信息
        db_status_layout = QFormLayout()
        db_status_layout.setSpacing(10)
        
        self.db_status_label = QLabel("未知")
        self.db_status_label.setStyleSheet("""
            QLabel {
                color: #666;
                padding: 5px;
                border-radius: 4px;
                background: #f8f9fa;
            }
        """)
        
        self.db_size_label = QLabel("未知")
        self.db_size_label.setStyleSheet("""
            QLabel {
                color: #666;
                padding: 5px;
                border-radius: 4px;
                background: #f8f9fa;
            }
        """)
        
        status_label = QLabel("状态:")
        status_label.setStyleSheet("color: #333; font-weight: bold;")
        size_label = QLabel("大小:")
        size_label.setStyleSheet("color: #333; font-weight: bold;")
        
        db_status_layout.addRow(status_label, self.db_status_label)
        db_status_layout.addRow(size_label, self.db_size_label)
        
        cursor_db_layout.addLayout(db_status_layout)
        
        # 数据库表信息
        tables_label = QLabel("数据库表:")
        tables_label.setStyleSheet("color: #333; font-weight: bold; margin-top: 10px;")
        cursor_db_layout.addWidget(tables_label)
        
        self.db_tables_list = QListWidget()
        self.db_tables_list.setMaximumHeight(100)
        self.db_tables_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                background: white;
                padding: 5px;
            }
            QListWidget::item {
                padding: 5px;
                border-radius: 2px;
            }
            QListWidget::item:selected {
                background: #e7f1ff;
                color: #004085;
            }
            QListWidget::item:hover {
                background: #f8f9fa;
            }
        """)
        cursor_db_layout.addWidget(self.db_tables_list)
        
        cursor_db_group.setLayout(cursor_db_layout)
        cursor_layout.addWidget(cursor_db_group)
        
        # 机器ID配置组
        machine_id_group = QGroupBox("Cursor机器ID配置")
        machine_id_group.setStyleSheet(group_style)
        machine_id_group_layout = QVBoxLayout()
        
        # 机器ID路径
        machine_id_path_layout = QHBoxLayout()
        
        self.machine_id_path = QLineEdit()
        self.machine_id_path.setPlaceholderText("请输入Cursor机器ID文件路径")
        self.machine_id_path.textChanged.connect(lambda: self.save_btn.setEnabled(True))
        self.machine_id_path.setStyleSheet(input_style)
        machine_id_path_layout.addWidget(self.machine_id_path)
        
        self.machine_id_browse_btn = QPushButton("浏览...")
        self.machine_id_browse_btn.setStyleSheet(browse_button_style)
        self.machine_id_browse_btn.clicked.connect(self.browse_machine_id_path)
        machine_id_path_layout.addWidget(self.machine_id_browse_btn)
        
        self.machine_id_view_btn = QPushButton("查看内容")
        self.machine_id_view_btn.setStyleSheet(browse_button_style)
        self.machine_id_view_btn.clicked.connect(self.view_machine_id)
        machine_id_path_layout.addWidget(self.machine_id_view_btn)
        
        # 机器ID说明
        machine_id_info = QLabel("机器ID用于Cursor唯一标识您的设备，更改此路径可能会影响授权状态。")
        machine_id_info.setWordWrap(True)
        machine_id_info.setStyleSheet("color: #666; font-style: italic; padding: 5px;")
        
        machine_id_group_layout.addLayout(machine_id_path_layout)
        machine_id_group_layout.addWidget(machine_id_info)
        
        machine_id_group.setLayout(machine_id_group_layout)
        cursor_layout.addWidget(machine_id_group)
        
        # Cursor其他配置文件组
        cursor_other_group = QGroupBox("Cursor其他路径配置")
        cursor_other_group.setStyleSheet(group_style)
        cursor_other_layout = QFormLayout()
        cursor_other_layout.setSpacing(10)
        
        # 资源路径
        self.resources_path = QLineEdit()
        self.resources_path.setPlaceholderText("请输入Cursor资源文件路径")
        self.resources_path.textChanged.connect(lambda: self.save_btn.setEnabled(True))
        self.resources_path.setStyleSheet(input_style)
        
        resources_layout = QHBoxLayout()
        resources_layout.addWidget(self.resources_path)
        
        self.resources_browse_btn = QPushButton("浏览...")
        self.resources_browse_btn.setStyleSheet(browse_button_style)
        self.resources_browse_btn.clicked.connect(self.browse_resources_path)
        resources_layout.addWidget(self.resources_browse_btn)
        
        # 更新程序路径
        self.updater_path = QLineEdit()
        self.updater_path.setPlaceholderText("请输入Cursor更新程序路径")
        self.updater_path.textChanged.connect(lambda: self.save_btn.setEnabled(True))
        self.updater_path.setStyleSheet(input_style)
        
        updater_layout = QHBoxLayout()
        updater_layout.addWidget(self.updater_path)
        
        self.updater_browse_btn = QPushButton("浏览...")
        self.updater_browse_btn.setStyleSheet(browse_button_style)
        self.updater_browse_btn.clicked.connect(self.browse_updater_path)
        updater_layout.addWidget(self.updater_browse_btn)
        
        # 更新配置路径
        self.update_yml_path = QLineEdit()
        self.update_yml_path.setPlaceholderText("请输入Cursor更新配置文件路径")
        self.update_yml_path.textChanged.connect(lambda: self.save_btn.setEnabled(True))
        self.update_yml_path.setStyleSheet(input_style)
        
        update_yml_layout = QHBoxLayout()
        update_yml_layout.addWidget(self.update_yml_path)
        
        self.update_yml_browse_btn = QPushButton("浏览...")
        self.update_yml_browse_btn.setStyleSheet(browse_button_style)
        self.update_yml_browse_btn.clicked.connect(self.browse_update_yml_path)
        update_yml_layout.addWidget(self.update_yml_browse_btn)
        
        # 产品配置路径
        self.product_json_path = QLineEdit()
        self.product_json_path.setPlaceholderText("请输入Cursor产品配置文件路径")
        self.product_json_path.textChanged.connect(lambda: self.save_btn.setEnabled(True))
        self.product_json_path.setStyleSheet(input_style)
        
        product_json_layout = QHBoxLayout()
        product_json_layout.addWidget(self.product_json_path)
        
        self.product_json_browse_btn = QPushButton("浏览...")
        self.product_json_browse_btn.setStyleSheet(browse_button_style)
        self.product_json_browse_btn.clicked.connect(self.browse_product_json_path)
        product_json_layout.addWidget(self.product_json_browse_btn)
        
        # 添加到布局
        cursor_other_layout.addRow("资源路径:", resources_layout)
        cursor_other_layout.addRow("更新程序路径:", updater_layout)
        cursor_other_layout.addRow("更新配置路径:", update_yml_layout)
        cursor_other_layout.addRow("产品配置路径:", product_json_layout)
        
        cursor_other_group.setLayout(cursor_other_layout)
        cursor_layout.addWidget(cursor_other_group)
        
        # 添加提示文本
        help_text = QLabel("提示：请确保所有路径正确设置，以确保程序正常运行")
        help_text.setStyleSheet("color: #666; padding: 5px; font-style: italic;")
        cursor_layout.addWidget(help_text)
        
        # 添加到选项卡
        self.config_tabs.addTab(self.cursor_tab, "Cursor配置")
        
        # 创建Chrome配置选项卡
        self.chrome_tab = QWidget()
        chrome_layout = QVBoxLayout(self.chrome_tab)
        
        # Chrome可执行文件路径
        chrome_path_group = QGroupBox("本地Chrome浏览器可执行文件")
        chrome_path_group.setStyleSheet(group_style)
        chrome_path_layout = QHBoxLayout()
        
        self.chrome_exe_path = QLineEdit()
        self.chrome_exe_path.setPlaceholderText("请选择本地Chrome浏览器可执行文件路径")
        self.chrome_exe_path.setStyleSheet(input_style)
        self.chrome_exe_path.textChanged.connect(lambda: self.save_btn.setEnabled(True))
        chrome_path_layout.addWidget(self.chrome_exe_path)
        
        self.chrome_path_browse_btn = QPushButton("浏览...")
        self.chrome_path_browse_btn.setStyleSheet(browse_button_style)
        self.chrome_path_browse_btn.clicked.connect(self.browse_chrome_path)
        chrome_path_layout.addWidget(self.chrome_path_browse_btn)
        
        chrome_path_group.setLayout(chrome_path_layout)
        chrome_layout.addWidget(chrome_path_group)
        
        # Chrome用户数据目录
        chrome_data_group = QGroupBox("Chrome用户数据目录")
        chrome_data_group.setStyleSheet(group_style)
        chrome_data_layout = QHBoxLayout()
        
        self.chrome_data_path = QLineEdit()
        self.chrome_data_path.setPlaceholderText("请选择Chrome用户数据目录路径")
        self.chrome_data_path.setStyleSheet(input_style)
        self.chrome_data_path.textChanged.connect(lambda: self.save_btn.setEnabled(True))
        chrome_data_layout.addWidget(self.chrome_data_path)
        
        self.chrome_data_browse_btn = QPushButton("浏览...")
        self.chrome_data_browse_btn.setStyleSheet(browse_button_style)
        self.chrome_data_browse_btn.clicked.connect(self.browse_chrome_data)
        chrome_data_layout.addWidget(self.chrome_data_browse_btn)
        
        chrome_data_group.setLayout(chrome_data_layout)
        chrome_layout.addWidget(chrome_data_group)
        
        # 添加提示
        chrome_note = QLabel("注意: 本地Chrome浏览器路径将用于自动化任务和页面控制，请确保指定正确的chrome.exe文件路径")
        chrome_note.setStyleSheet("""
            QLabel {
                color: #6c757d;
                padding: 10px;
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 4px;
                margin-top: 10px;
                margin-bottom: 10px;
            }
        """)
        chrome_layout.addWidget(chrome_note)
        
        # 填充空白
        chrome_layout.addStretch()
        
        # Chrome自动化配置
        automation_group = QGroupBox("浏览器自动化配置")
        automation_group.setStyleSheet("""
            QGroupBox {
                border: 2px solid #4a90e2;
                border-radius: 6px;
                margin-top: 12px;
                padding: 15px;
            }
            QGroupBox::title {
                color: #4a90e2;
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                background: white;
            }
        """)
        automation_layout = QVBoxLayout()
        automation_layout.setSpacing(15)
        
        # User-Agent配置
        ua_group = QGroupBox("浏览器标识(User-Agent)")
        ua_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #ccc;
                border-radius: 4px;
                margin-top: 10px;
                padding: 10px;
                background: white;
            }
            QGroupBox::title {
                color: #333;
                background: white;
            }
        """)
        
        ua_layout = QFormLayout()
        ua_layout.setSpacing(10)
        
        # 先创建所有UA相关的控件
        self.ua_enabled = QCheckBox("启用自定义浏览器标识")
        self.ua_type = QComboBox()
        self.ua_type.addItems(["系统默认", "自定义标识", "随机标识", "移动设备", "平板设备"])
        self.ua_custom = QLineEdit()
        self.ua_custom.setPlaceholderText("请输入自定义的浏览器标识字符串")
        self.ua_presets = QComboBox()
        self.ua_presets.addItems([
            "Windows Chrome浏览器",
            "Mac Chrome浏览器",
            "Android Chrome浏览器",
            "iOS Chrome浏览器"
        ])
        
        # 然后设置控件样式
        for widget in [self.ua_type, self.ua_custom, self.ua_presets]:
            widget.setStyleSheet("""
                QComboBox, QLineEdit {
                    padding: 5px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    min-width: 200px;
                    background: white;
                }
                QComboBox:focus, QLineEdit:focus {
                    border: 2px solid #4a90e2;
                    background-color: #fafafa;
                }
                QComboBox:hover, QLineEdit:hover {
                    border-color: #357abd;
                }
            """)
            
        # 添加到布局
        ua_layout.addRow(self.ua_enabled)
        ua_layout.addRow("标识类型:", self.ua_type)
        ua_layout.addRow("自定义标识:", self.ua_custom)
        ua_layout.addRow("快速选择:", self.ua_presets)
        
        ua_group.setLayout(ua_layout)
        automation_layout.addWidget(ua_group)
        
        # 其他自动化选项
        options_group = QGroupBox("浏览器行为设置")
        options_group.setStyleSheet(ua_group.styleSheet())
        options_layout = QFormLayout()
        options_layout.setSpacing(10)
        
        # 创建选项组
        behavior_options = QHBoxLayout()
        behavior_options.setSpacing(20)
        
        self.headless_mode = QCheckBox("无界面模式")
        self.disable_gpu = QCheckBox("禁用GPU")
        self.disable_images = QCheckBox("禁用图片")
        self.incognito_mode = QCheckBox("无痕模式")
        self.disable_js = QCheckBox("禁用JavaScript")
        
        # 设置复选框样式
        checkbox_style = """
            QCheckBox {
                spacing: 5px;
                color: #333;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 2px solid #ddd;
                border-radius: 3px;
                background: white;
            }
            QCheckBox::indicator:checked {
                background-color: #4a90e2;
                border-color: #4a90e2;
            }
            QCheckBox::indicator:hover {
                border-color: #4a90e2;
            }
        """
        
        # 设置复选框样式
        for checkbox in [self.headless_mode, self.disable_gpu, self.disable_images,
                        self.incognito_mode, self.disable_js]:
            checkbox.setStyleSheet(checkbox_style)
        
        behavior_options.addWidget(self.headless_mode)
        behavior_options.addWidget(self.disable_gpu)
        behavior_options.addWidget(self.disable_images)
        behavior_options.addStretch()
        
        privacy_options = QHBoxLayout()
        privacy_options.setSpacing(20)
        privacy_options.addWidget(self.incognito_mode)
        privacy_options.addWidget(self.disable_js)
        
        # 添加使用本地Chrome浏览器选项
        self.use_local_browser = QCheckBox("使用指定的本地Chrome浏览器")
        self.use_local_browser.setStyleSheet(checkbox_style)
        privacy_options.addWidget(self.use_local_browser)
        
        privacy_options.addStretch()
        
        options_layout.addRow("运行模式:", behavior_options)
        options_layout.addRow("隐私设置:", privacy_options)
        
        # 超时和窗口大小设置
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(10, 300)
        self.timeout_spin.setValue(30)
        self.timeout_spin.setSuffix(" 秒")
        
        window_size_layout = QHBoxLayout()
        self.window_width = QSpinBox()
        self.window_width.setRange(800, 3840)
        self.window_width.setValue(1920)
        self.window_height = QSpinBox()
        self.window_height.setRange(600, 2160)
        self.window_height.setValue(1080)
        
        # 设置数字输入框样式
        spinbox_style = """
            QSpinBox {
                padding: 5px;
                border: 1px solid #ddd;
                border-radius: 4px;
                min-width: 80px;
            }
            QSpinBox:focus {
                border-color: #4a90e2;
            }
        """
        for spinbox in [self.timeout_spin, self.window_width, self.window_height]:
            spinbox.setStyleSheet(spinbox_style)
        
        window_size_layout.addWidget(self.window_width)
        window_size_layout.addWidget(QLabel("×"))
        window_size_layout.addWidget(self.window_height)
        window_size_layout.addStretch()
        
        options_layout.addRow("超时时间:", self.timeout_spin)
        options_layout.addRow("窗口大小:", window_size_layout)
        
        options_group.setLayout(options_layout)
        automation_layout.addWidget(options_group)
        
        # 添加说明文本
        help_text = QLabel("提示：无界面模式适合自动化任务，禁用图片和JavaScript可以提高加载速度。请确保正确设置本地Chrome浏览器路径（chrome.exe）以确保自动化功能正常工作。")
        help_text.setStyleSheet("color: #666; padding: 5px;")
        help_text.setWordWrap(True)
        automation_layout.addWidget(help_text)
        
        automation_group.setLayout(automation_layout)
        chrome_layout.addWidget(automation_group)
        
        self.config_tabs.addTab(self.chrome_tab, "Chrome配置")
        
        # 创建备份选项卡
        self.backup_tab = QWidget()
        backup_layout = QVBoxLayout(self.backup_tab)
        
        # 备份设置
        backup_settings_group = QGroupBox("备份设置")
        backup_settings_group.setStyleSheet(group_style)
        backup_settings_layout = QFormLayout()
        
        self.backup_enabled_check = QCheckBox("启用自动备份")
        self.backup_enabled_check.stateChanged.connect(lambda: self.save_btn.setEnabled(True))
        
        self.backup_interval_spin = QSpinBox()
        self.backup_interval_spin.setRange(1, 90)
        self.backup_interval_spin.setSuffix(" 天")
        self.backup_interval_spin.valueChanged.connect(lambda: self.save_btn.setEnabled(True))
        
        self.backup_max_spin = QSpinBox()
        self.backup_max_spin.setRange(1, 50)
        self.backup_max_spin.valueChanged.connect(lambda: self.save_btn.setEnabled(True))
        
        self.backup_dir_input = QLineEdit()
        self.backup_dir_input.setPlaceholderText("请选择备份目录路径")
        self.backup_dir_input.textChanged.connect(lambda: self.save_btn.setEnabled(True))
        
        self.backup_dir_browse_btn = QPushButton("浏览...")
        self.backup_dir_browse_btn.clicked.connect(self.browse_backup_dir)
        
        backup_settings_layout.addRow("", self.backup_enabled_check)
        backup_settings_layout.addRow("备份间隔:", self.backup_interval_spin)
        backup_settings_layout.addRow("最大备份数:", self.backup_max_spin)
        
        backup_dir_layout = QHBoxLayout()
        backup_dir_layout.addWidget(self.backup_dir_input)
        backup_dir_layout.addWidget(self.backup_dir_browse_btn)
        
        backup_settings_layout.addRow("备份目录:", backup_dir_layout)
        
        backup_settings_group.setLayout(backup_settings_layout)
        backup_layout.addWidget(backup_settings_group)
        
        # 备份列表
        backup_list_group = QGroupBox("备份列表")
        backup_list_layout = QVBoxLayout()
        
        self.backup_list = QTableWidget(0, 3)
        self.backup_list.setHorizontalHeaderLabels(["名称", "时间", "大小"])
        self.backup_list.horizontalHeader().setStretchLastSection(True)
        self.backup_list.setSelectionBehavior(QTableWidget.SelectRows)
        self.backup_list.setEditTriggers(QTableWidget.NoEditTriggers)
        
        backup_list_layout.addWidget(self.backup_list)
        
        # 备份操作按钮
        backup_buttons_layout = QHBoxLayout()
        
        self.create_backup_btn = QPushButton("创建备份")
        self.create_backup_btn.clicked.connect(self.create_backup)
        backup_buttons_layout.addWidget(self.create_backup_btn)
        
        self.restore_backup_btn = QPushButton("还原备份")
        self.restore_backup_btn.clicked.connect(self.restore_backup)
        backup_buttons_layout.addWidget(self.restore_backup_btn)
        
        self.refresh_backups_btn = QPushButton("刷新列表")
        self.refresh_backups_btn.clicked.connect(self.load_backups)
        backup_buttons_layout.addWidget(self.refresh_backups_btn)
        
        backup_list_layout.addLayout(backup_buttons_layout)
        
        backup_list_group.setLayout(backup_list_layout)
        backup_layout.addWidget(backup_list_group)
        
        self.config_tabs.addTab(self.backup_tab, "备份与还原")
        
    def load_config_data(self):
        """加载配置数据"""
        # 加载Cursor配置
        cursor_exe = self.system_config.get_config("cursor", "executable_path", "")
        self.cursor_exe_path.setText(cursor_exe)
        
        cursor_data = self.system_config.get_config("cursor", "data_dir", "")
        self.cursor_data_path.setText(cursor_data)
        
        cursor_config = self.system_config.get_config("cursor", "config_file", "")
        self.cursor_config_path.setText(cursor_config)
        
        cursor_db = self.system_config.get_config("cursor", "db_file", "")
        self.cursor_db_path.setText(cursor_db)
        
        # 加载Cursor其他路径配置
        machine_id_path = self.system_config.get_config("cursor", "machine_id_path", "")
        self.machine_id_path.setText(machine_id_path)
        
        resources_path = self.system_config.get_config("cursor", "resources_path", "")
        self.resources_path.setText(resources_path)
        
        updater_path = self.system_config.get_config("cursor", "updater_path", "")
        self.updater_path.setText(updater_path)
        
        update_yml_path = self.system_config.get_config("cursor", "update_yml_path", "")
        self.update_yml_path.setText(update_yml_path)
        
        product_json_path = self.system_config.get_config("cursor", "product_json_path", "")
        self.product_json_path.setText(product_json_path)
        
        # 检查数据库状态
        self.check_db_status()
        
        # 加载Chrome配置
        chrome_exe = self.system_config.get_config("chrome", "executable_path", "")
        self.chrome_exe_path.setText(chrome_exe)
        
        chrome_data = self.system_config.get_config("chrome", "user_data_dir", "")
        self.chrome_data_path.setText(chrome_data)
        
        # 加载备份配置
        enabled = self.system_config.get_config("backup", "enabled", False)
        self.backup_enabled_check.setChecked(enabled)
        
        interval = self.system_config.get_config("backup", "interval_days", 7)
        self.backup_interval_spin.setValue(interval)
        
        max_backups = self.system_config.get_config("backup", "max_backups", 5)
        self.backup_max_spin.setValue(max_backups)
        
        backup_dir = self.system_config.get_config("backup", "backup_dir", "backups")
        self.backup_dir_input.setText(backup_dir)
        
        # 加载备份列表
        self.load_backups()
        
        # 加载Chrome自动化配置
        automation = self.system_config.get_config("chrome", "automation", {})
        
        # User-Agent设置
        ua_config = automation.get("user_agent", {})
        self.ua_enabled.setChecked(ua_config.get("enabled", False))
        
        ua_type = ua_config.get("type", "default")
        type_map = {
            "default": 0,
            "custom": 1,
            "random": 2,
            "mobile": 3,
            "tablet": 4
        }
        self.ua_type.setCurrentIndex(type_map.get(ua_type, 0))
        
        self.ua_custom.setText(ua_config.get("custom", ""))
        
        # 其他自动化选项
        self.headless_mode.setChecked(automation.get("headless", False))
        self.disable_gpu.setChecked(automation.get("disable_gpu", True))
        self.disable_images.setChecked(automation.get("disable_images", False))
        self.incognito_mode.setChecked(automation.get("incognito", False))
        self.disable_js.setChecked(automation.get("disable_javascript", False))
        self.timeout_spin.setValue(automation.get("timeout", 30))
        
        # 使用本地浏览器选项
        self.use_local_browser.setChecked(automation.get("use_local_browser", True))
        
        window_size = automation.get("window_size", {"width": 1920, "height": 1080})
        self.window_width.setValue(window_size.get("width", 1920))
        self.window_height.setValue(window_size.get("height", 1080))
        
        # 禁用保存按钮
        self.save_btn.setEnabled(False)
        
    def save_config(self):
        """保存配置"""
        # 保存Cursor配置
        self.system_config.set_config("cursor", "executable_path", self.cursor_exe_path.text())
        self.system_config.set_config("cursor", "data_dir", self.cursor_data_path.text())
        self.system_config.set_config("cursor", "config_file", self.cursor_config_path.text())
        self.system_config.set_config("cursor", "db_file", self.cursor_db_path.text())
        
        # 保存Cursor其他路径配置
        self.system_config.set_config("cursor", "machine_id_path", self.machine_id_path.text())
        self.system_config.set_config("cursor", "resources_path", self.resources_path.text())
        self.system_config.set_config("cursor", "updater_path", self.updater_path.text())
        self.system_config.set_config("cursor", "update_yml_path", self.update_yml_path.text())
        self.system_config.set_config("cursor", "product_json_path", self.product_json_path.text())
        
        # 保存Chrome配置
        self.system_config.set_config("chrome", "executable_path", self.chrome_exe_path.text())
        self.system_config.set_config("chrome", "user_data_dir", self.chrome_data_path.text())
        
        # 保存备份配置
        self.system_config.set_config("backup", "enabled", self.backup_enabled_check.isChecked())
        self.system_config.set_config("backup", "interval_days", self.backup_interval_spin.value())
        self.system_config.set_config("backup", "max_backups", self.backup_max_spin.value())
        self.system_config.set_config("backup", "backup_dir", self.backup_dir_input.text())
        
        # 保存Chrome自动化配置
        type_map = {
            0: "default",
            1: "custom",
            2: "random",
            3: "mobile",
            4: "tablet"
        }
        
        automation_config = {
            "headless": self.headless_mode.isChecked(),
            "user_agent": {
                "enabled": self.ua_enabled.isChecked(),
                "type": type_map.get(self.ua_type.currentIndex(), "default"),
                "custom": self.ua_custom.text(),
                "presets": {
                    "chrome_windows": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                    "chrome_mac": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                    "chrome_android": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36",
                    "chrome_ios": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/122.0.0.0 Mobile/15E148 Safari/604.1"
                }
            },
            "window_size": {
                "width": self.window_width.value(),
                "height": self.window_height.value()
            },
            "disable_gpu": self.disable_gpu.isChecked(),
            "disable_images": self.disable_images.isChecked(),
            "incognito": self.incognito_mode.isChecked(),
            "disable_javascript": self.disable_js.isChecked(),
            "timeout": self.timeout_spin.value(),
            "use_local_browser": self.use_local_browser.isChecked()
        }
        
        self.system_config.set_config("chrome", "automation", automation_config)
        
        # 禁用保存按钮
        self.save_btn.setEnabled(False)
        
        QMessageBox.information(self, "成功", "系统配置已保存")
        
    def check_db_status(self):
        """检查数据库状态"""
        status = self.system_config.check_cursor_db_status()
        
        # 更新UI
        self.db_status_label.setText(status["status"])
        self.db_size_label.setText(status["size"])
        
        # 更新表列表
        self.db_tables_list.clear()
        for table in status["tables"]:
            self.db_tables_list.addItem(table)
            
        # 设置状态标签颜色
        if status["valid"]:
            self.db_status_label.setStyleSheet("color: green;")
        else:
            self.db_status_label.setStyleSheet("color: red;")
            
    def browse_cursor_path(self):
        """浏览Cursor可执行文件路径"""
        file_filter = "可执行文件 (*.exe)" if platform.system() == "Windows" else "可执行文件 (*.*)"
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "选择Cursor可执行文件", 
            self.cursor_exe_path.text(),
            file_filter
        )
        if file_path:
            self.cursor_exe_path.setText(file_path)
            
    def browse_cursor_data(self):
        """浏览Cursor数据目录"""
        directory = QFileDialog.getExistingDirectory(
            self, 
            "选择Cursor数据目录", 
            self.cursor_data_path.text()
        )
        if directory:
            self.cursor_data_path.setText(directory)
            
    def browse_cursor_config(self):
        """浏览Cursor配置文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "选择Cursor配置文件", 
            self.cursor_config_path.text()
        )
        if file_path:
            self.cursor_config_path.setText(file_path)
            
    def browse_cursor_db(self):
        """浏览Cursor数据库文件"""
        file_filter = "数据库文件 (*.sqlite *.db)"
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "选择Cursor数据库文件", 
            self.cursor_db_path.text(),
            file_filter
        )
        if file_path:
            self.cursor_db_path.setText(file_path)
            
    def browse_chrome_path(self):
        """浏览本地Chrome浏览器可执行文件路径"""
        file_filter = "可执行文件 (*.exe)" if platform.system() == "Windows" else "可执行文件 (*.*)"
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "选择本地Chrome浏览器可执行文件", 
            self.chrome_exe_path.text(),
            file_filter
        )
        if file_path:
            self.chrome_exe_path.setText(file_path)
            
    def browse_chrome_data(self):
        """浏览Chrome用户数据目录"""
        directory = QFileDialog.getExistingDirectory(
            self, 
            "选择Chrome用户数据目录", 
            self.chrome_data_path.text()
        )
        if directory:
            self.chrome_data_path.setText(directory)
            
    def browse_machine_id_path(self):
        """浏览Cursor机器ID文件路径"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "选择Cursor机器ID文件", 
            self.machine_id_path.text(),
            "所有文件 (*.*)"
        )
        if file_path:
            self.machine_id_path.setText(file_path)
            
            # 询问是否查看文件内容
            if QMessageBox.question(
                self,
                "查看机器ID",
                "是否查看机器ID文件内容？\n注意：机器ID是Cursor的唯一标识，请谨慎操作。",
                QMessageBox.Yes | QMessageBox.No
            ) == QMessageBox.Yes:
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    dialog = QDialog(self)
                    dialog.setWindowTitle("机器ID")
                    dialog.resize(400, 200)
                    
                    layout = QVBoxLayout(dialog)
                    
                    text_edit = QTextEdit()
                    text_edit.setReadOnly(True)
                    text_edit.setFont(QFont("Courier New", 10))
                    text_edit.setText(content)
                    
                    layout.addWidget(text_edit)
                    
                    # 添加提示信息
                    warning_label = QLabel("警告：此ID用于标识您的设备，修改可能导致授权失效")
                    warning_label.setStyleSheet("color: red; font-weight: bold;")
                    layout.addWidget(warning_label)
                    
                    button_box = QDialogButtonBox(QDialogButtonBox.Close)
                    button_box.rejected.connect(dialog.reject)
                    layout.addWidget(button_box)
                    
                    dialog.exec_()
                except Exception as e:
                    QMessageBox.warning(self, "错误", f"无法读取机器ID文件: {str(e)}")
            
    def browse_resources_path(self):
        """浏览Cursor资源文件路径"""
        directory = QFileDialog.getExistingDirectory(
            self, 
            "选择Cursor资源目录", 
            self.resources_path.text()
        )
        if directory:
            self.resources_path.setText(directory)
            
    def browse_updater_path(self):
        """浏览Cursor更新程序路径"""
        directory = QFileDialog.getExistingDirectory(
            self, 
            "选择Cursor更新程序目录", 
            self.updater_path.text()
        )
        if directory:
            self.updater_path.setText(directory)
            
    def browse_update_yml_path(self):
        """浏览Cursor更新配置文件路径"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "选择Cursor更新配置文件", 
            self.update_yml_path.text(),
            "YAML文件 (*.yml);;所有文件 (*.*)"
        )
        if file_path:
            self.update_yml_path.setText(file_path)
            
    def browse_product_json_path(self):
        """浏览Cursor产品配置文件路径"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "选择Cursor产品配置文件", 
            self.product_json_path.text(),
            "JSON文件 (*.json);;所有文件 (*.*)"
        )
        if file_path:
            self.product_json_path.setText(file_path)
            
    def browse_backup_dir(self):
        """浏览备份目录"""
        directory = QFileDialog.getExistingDirectory(
            self, 
            "选择备份目录", 
            self.backup_dir_input.text()
        )
        if directory:
            self.backup_dir_input.setText(directory)
            
    def view_cursor_config(self):
        """查看Cursor配置文件内容"""
        config_file = self.cursor_config_path.text()
        if not config_file or not os.path.exists(config_file):
            QMessageBox.warning(self, "错误", "配置文件不存在")
            return
            
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                content = f.read()
                
            dialog = QDialog(self)
            dialog.setWindowTitle(f"配置文件: {os.path.basename(config_file)}")
            dialog.resize(600, 400)
            
            layout = QVBoxLayout(dialog)
            
            text_edit = QTextEdit()
            text_edit.setReadOnly(True)
            text_edit.setFont(QFont("Courier New", 10))
            text_edit.setText(content)
            
            layout.addWidget(text_edit)
            
            button_box = QDialogButtonBox(QDialogButtonBox.Close)
            button_box.rejected.connect(dialog.reject)
            layout.addWidget(button_box)
            
            dialog.exec_()
        except Exception as e:
            QMessageBox.warning(self, "错误", f"无法读取配置文件: {str(e)}")
            
    def load_backups(self):
        """加载备份列表"""
        backups = self.system_config.get_backups()
        
        self.backup_list.setRowCount(0)
        for backup in backups:
            row_position = self.backup_list.rowCount()
            self.backup_list.insertRow(row_position)
            
            self.backup_list.setItem(row_position, 0, QTableWidgetItem(backup["name"]))
            self.backup_list.setItem(row_position, 1, QTableWidgetItem(backup["time"]))
            self.backup_list.setItem(row_position, 2, QTableWidgetItem(backup["size"]))
            
        # 调整列宽
        self.backup_list.resizeColumnsToContents()
            
    def create_backup(self):
        """创建备份"""
        result = self.system_config.create_backup()
        if result["success"]:
            QMessageBox.information(self, "成功", result["message"])
            self.load_backups()
        else:
            QMessageBox.warning(self, "错误", result["message"])
            
    def restore_backup(self):
        """还原备份"""
        selected_rows = self.backup_list.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "警告", "请先选择一个备份")
            return
            
        selected_row = self.backup_list.row(selected_rows[0])
        backup_name = self.backup_list.item(selected_row, 0).text()
        
        # 获取备份路径
        backup_dir = self.system_config.get_config("backup", "backup_dir", "backups")
        backup_path = os.path.join(backup_dir, backup_name)
        
        # 确认还原
        if QMessageBox.question(
            self, 
            "确认还原", 
            f"确定要还原备份 {backup_name}？\n这将覆盖当前的配置和数据库文件。",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            result = self.system_config.restore_backup(backup_path)
            if result["success"]:
                QMessageBox.information(self, "成功", result["message"])
                # 刷新数据库状态
                self.check_db_status()
            else:
                QMessageBox.warning(self, "错误", result["message"])
                
    def showEvent(self, event):
        """显示事件处理"""
        super().showEvent(event)
        # 检查数据库状态
        self.check_db_status()
        # 启动定时器
        if not self.refresh_timer.isActive():
            self.refresh_timer.start(30000)
        
    def hideEvent(self, event):
        """隐藏事件处理"""
        super().hideEvent(event)
        # 停止定时器
        self.refresh_timer.stop()
        
    def set_default_paths(self):
        """设置默认路径"""
        # 使用配置文件中已有的路径，避免重复查找
        # 如果Cursor可执行文件路径为空，则设置默认路径
        if not self.cursor_exe_path.text():
            cursor_exe = self.system_config.get_config("cursor", "executable_path", "")
            if cursor_exe:
                self.cursor_exe_path.setText(cursor_exe)
                
        # 如果Cursor数据目录为空，则设置默认路径
        if not self.cursor_data_path.text():
            cursor_data = self.system_config.get_config("cursor", "data_dir", "")
            if cursor_data:
                self.cursor_data_path.setText(cursor_data)
                
        # 如果Cursor配置文件为空，则设置默认路径
        if not self.cursor_config_path.text():
            cursor_config = self.system_config.get_config("cursor", "config_file", "")
            if cursor_config:
                self.cursor_config_path.setText(cursor_config)
                
        # 如果Cursor数据库文件为空，则设置默认路径
        if not self.cursor_db_path.text():
            cursor_db = self.system_config.get_config("cursor", "db_file", "")
            if cursor_db:
                self.cursor_db_path.setText(cursor_db)
                
        # 如果Chrome可执行文件路径为空，则设置默认路径
        if not self.chrome_exe_path.text():
            chrome_exe = self.system_config.get_config("chrome", "executable_path", "")
            if chrome_exe:
                self.chrome_exe_path.setText(chrome_exe)
                
        # 如果Chrome用户数据目录为空，则设置默认路径
        if not self.chrome_data_path.text():
            chrome_data = self.system_config.get_config("chrome", "user_data_dir", "")
            if chrome_data:
                self.chrome_data_path.setText(chrome_data)
                
    def detect_paths(self):
        """自动检测所有路径"""
        try:
            # 显示进度对话框
            QMessageBox.information(self, "自动检测", "即将开始自动检测路径，这可能需要几秒钟...")
            
            # 调用系统配置管理器的重新检测方法
            if self.system_config.redetect_paths():
                QMessageBox.information(self, "成功", "自动检测路径完成")
                # 刷新UI显示
                self.load_config_data()
            else:
                QMessageBox.warning(self, "警告", "自动检测路径时出现错误")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"自动检测路径失败: {str(e)}")
            
    def view_machine_id(self):
        """查看机器ID文件内容"""
        machine_id_file = self.machine_id_path.text()
        if not machine_id_file or not os.path.exists(machine_id_file):
            QMessageBox.warning(self, "错误", "机器ID文件不存在")
            return
            
        try:
            with open(machine_id_file, "r", encoding="utf-8") as f:
                content = f.read()
                
            dialog = QDialog(self)
            dialog.setWindowTitle("Cursor机器ID")
            dialog.resize(500, 250)
            
            layout = QVBoxLayout(dialog)
            
            # 添加机器ID内容
            id_content_group = QGroupBox("机器ID内容")
            id_content_layout = QVBoxLayout()
            
            text_edit = QTextEdit()
            text_edit.setReadOnly(True)
            text_edit.setFont(QFont("Courier New", 11))
            text_edit.setText(content)
            id_content_layout.addWidget(text_edit)
            
            id_content_group.setLayout(id_content_layout)
            layout.addWidget(id_content_group)
            
            # 添加警告信息
            warning_label = QLabel("警告：此ID是Cursor识别您设备的唯一标识，修改可能导致授权失效！")
            warning_label.setStyleSheet("color: red; font-weight: bold; padding: 10px;")
            warning_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(warning_label)
            
            # 添加说明
            info_label = QLabel("机器ID用于防止账号被滥用。如需迁移授权到新设备，请联系Cursor支持团队。")
            info_label.setWordWrap(True)
            info_label.setStyleSheet("color: #666; padding: 5px;")
            layout.addWidget(info_label)
            
            # 添加按钮
            button_box = QDialogButtonBox(QDialogButtonBox.Close)
            button_box.rejected.connect(dialog.reject)
            layout.addWidget(button_box)
            
            dialog.exec_()
        except Exception as e:
            QMessageBox.warning(self, "错误", f"无法读取机器ID文件: {str(e)}") 