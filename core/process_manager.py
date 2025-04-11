import os
import subprocess
import psutil
import time
import sys
import logging
import platform
from pathlib import Path
from PyQt5.QtCore import QObject
from utils.logger import LoggerManager

class CursorProcessManager(QObject):
    """Cursor进程管理器类，用于检测和控制Cursor进程"""
    
    def __init__(self):
        """初始化Cursor进程管理器"""
        super().__init__()
        self.logger = LoggerManager()
        self.logger.info("Cursor进程管理器初始化完成", "CursorProcessManager")
        
    def get_cursor_status(self):
        """获取Cursor进程状态
        
        Returns:
            dict: 包含进程状态信息的字典
        """
        try:
            # 查找Cursor进程
            cursor_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'exe']):
                try:
                    if 'cursor' in proc.info['name'].lower():
                        cursor_processes.append(proc)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
            # 获取可执行文件路径
            executable = self._find_cursor_executable()
            if executable:
                self.logger.info(f"找到Cursor可执行文件: {executable}", "CursorProcessManager")
            else:
                self.logger.warning("未找到Cursor可执行文件", "CursorProcessManager")
                
            return {
                "running": len(cursor_processes) > 0,
                "process_count": len(cursor_processes),
                "executable": executable,
                "executable_exists": os.path.exists(executable) if executable else False
            }
        except Exception as e:
            self.logger.error(f"获取Cursor状态失败: {e}", "CursorProcessManager")
            return {
                "running": False,
                "process_count": 0,
                "executable": None,
                "executable_exists": False
            }
            
    def _find_cursor_executable(self):
        """查找Cursor可执行文件路径
        
        Returns:
            str: 可执行文件路径，如果未找到则返回None
        """
        try:
            if platform.system() == "Windows":
                # Windows下的默认安装路径
                default_paths = [
                    os.path.expandvars(r"%LOCALAPPDATA%\Programs\Cursor\Cursor.exe"),
                    os.path.expandvars(r"%APPDATA%\Cursor\Cursor.exe")
                ]
            else:
                # Linux/Mac下的默认安装路径
                default_paths = [
                    os.path.expanduser("~/.local/share/cursor/cursor"),
                    "/usr/bin/cursor",
                    "/usr/local/bin/cursor"
                ]
                
            for path in default_paths:
                if os.path.exists(path):
                    return path
                    
            return None
        except Exception as e:
            self.logger.error(f"查找Cursor可执行文件失败: {e}", "CursorProcessManager")
            return None
            
    def start_cursor(self, workspace_path=None):
        """启动Cursor
        
        Args:
            workspace_path: 工作区路径，可选
            
        Returns:
            bool: 是否成功启动
        """
        try:
            executable = self._find_cursor_executable()
            if not executable:
                self.logger.error("未找到Cursor可执行文件", "CursorProcessManager")
                return False
                
            if workspace_path:
                os.startfile(executable, workspace_path)
            else:
                os.startfile(executable)
                
            self.logger.info("Cursor已启动", "CursorProcessManager")
            return True
        except Exception as e:
            self.logger.error(f"启动Cursor失败: {e}", "CursorProcessManager")
            return False
            
    def kill_cursor(self):
        """关闭所有Cursor进程
        
        Returns:
            bool: 是否成功关闭
        """
        try:
            killed = False
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if 'cursor' in proc.info['name'].lower():
                        proc.kill()
                        killed = True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
            if killed:
                self.logger.info("所有Cursor进程已关闭", "CursorProcessManager")
            else:
                self.logger.warning("未找到运行的Cursor进程", "CursorProcessManager")
                
            return killed
        except Exception as e:
            self.logger.error(f"关闭Cursor进程失败: {e}", "CursorProcessManager")
            return False
            
    def restart_cursor(self, workspace_path=None):
        """重启Cursor
        
        Args:
            workspace_path: 工作区路径，可选
            
        Returns:
            bool: 是否成功重启
        """
        try:
            if self.kill_cursor():
                # 等待进程完全关闭
                time.sleep(2)
                
            return self.start_cursor(workspace_path)
        except Exception as e:
            self.logger.error(f"重启Cursor失败: {e}", "CursorProcessManager")
            return False
            
 