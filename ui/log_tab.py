from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                        QLabel, QTableWidget, QTableWidgetItem, QGroupBox, 
                        QFormLayout, QLineEdit, QComboBox, QCheckBox, 
                        QTextEdit, QFileDialog, QMessageBox, QSpinBox,
                        QSplitter, QTabWidget)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QTextCursor
from utils.logger import LoggerManager
import os

class LogTab(QWidget):
    """日志查看选项卡"""
    
    # 日志级别对应的颜色
    LEVEL_COLORS = {
        "DEBUG": QColor(128, 191, 255),     # 浅蓝色
        "INFO": QColor(98, 203, 98),        # 绿色
        "SUCCESS": QColor(0, 255, 127),     # 亮绿色
        "WARNING": QColor(255, 191, 0),     # 金黄色
        "ERROR": QColor(255, 69, 69),       # 红色
        "CRITICAL": QColor(255, 0, 0)       # 鲜红色
    }
    
    def __init__(self, logger_manager=None, parent=None):
        """初始化日志选项卡
        
        Args:
            logger_manager: 日志管理器实例
            parent: 父窗口
        """
        super().__init__(parent)
        
        # 获取日志管理器实例
        self.logger_manager = logger_manager or LoggerManager()
        
        # 创建UI
        self.setup_ui()
        
        # 创建定时器，实时刷新日志
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_log_display)
        self.refresh_timer.start(1000)  # 每秒刷新一次
        
        # 初始加载日志
        self.refresh_log_display()
        
    def setup_ui(self):
        """设置UI界面"""
        layout = QVBoxLayout(self)
        
        # 创建过滤控制面板
        filter_group = QGroupBox("日志过滤")
        filter_layout = QHBoxLayout()
        
        # 日志级别过滤
        level_layout = QFormLayout()
        self.level_combo = QComboBox()
        self.level_combo.addItem("全部", None)
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            self.level_combo.addItem(level, level)
        self.level_combo.currentIndexChanged.connect(self.apply_filter)
        level_layout.addRow("日志级别:", self.level_combo)
        filter_layout.addLayout(level_layout)
        
        # 日志来源过滤
        source_layout = QFormLayout()
        self.source_edit = QLineEdit()
        self.source_edit.setPlaceholderText("输入日志来源过滤")
        self.source_edit.textChanged.connect(self.apply_filter)
        source_layout.addRow("日志来源:", self.source_edit)
        filter_layout.addLayout(source_layout)
        
        # 关键字过滤
        keyword_layout = QFormLayout()
        self.keyword_edit = QLineEdit()
        self.keyword_edit.setPlaceholderText("输入关键字过滤")
        self.keyword_edit.textChanged.connect(self.apply_filter)
        keyword_layout.addRow("关键字:", self.keyword_edit)
        filter_layout.addLayout(keyword_layout)
        
        # 每页行数
        lines_layout = QFormLayout()
        self.max_lines_spin = QSpinBox()
        self.max_lines_spin.setRange(10, 10000)
        self.max_lines_spin.setValue(500)
        self.max_lines_spin.setSingleStep(100)
        self.max_lines_spin.valueChanged.connect(self.apply_filter)
        lines_layout.addRow("显示行数:", self.max_lines_spin)
        filter_layout.addLayout(lines_layout)
        
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)
        
        # 创建日志内容显示区域
        self.log_tabs = QTabWidget()
        
        # 创建实时日志选项卡
        self.realtime_tab = QWidget()
        realtime_layout = QVBoxLayout(self.realtime_tab)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setLineWrapMode(QTextEdit.NoWrap)
        realtime_layout.addWidget(self.log_text)
        
        # 创建按钮行
        realtime_buttons = QHBoxLayout()
        
        self.clear_btn = QPushButton("清空显示")
        self.clear_btn.clicked.connect(self.clear_display)
        realtime_buttons.addWidget(self.clear_btn)
        
        self.auto_scroll_check = QCheckBox("自动滚动")
        self.auto_scroll_check.setChecked(True)
        realtime_buttons.addWidget(self.auto_scroll_check)
        
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.clicked.connect(self.refresh_log_display)
        realtime_buttons.addWidget(self.refresh_btn)
        
        realtime_buttons.addStretch()
        
        realtime_layout.addLayout(realtime_buttons)
        
        # 创建文件日志选项卡
        self.file_tab = QWidget()
        file_layout = QVBoxLayout(self.file_tab)
        
        self.file_log_text = QTextEdit()
        self.file_log_text.setReadOnly(True)
        self.file_log_text.setLineWrapMode(QTextEdit.NoWrap)
        file_layout.addWidget(self.file_log_text)
        
        # 创建文件日志按钮行
        file_buttons = QHBoxLayout()
        
        self.load_file_btn = QPushButton("加载日志文件")
        self.load_file_btn.clicked.connect(self.load_log_file)
        file_buttons.addWidget(self.load_file_btn)
        
        self.file_info_label = QLabel("当前日志文件: 无")
        file_buttons.addWidget(self.file_info_label)
        
        file_buttons.addStretch()
        
        self.open_log_dir_btn = QPushButton("打开日志目录")
        self.open_log_dir_btn.clicked.connect(self.open_log_directory)
        file_buttons.addWidget(self.open_log_dir_btn)
        
        file_layout.addLayout(file_buttons)
        
        # 添加选项卡
        self.log_tabs.addTab(self.realtime_tab, "实时日志")
        self.log_tabs.addTab(self.file_tab, "文件日志")
        
        layout.addWidget(self.log_tabs)
        
        # 日志统计信息
        self.status_label = QLabel("日志统计: 0条日志")
        layout.addWidget(self.status_label)
        
        # 设置样式
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
            
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 4px;
                background: white;
                selection-background-color: #4a90e2;
                font-family: 'Consolas', 'Courier New', monospace;
                padding: 5px;
            }
            
            QTextEdit:focus {
                border-color: #4a90e2;
            }
            
            QComboBox {
                padding: 5px;
                border: 1px solid #ddd;
                border-radius: 4px;
                min-width: 100px;
            }
            
            QComboBox:hover {
                border-color: #357abd;
            }
            
            QComboBox:focus {
                border-color: #4a90e2;
            }
            
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            
            QComboBox::down-arrow {
                image: url(resources/icons/down-arrow.png);
                width: 12px;
                height: 12px;
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
            
            QCheckBox {
                spacing: 8px;
            }
            
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #ddd;
                border-radius: 3px;
            }
            
            QCheckBox::indicator:checked {
                background-color: #4a90e2;
                border-color: #4a90e2;
            }
            
            QCheckBox::indicator:hover {
                border-color: #4a90e2;
            }
            
            QSpinBox {
                padding: 5px;
                border: 1px solid #ddd;
                border-radius: 4px;
                min-width: 80px;
            }
            
            QSpinBox:hover {
                border-color: #357abd;
            }
            
            QSpinBox:focus {
                border-color: #4a90e2;
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
            }
            
            QTabBar::tab:hover {
                background: #e9ecef;
            }
        """)
        
        # 设置过滤组样式
        filter_group.setStyleSheet("""
            QGroupBox {
                background: #f8f9fa;
            }
        """)
        
        # 设置状态标签样式
        self.status_label.setStyleSheet("""
            QLabel {
                color: #666;
                padding: 5px;
                background: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 4px;
            }
        """)
        
        # 设置日志文本框样式
        log_text_style = """
            QTextEdit {
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
                line-height: 1.5;
                background-color: #1e1e1e;
                color: #e0e0e0;
                selection-background-color: #264f78;
                border: 1px solid #333333;
                border-radius: 4px;
                padding: 5px;
            }
        """
        self.log_text.setStyleSheet(log_text_style)
        self.file_log_text.setStyleSheet(log_text_style)
        
    def refresh_log_display(self):
        """刷新日志显示"""
        # 获取过滤条件
        level_idx = self.level_combo.currentIndex()
        level_filter = self.level_combo.itemData(level_idx)
        
        source_filter = self.source_edit.text().strip()
        source_filter = source_filter if source_filter else None
        
        keyword_filter = self.keyword_edit.text().strip()
        
        max_lines = self.max_lines_spin.value()
        
        # 获取日志
        logs = self.logger_manager.get_recent_logs(max_count=max_lines, level=level_filter, source=source_filter)
        
        # 应用关键字过滤
        if keyword_filter:
            logs = [log for log in logs if keyword_filter.lower() in str(log).lower()]
            
        # 清空文本显示
        self.log_text.clear()
            
        # 定义显示格式
        for log in logs:
            # 设置颜色
            if hasattr(log, 'level'):
                # 检查是否包含"成功"或"完成"等关键词
                if log.level == "INFO" and any(keyword in log.message.lower() for keyword in ["成功", "完成", "已创建", "已更新"]):
                    self.log_text.setTextColor(self.LEVEL_COLORS["SUCCESS"])
                elif log.level in self.LEVEL_COLORS:
                    self.log_text.setTextColor(self.LEVEL_COLORS[log.level])
                else:
                    self.log_text.setTextColor(QColor(220, 220, 220))  # 默认浅灰色
            else:
                self.log_text.setTextColor(QColor(220, 220, 220))  # 默认浅灰色
                
            self.log_text.append(str(log))
            
        # 更新状态标签
        self.status_label.setText(f"日志统计: {len(logs)}条日志")
        
        # 如果启用了自动滚动，则滚动到底部
        if self.auto_scroll_check.isChecked():
            self.log_text.moveCursor(QTextCursor.End)
        
    def load_log_file(self):
        """加载日志文件"""
        log_files = self.logger_manager.get_log_files()
        if not log_files:
            QMessageBox.information(self, "提示", "没有找到日志文件")
            return
            
        # 默认加载最新的日志文件
        current_file = log_files[0]
        self.load_file_content(current_file)
        
    def load_file_content(self, file_path):
        """加载文件内容
        
        Args:
            file_path: 文件路径
        """
        try:
            # 获取过滤条件
            level_idx = self.level_combo.currentIndex()
            level_filter = self.level_combo.itemData(level_idx)
            
            source_filter = self.source_edit.text().strip()
            source_filter = source_filter if source_filter else None
            
            keyword_filter = self.keyword_edit.text().strip()
            
            max_lines = self.max_lines_spin.value()
            
            # 清空文本显示
            self.file_log_text.clear()
            
            # 读取文件
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()[-max_lines:]
                
                for line in lines:
                    # 应用关键字过滤
                    if keyword_filter and keyword_filter.lower() not in line.lower():
                        continue
                        
                    # 设置颜色
                    color = QColor(220, 220, 220)  # 默认浅灰色
                    for level, level_color in self.LEVEL_COLORS.items():
                        if f" {level} " in line:
                            color = level_color
                            # 检查是否包含"成功"或"完成"等关键词
                            if level == "INFO" and any(keyword in line.lower() for keyword in ["成功", "完成", "已创建", "已更新"]):
                                color = self.LEVEL_COLORS["SUCCESS"]
                            break
                            
                    # 应用过滤
                    if level_filter and f" {level_filter} " not in line:
                        continue
                    if source_filter and f"[{source_filter}]" not in line:
                        continue
                        
                    # 添加日志行
                    self.file_log_text.setTextColor(color)
                    self.file_log_text.append(line.strip())
                    
            # 更新文件信息
            file_size = os.path.getsize(file_path)
            if file_size < 1024:
                size_str = f"{file_size} B"
            elif file_size < 1024 * 1024:
                size_str = f"{file_size / 1024:.2f} KB"
            else:
                size_str = f"{file_size / (1024 * 1024):.2f} MB"
                
            self.file_info_label.setText(f"当前日志文件: {os.path.basename(file_path)} ({size_str})")
            
            # 自动滚动到底部
            cursor = self.file_log_text.textCursor()
            cursor.movePosition(QTextCursor.End)
            self.file_log_text.setTextCursor(cursor)
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"加载日志文件失败: {str(e)}")
            
    def apply_filter(self):
        """应用过滤条件"""
        # 刷新显示
        self.refresh_log_display()
        
        # 如果在文件日志选项卡，重新加载当前文件
        if self.log_tabs.currentIndex() == 1:
            self.load_log_file()
            
    def clear_display(self):
        """清空显示内容"""
        self.log_text.clear()
        
    def open_log_directory(self):
        """打开日志目录"""
        log_dir = self.logger_manager.log_dir
        
        if not os.path.exists(log_dir):
            QMessageBox.information(self, "提示", "日志目录不存在")
            return
            
        import subprocess
        import platform
        
        try:
            if platform.system() == "Windows":
                os.startfile(log_dir)
            elif platform.system() == "Darwin":  # macOS
                subprocess.call(["open", log_dir])
            else:  # Linux
                subprocess.call(["xdg-open", log_dir])
        except Exception as e:
            QMessageBox.warning(self, "错误", f"打开日志目录失败: {str(e)}")
            
    def showEvent(self, event):
        """显示事件"""
        super().showEvent(event)
        # 刷新显示
        self.refresh_log_display()
        # 重新启动定时器
        if not self.refresh_timer.isActive():
            self.refresh_timer.start(1000)
        
    def hideEvent(self, event):
        """隐藏事件"""
        super().hideEvent(event)
        # 暂停定时器
        self.refresh_timer.stop()
        
    def closeEvent(self, event):
        """关闭事件"""
        self.refresh_timer.stop()
        super().closeEvent(event) 