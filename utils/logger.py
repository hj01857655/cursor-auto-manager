import logging
import os
import time
import queue
from logging.handlers import RotatingFileHandler
from datetime import datetime
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QColor

class LogMessage:
    """日志消息类，用于存储日志信息"""
    
    def __init__(self, level, message, time_str=None, source=None):
        """初始化日志消息
        
        Args:
            level: 日志级别
            message: 日志消息内容
            time_str: 日志时间字符串，如果为None则使用当前时间
            source: 日志来源
        """
        self.level = level
        self.message = message
        self.time_str = time_str or datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        self.source = source or "app"
        
    def __str__(self):
        """返回日志消息的字符串表示形式"""
        return f"[{self.time_str}] [{self.level}] [{self.source}] {self.message}"

class LoggerManager(QObject):
    """日志管理器类"""
    
    # 定义信号
    log_message = pyqtSignal(str)
    
    # 日志级别对应的颜色
    LEVEL_COLORS = {
        "DEBUG": QColor(23, 162, 184),      # 蓝色 #17a2b8
        "INFO": QColor(40, 167, 69),        # 绿色 #28a745
        "SUCCESS": QColor(40, 167, 69),     # 绿色 #28a745
        "WARNING": QColor(255, 193, 7),     # 黄色 #ffc107
        "ERROR": QColor(220, 53, 69),       # 红色 #dc3545
        "CRITICAL": QColor(220, 53, 69)     # 红色 #dc3545
    }
    
    def __init__(self):
        """初始化日志管理器"""
        super().__init__()
        
        # 创建日志目录
        self.log_dir = "logs"
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
            
        # 创建日志文件
        self.log_file = os.path.join(self.log_dir, f"app_{datetime.now().strftime('%Y%m%d')}.log")
        
        # 创建日志处理器
        self.handler = RotatingFileHandler(
            self.log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        
        # 设置日志格式
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
        self.handler.setFormatter(formatter)
        
        # 创建日志记录器
        self.logger = logging.getLogger("LoggerManager")
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(self.handler)
        
        # 创建日志队列
        self.log_queue = queue.Queue(maxsize=1000)
        
        # 添加一个自定义处理器来处理所有日志
        class QueueHandler(logging.Handler):
            def __init__(self, queue_manager):
                super().__init__()
                self.queue_manager = queue_manager
                
            def emit(self, record):
                try:
                    level = record.levelname
                    message = self.format(record)
                    source = record.name
                    self.queue_manager._add_to_queue(level, message, source)
                except Exception:
                    self.handleError(record)
                    
        # 创建并添加队列处理器
        queue_handler = QueueHandler(self)
        queue_handler.setFormatter(formatter)
        self.logger.addHandler(queue_handler)
        
        # 记录初始化日志
        self.info("日志管理器初始化完成")
        
    def get_handler(self):
        """获取日志处理器"""
        return self.handler
        
    def log(self, message, level=logging.INFO, source="app"):
        """记录日志
        
        Args:
            message: 日志消息
            level: 日志级别
            source: 日志来源
        """
        # 记录到文件
        self.logger.log(level, message)
        
        # 添加到队列
        self._add_to_queue(
            logging.getLevelName(level),
            message,
            source
        )
        
        # 发送信号
        self.log_message.emit(message)
        
    def info(self, message, source="app"):
        """记录信息日志"""
        self.log(message, logging.INFO, source)
        
    def warning(self, message, source="app"):
        """记录警告日志"""
        self.log(message, logging.WARNING, source)
        
    def error(self, message, source="app"):
        """记录错误日志"""
        self.log(message, logging.ERROR, source)
        
    def debug(self, message, source="app"):
        """记录调试日志"""
        self.log(message, logging.DEBUG, source)
        
    def _add_to_queue(self, level, message, source="app"):
        """将日志消息添加到队列
        
        Args:
            level: 日志级别
            message: 日志消息
            source: 日志来源
        """
        try:
            # 如果队列已满，移除最旧的消息
            if self.log_queue.full():
                try:
                    self.log_queue.get_nowait()
                except queue.Empty:
                    pass
                    
            # 创建日志消息对象
            log_message = LogMessage(
                level=level if isinstance(level, str) else logging.getLevelName(level),
                message=message,
                source=source
            )
            
            # 添加到队列
            self.log_queue.put(log_message)
        except Exception as e:
            print(f"Error adding log to queue: {e}")
            
    def get_recent_logs(self, max_count=100, level=None, source=None):
        """获取最近的日志
        
        Args:
            max_count: 最大返回数量
            level: 过滤的日志级别
            source: 过滤的日志来源
            
        Returns:
            list: 日志消息列表
        """
        logs = []
        try:
            # 复制队列内容
            with self.log_queue.mutex:
                items = list(self.log_queue.queue)
                
            # 应用过滤
            for item in items:
                if level and item.level != level:
                    continue
                if source and item.source != source:
                    continue
                logs.append(item)
                
            # 返回最新的日志
            return logs[-max_count:]
        except Exception as e:
            self.error(f"获取最近日志失败: {e}")
            return []
        
    def read_log_file(self, max_lines=1000, level=None, source=None):
        """从日志文件中读取日志
        
        Args:
            max_lines: 最大返回行数
            level: 过滤的日志级别
            source: 过滤的日志来源
            
        Returns:
            list: 日志消息列表
        """
        if not os.path.exists(self.log_file):
            return []
            
        logs = []
        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                
            # 解析日志行
            for line in lines[-max_lines:]:
                parts = line.split(" - ", 3)
                if len(parts) >= 4:
                    time_str = parts[0]
                    log_level = parts[2]
                    content = parts[3]
                    
                    # 尝试提取source
                    if "[" in content and "]" in content:
                        source_part = content.split("]", 1)[0] + "]"
                        if source_part.startswith("["):
                            source_value = source_part[1:-1]
                            message = content.split("]", 1)[1].strip()
                        else:
                            source_value = "app"
                            message = content
                    else:
                        source_value = "app"
                        message = content
                        
                    # 应用过滤
                    if (level is None or log_level == level) and (source is None or source_value == source):
                        log_message = LogMessage(log_level, message.strip(), time_str, source_value)
                        logs.append(log_message)
                        
            return logs
        except Exception as e:
            self.error(f"读取日志文件失败: {e}", "LoggerManager")
            return []
            
    def clear_memory_logs(self):
        """清空内存中的日志队列"""
        with self.log_queue.mutex:
            self.log_queue.queue.clear()
            
    def get_log_files(self):
        """获取所有日志文件
        
        Returns:
            list: 日志文件路径列表
        """
        if not os.path.exists(self.log_dir):
            return []
            
        log_files = []
        for file in os.listdir(self.log_dir):
            if file.endswith(".log"):
                log_files.append(os.path.join(self.log_dir, file))
                
        # 按修改时间排序，最新的在前
        log_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        return log_files
        
    def get_log_size(self):
        """获取当前日志文件大小
        
        Returns:
            str: 日志文件大小（格式化后的字符串）
        """
        if not os.path.exists(self.log_file):
            return "0 KB"
            
        size_bytes = os.path.getsize(self.log_file)
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.2f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.2f} MB" 