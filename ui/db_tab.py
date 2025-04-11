from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                        QLabel, QTableWidget, QTableWidgetItem, QGroupBox, 
                        QFormLayout, QFileDialog, QLineEdit, QMessageBox,
                        QTabWidget, QTextEdit, QCheckBox, QComboBox, QDialog,
                        QDialogButtonBox, QHeaderView, QFrame, QSplitter)
from PyQt5.QtCore import Qt, QSize, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QIcon
from core.db_manager import DbManager
import os
import json
from PyQt5.QtWidgets import QApplication

class DbTab(QWidget):
    """数据库管理选项卡"""
    
    # 数据更新信号
    data_updated = pyqtSignal()
    
    def __init__(self, parent=None):
        """初始化数据库管理选项卡
        
        Args:
            parent: 父窗口
        """
        super().__init__(parent)
        
        # 获取数据库管理器
        self.db_manager = DbManager()
        
        # 父窗口引用，用于访问主窗口中的其他组件
        self.parent_window = parent
        
        # 创建UI
        self.setup_ui()
        
        # 延迟加载数据库信息，给UI更多时间初始化
        QTimer.singleShot(500, self.load_db_info)
        
        # 创建定时器，定期刷新数据库状态
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.load_db_info)
        self.refresh_timer.start(30000)  # 每30秒更新一次
        
    def setup_ui(self):
        """设置UI"""
        self._show_only_item_table = True  # 标记只显示ItemTable表
        
        main_layout = QVBoxLayout(self)
        
        # 创建顶部信息栏
        info_layout = QHBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(10)
        
        # 数据库路径选择
        self.db_path_label = QLabel("数据库路径:")
        info_layout.addWidget(self.db_path_label)
        
        self.db_path_input = QLineEdit()
        self.db_path_input.setReadOnly(True)
        self.db_path_input.setMinimumHeight(32)  # 设置最小高度
        info_layout.addWidget(self.db_path_input)
        
        # 创建按钮容器并设置固定高度
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(10)
        
        self.browse_btn = QPushButton("浏览...")
        self.browse_btn.setMinimumHeight(32)  # 设置按钮最小高度
        button_layout.addWidget(self.browse_btn)
        
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.setMinimumHeight(32)  # 设置按钮最小高度
        button_layout.addWidget(self.refresh_btn)
        
        info_layout.addWidget(button_container)
        
        # 连接信号
        self.browse_btn.clicked.connect(self.browse_db_path)
        self.refresh_btn.clicked.connect(self.load_db_info)
        
        main_layout.addLayout(info_layout)
        
        # 创建状态信息栏
        status_group = QGroupBox("数据库状态")
        status_layout = QFormLayout()
        
        self.status_label = QLabel("未知")
        self.size_label = QLabel("未知")
        self.tables_label = QLabel("未知")
        
        status_layout.addRow("状态:", self.status_label)
        status_layout.addRow("大小:", self.size_label)
        status_layout.addRow("表数量:", self.tables_label)
        
        status_group.setLayout(status_layout)
        main_layout.addWidget(status_group)
        
        # 创建选项卡
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # 创建键值对选项卡
        self.key_value_tab = QWidget()
        key_value_layout = QVBoxLayout(self.key_value_tab)
        
        # 搜索框
        search_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入关键字搜索ItemTable中的键...")
        self.search_input.returnPressed.connect(self.search_keys)
        search_layout.addWidget(self.search_input)
        
        self.table_combo = QComboBox()
        self.table_combo.currentIndexChanged.connect(self.on_table_changed)
        search_layout.addWidget(self.table_combo)
        
        self.search_btn = QPushButton("搜索")
        self.search_btn.clicked.connect(self.search_keys)
        search_layout.addWidget(self.search_btn)
        
        key_value_layout.addLayout(search_layout)
        
        # 创建键值对表格
        self.key_value_table = QTableWidget(0, 2)
        self.key_value_table.setHorizontalHeaderLabels(["键", "值"])
        self.key_value_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.key_value_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.key_value_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.key_value_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.key_value_table.doubleClicked.connect(self.on_table_double_clicked)
        
        key_value_layout.addWidget(self.key_value_table)
        
        # 创建操作按钮栏
        buttons_layout = QHBoxLayout()
        
        self.refresh_data_btn = QPushButton("刷新数据")
        self.refresh_data_btn.clicked.connect(lambda: self.load_key_value_data())
        self.refresh_data_btn.setToolTip("刷新当前表的键值对数据")
        buttons_layout.addWidget(self.refresh_data_btn)
        
        self.add_btn = QPushButton("添加")
        self.add_btn.clicked.connect(self.add_key_value)
        buttons_layout.addWidget(self.add_btn)
        
        self.edit_btn = QPushButton("编辑")
        self.edit_btn.clicked.connect(self.edit_key_value)
        buttons_layout.addWidget(self.edit_btn)
        
        self.delete_btn = QPushButton("删除")
        self.delete_btn.clicked.connect(self.delete_key_value)
        buttons_layout.addWidget(self.delete_btn)
        
        self.export_btn = QPushButton("导出")
        self.export_btn.clicked.connect(self.export_data)
        buttons_layout.addWidget(self.export_btn)
        
        self.import_btn = QPushButton("导入")
        self.import_btn.clicked.connect(self.import_data)
        buttons_layout.addWidget(self.import_btn)
        
        key_value_layout.addLayout(buttons_layout)
        
        # 添加选项卡 - 将标签修改为专注于ItemTable
        self.tabs.addTab(self.key_value_tab, "ItemTable键值对管理")
        
    def browse_db_path(self):
        """浏览数据库文件路径"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "选择数据库文件", 
            "", 
            "数据库文件 (*.db *.sqlite *.vscdb);;所有文件 (*.*)"
        )
        
        if file_path:
            if self.db_manager.set_db_path(file_path):
                self.db_path_input.setText(file_path)
                self.load_db_info()
            else:
                QMessageBox.warning(self, "错误", "无法打开数据库文件")
                
    def load_db_info(self):
        """加载数据库信息"""
        # 尝试多种方法获取数据库路径
        db_path = self.db_path_input.text()
        
        # 如果输入框中没有路径，尝试从各种来源获取
        if not db_path:
            # 方法1: 从parent_window.system_config获取 (如果存在)
            if hasattr(self, 'parent_window') and hasattr(self.parent_window, 'system_config'):
                db_path = self.parent_window.system_config.get_config("cursor", "db_file", "")
            
            # 方法2: 从直接parent()获取 (如果是MainWindow)
            elif hasattr(self.parent(), "system_config"):
                db_path = self.parent().system_config.get_config("cursor", "db_file", "")
                
            # 方法3: 尝试直接从系统配置获取
            if not db_path:
                try:
                    from utils.system_config import SystemConfigManager
                    system_config = SystemConfigManager()
                    db_path = system_config.get_config("cursor", "db_file", "")
                except Exception as e:
                    print(f"获取系统配置失败: {e}")
        
        # 如果仍然没有找到有效的数据库路径
        if not db_path or not os.path.exists(db_path):
            self.status_label.setText("未找到数据库")
            self.status_label.setStyleSheet("color: #ffc107;")  # 黄色警告
            self.size_label.setText("0 KB")
            self.tables_label.setText("未找到")
            self.tables_label.setStyleSheet("color: #ffc107;")  # 黄色警告
            return
            
        # 设置数据库路径并更新UI
        if self.db_manager.set_db_path(db_path):
            self.db_path_input.setText(db_path)
        else:
            self.status_label.setText("数据库连接失败")
            self.status_label.setStyleSheet("color: #dc3545;")  # 红色错误
            return
            
        try:
            # 获取数据库信息
            info = self.db_manager.get_db_info()
            
            # 更新状态
            if info["status"] == "正常":
                self.status_label.setText("正常")
                self.status_label.setStyleSheet("color: #28a745;")  # 绿色正常
            elif "错误" in info["status"] or "失败" in info["status"]:
                self.status_label.setText(info["status"])
                self.status_label.setStyleSheet("color: #dc3545;")  # 红色错误
            else:
                self.status_label.setText(info["status"])
                self.status_label.setStyleSheet("color: #ffc107;")  # 黄色警告
                
            self.size_label.setText(info["size"])
            
            # 筛选出ItemTable表
            item_table_found = False
            for table in info["tables"]:
                table_name = table.split(" ")[0]
                if table_name == "ItemTable":
                    item_table_found = True
                    break
                    
            # 更新表格列表
            self.table_combo.clear()
            
            # 只添加ItemTable表或可选的默认表
            if item_table_found:
                self.tables_label.setText("已找到")
                self.tables_label.setStyleSheet("color: #28a745;")  # 绿色正常
                self.table_combo.addItem("ItemTable")
                
                # 直接开始加载ItemTable的数据
                self.load_key_value_data("ItemTable")
            else:
                self.tables_label.setText("未找到")
                self.tables_label.setStyleSheet("color: #ffc107;")  # 黄色警告
                
        except Exception as e:
            QMessageBox.warning(self, "错误", f"加载数据库信息失败: {str(e)}")
            print(f"加载数据库信息失败: {e}")
            
    def load_key_value_data(self, table_name=None):
        """加载键值对数据
        
        Args:
            table_name: 要加载的表名，如果为None则使用当前选中的表
        """
        # 获取当前选择的表或使用传入的表名
        if table_name is None:
            if self.table_combo.count() == 0:
                return
            
            table_name = self.table_combo.currentText()
            
        if not table_name:
            return
            
        try:
            # 显示加载状态
            self.search_input.setPlaceholderText("正在加载数据...")
            QApplication.processEvents()  # 强制更新UI
            
            # 清空表格
            self.key_value_table.setRowCount(0)
            
            # 获取键值对数据
            result = self.db_manager.get_key_value_pairs(table_name)
            if result["status"] != "正常":
                print(f"加载键值对失败: {result['message']}")
                self.search_input.setPlaceholderText(f"加载失败: {result['message']}")
                return
                
            # 填充表格
            for key, value in result["data"].items():
                row = self.key_value_table.rowCount()
                self.key_value_table.insertRow(row)
                
                # 添加键
                key_item = QTableWidgetItem(key)
                self.key_value_table.setItem(row, 0, key_item)
                
                # 添加值（可能是复杂对象，转换为字符串）
                if isinstance(value, (dict, list)):
                    try:
                        value_str = json.dumps(value, ensure_ascii=False)
                    except:
                        value_str = str(value)
                else:
                    value_str = str(value)
                    
                value_item = QTableWidgetItem(value_str)
                self.key_value_table.setItem(row, 1, value_item)
            
            # 调整列宽
            self.key_value_table.resizeColumnsToContents()
            
            # 更新搜索框提示
            self.search_input.setPlaceholderText(f"输入关键字搜索{table_name}中的键... (共{self.key_value_table.rowCount()}条记录)")
            
        except Exception as e:
            print(f"加载键值对数据失败: {e}")
            self.search_input.setPlaceholderText(f"加载失败: {str(e)}")
            # 静默失败，不显示错误消息框，避免反复弹出
            
    def search_keys(self):
        """搜索键"""
        # 获取搜索关键字
        keyword = self.search_input.text().strip()
        if not keyword:
            self.load_key_value_data()
            return
            
        # 获取当前选择的表
        table_name = self.table_combo.currentText()
        if not table_name:
            return
            
        try:
            # 清空表格
            self.key_value_table.setRowCount(0)
            
            # 搜索键
            result = self.db_manager.search_keys(keyword, table_name)
            if result["status"] != "正常":
                QMessageBox.warning(self, "错误", result["message"])
                return
                
            # 填充表格
            for key, value in result["data"].items():
                row = self.key_value_table.rowCount()
                self.key_value_table.insertRow(row)
                
                # 添加键
                key_item = QTableWidgetItem(key)
                self.key_value_table.setItem(row, 0, key_item)
                
                # 添加值（可能是复杂对象，转换为字符串）
                if isinstance(value, (dict, list)):
                    value_str = json.dumps(value, ensure_ascii=False)
                else:
                    value_str = str(value)
                    
                value_item = QTableWidgetItem(value_str)
                self.key_value_table.setItem(row, 1, value_item)
            
            # 调整列宽
            self.key_value_table.resizeColumnsToContents()
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"搜索键失败: {str(e)}")
            
    def on_table_changed(self):
        """表格选择改变事件"""
        self.load_key_value_data()
        
    def add_key_value(self):
        """添加键值对"""
        # 获取当前选择的表
        table_name = self.table_combo.currentText()
        if not table_name:
            QMessageBox.warning(self, "错误", "请先选择一个表")
            return
            
        # 弹出编辑对话框
        dialog = KeyValueDialog(self, "添加键值对")
        if dialog.exec_() == QDialog.Accepted:
            key = dialog.key_input.text().strip()
            value_text = dialog.value_input.toPlainText().strip()
            
            if not key:
                QMessageBox.warning(self, "错误", "键不能为空")
                return
                
            # 尝试解析JSON
            if value_text.startswith('{') or value_text.startswith('['):
                try:
                    value = json.loads(value_text)
                except:
                    value = value_text
            else:
                value = value_text
                
            # 添加键值对
            result = self.db_manager.set_key_value(key, value, table_name)
            if result["status"] == "正常":
                QMessageBox.information(self, "成功", result["message"])
                self.load_key_value_data()
            else:
                QMessageBox.warning(self, "错误", result["message"])
                
    def edit_key_value(self):
        """编辑键值对"""
        # 获取当前选择的行
        selected_items = self.key_value_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "错误", "请先选择一项")
            return
            
        # 获取当前选择的表
        table_name = self.table_combo.currentText()
        if not table_name:
            return
            
        # 获取键和值
        row = selected_items[0].row()
        key = self.key_value_table.item(row, 0).text()
        value_text = self.key_value_table.item(row, 1).text()
        
        # 弹出编辑对话框
        dialog = KeyValueDialog(self, "编辑键值对", key, value_text)
        if dialog.exec_() == QDialog.Accepted:
            new_key = dialog.key_input.text().strip()
            new_value_text = dialog.value_input.toPlainText().strip()
            
            if not new_key:
                QMessageBox.warning(self, "错误", "键不能为空")
                return
                
            # 如果键改变了，先删除旧键
            if new_key != key:
                self.db_manager.delete_key(key, table_name)
                
            # 尝试解析JSON
            if new_value_text.startswith('{') or new_value_text.startswith('['):
                try:
                    new_value = json.loads(new_value_text)
                except:
                    new_value = new_value_text
            else:
                new_value = new_value_text
                
            # 更新键值对
            result = self.db_manager.set_key_value(new_key, new_value, table_name)
            if result["status"] == "正常":
                QMessageBox.information(self, "成功", result["message"])
                self.load_key_value_data()
            else:
                QMessageBox.warning(self, "错误", result["message"])
                
    def delete_key_value(self):
        """删除键值对"""
        # 获取当前选择的行
        selected_items = self.key_value_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "错误", "请先选择一项")
            return
            
        # 获取当前选择的表
        table_name = self.table_combo.currentText()
        if not table_name:
            return
            
        # 获取键
        row = selected_items[0].row()
        key = self.key_value_table.item(row, 0).text()
        
        # 确认删除
        reply = QMessageBox.question(
            self, 
            "确认删除", 
            f"确定要删除键 '{key}' 吗？", 
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 删除键
            result = self.db_manager.delete_key(key, table_name)
            if result["status"] == "正常":
                QMessageBox.information(self, "成功", result["message"])
                self.load_key_value_data()
            else:
                QMessageBox.warning(self, "错误", result["message"])
                
    def on_table_double_clicked(self, index):
        """表格双击事件"""
        if index.isValid():
            self.edit_key_value()
            
    def export_data(self):
        """导出数据"""
        # 获取当前选择的表
        table_name = self.table_combo.currentText()
        if not table_name:
            QMessageBox.warning(self, "错误", "请先选择一个表")
            return
            
        # 选择导出路径
        export_path, _ = QFileDialog.getSaveFileName(
            self, 
            "导出数据", 
            f"{table_name}.json", 
            "JSON文件 (*.json)"
        )
        
        if export_path:
            # 导出数据
            result = self.db_manager.export_to_json(export_path, table_name)
            if result["status"] == "正常":
                QMessageBox.information(self, "成功", result["message"])
            else:
                QMessageBox.warning(self, "错误", result["message"])
                
    def import_data(self):
        """导入数据"""
        # 获取当前选择的表
        table_name = self.table_combo.currentText()
        if not table_name:
            QMessageBox.warning(self, "错误", "请先选择一个表")
            return
            
        # 选择导入文件
        import_path, _ = QFileDialog.getOpenFileName(
            self, 
            "导入数据", 
            "", 
            "JSON文件 (*.json)"
        )
        
        if import_path:
            # 确认导入
            reply = QMessageBox.question(
                self, 
                "确认导入", 
                "导入将合并数据，可能覆盖现有数据。是否继续？", 
                QMessageBox.Yes | QMessageBox.No, 
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # 导入数据
                result = self.db_manager.import_from_json(import_path, table_name)
                if result["status"] == "正常":
                    QMessageBox.information(self, "成功", result["message"])
                    self.load_key_value_data()
                else:
                    QMessageBox.warning(self, "错误", result["message"])
                    
    def showEvent(self, event):
        """显示事件"""
        super().showEvent(event)
        # 加载数据库信息
        self.load_db_info()
        # 启动定时器
        if not self.refresh_timer.isActive():
            self.refresh_timer.start(30000)
        
    def hideEvent(self, event):
        """隐藏事件"""
        super().hideEvent(event)
        # 停止定时器
        self.refresh_timer.stop()


class KeyValueDialog(QDialog):
    """键值对编辑对话框"""
    
    def __init__(self, parent=None, title="编辑键值对", key="", value=""):
        """初始化对话框
        
        Args:
            parent: 父窗口
            title: 对话框标题
            key: 初始键
            value: 初始值
        """
        super().__init__(parent)
        
        self.setWindowTitle(title)
        self.resize(500, 300)
        
        layout = QVBoxLayout(self)
        
        # 键输入
        key_layout = QHBoxLayout()
        key_layout.addWidget(QLabel("键:"))
        
        self.key_input = QLineEdit(key)
        key_layout.addWidget(self.key_input)
        
        layout.addLayout(key_layout)
        
        # 值输入
        layout.addWidget(QLabel("值:"))
        
        self.value_input = QTextEdit()
        self.value_input.setText(value)
        self.value_input.setFont(QFont("Courier New", 10))
        layout.addWidget(self.value_input)
        
        # 格式化JSON按钮
        format_btn = QPushButton("格式化JSON")
        format_btn.clicked.connect(self.format_json)
        layout.addWidget(format_btn)
        
        # 按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, 
            Qt.Horizontal, 
            self
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
    def format_json(self):
        """格式化JSON"""
        try:
            # 获取当前文本
            text = self.value_input.toPlainText().strip()
            
            # 如果是JSON格式，进行格式化
            if text.startswith('{') or text.startswith('['):
                data = json.loads(text)
                formatted_text = json.dumps(data, indent=4, ensure_ascii=False)
                self.value_input.setText(formatted_text)
            else:
                QMessageBox.warning(self, "错误", "不是有效的JSON格式")
                
        except Exception as e:
            QMessageBox.warning(self, "错误", f"格式化JSON失败: {str(e)}") 