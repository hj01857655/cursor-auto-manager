import os
import sqlite3
import json
import logging
from datetime import datetime
from utils.logger import LoggerManager

class DbManager:
    """数据库管理器类，用于管理Cursor数据库"""
    
    # 单例模式
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(DbManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, db_path=None):
        """初始化数据库管理器
        
        Args:
            db_path: 数据库文件路径，如果为None则尝试自动查找
        """
        # 避免重复初始化
        if hasattr(self, '_initialized') and self._initialized:
            if db_path and db_path != self.db_path:
                self.set_db_path(db_path)
            return
            
        # 设置日志
        self.logger = LoggerManager()
        
        # 数据库路径
        self.db_path = None
        if db_path:
            self.set_db_path(db_path)
        
        # 初始化完成标记
        self._initialized = True
        
    def set_db_path(self, db_path):
        """设置数据库路径
        
        Args:
            db_path: 数据库文件路径
            
        Returns:
            bool: 是否设置成功
        """
        if not db_path or not os.path.exists(db_path):
            self.logger.error(f"数据库文件不存在: {db_path}", "DbManager")
            return False
            
        self.db_path = db_path
        self.logger.info(f"设置数据库路径: {db_path}", "DbManager")
        return True
        
    def get_db_info(self):
        """获取数据库信息
        
        Returns:
            dict: 数据库信息字典
        """
        if not self.db_path or not os.path.exists(self.db_path):
            return {
                "status": "错误",
                "message": "数据库文件不存在",
                "size": "0 KB",
                "tables": [],
                "valid": False
            }
            
        try:
            # 获取文件大小
            size_bytes = os.path.getsize(self.db_path)
            if size_bytes < 1024:
                size_str = f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                size_str = f"{size_bytes / 1024:.2f} KB"
            else:
                size_str = f"{size_bytes / (1024 * 1024):.2f} MB"
                
            # 连接数据库
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 获取表列表
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [table[0] for table in cursor.fetchall()]
            
            # 获取每个表的行数
            table_info = []
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM [{table}];")
                    count = cursor.fetchone()[0]
                    table_info.append(f"{table} ({count}行)")
                except sqlite3.OperationalError:
                    table_info.append(f"{table} (无法读取)")
                    
            conn.close()
            
            return {
                "status": "正常",
                "message": "数据库状态正常",
                "size": size_str,
                "tables": table_info,
                "valid": True
            }
            
        except Exception as e:
            self.logger.error(f"获取数据库信息失败: {e}", "DbManager")
            return {
                "status": "错误",
                "message": f"获取数据库信息失败: {str(e)}",
                "size": "未知",
                "tables": [],
                "valid": False
            }
            
    def get_table_data(self, table_name, limit=100, offset=0):
        """获取表数据
        
        Args:
            table_name: 表名
            limit: 限制返回的行数
            offset: 偏移量
            
        Returns:
            dict: 表数据信息
        """
        if not self.db_path or not os.path.exists(self.db_path):
            return {
                "status": "错误",
                "message": "数据库文件不存在",
                "columns": [],
                "data": [],
                "total": 0
            }
            
        try:
            # 连接数据库
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # 使用行工厂获取列名
            cursor = conn.cursor()
            
            # 获取表的总行数
            cursor.execute(f"SELECT COUNT(*) FROM [{table_name}];")
            total = cursor.fetchone()[0]
            
            # 获取表数据
            cursor.execute(f"SELECT * FROM [{table_name}] LIMIT {limit} OFFSET {offset};")
            rows = cursor.fetchall()
            
            if not rows:
                conn.close()
                return {
                    "status": "正常",
                    "message": "表中没有数据",
                    "columns": [],
                    "data": [],
                    "total": 0
                }
                
            # 获取列名
            columns = [column for column in rows[0].keys()]
            
            # 转换数据为列表
            data = []
            for row in rows:
                row_data = {}
                for column in columns:
                    value = row[column]
                    # 尝试解析JSON字符串
                    if isinstance(value, str) and (value.startswith('{') or value.startswith('[')):
                        try:
                            value = json.loads(value)
                        except:
                            pass
                    row_data[column] = value
                data.append(row_data)
                
            conn.close()
            
            return {
                "status": "正常",
                "message": f"成功获取表数据，共{total}行",
                "columns": columns,
                "data": data,
                "total": total
            }
            
        except Exception as e:
            self.logger.error(f"获取表数据失败: {e}", "DbManager")
            return {
                "status": "错误",
                "message": f"获取表数据失败: {str(e)}",
                "columns": [],
                "data": [],
                "total": 0
            }
            
    def get_key_value_pairs(self, table_name="ItemTable", key_column="key", value_column="value", limit=100, offset=0):
        """获取键值对数据，特别针对ItemTable表
        
        Args:
            table_name: 表名，默认为ItemTable
            key_column: 键列名，默认为key
            value_column: 值列名，默认为value
            limit: 限制返回的行数
            offset: 偏移量
            
        Returns:
            dict: 键值对数据信息
        """
        if not self.db_path or not os.path.exists(self.db_path):
            return {
                "status": "错误",
                "message": "数据库文件不存在",
                "data": {},
                "total": 0
            }
            
        try:
            # 连接数据库
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 获取表的总行数
            cursor.execute(f"SELECT COUNT(*) FROM [{table_name}];")
            total = cursor.fetchone()[0]
            
            # 获取键值对数据
            cursor.execute(f"SELECT [{key_column}], [{value_column}] FROM [{table_name}] LIMIT {limit} OFFSET {offset};")
            rows = cursor.fetchall()
            
            if not rows:
                conn.close()
                return {
                    "status": "正常",
                    "message": "表中没有数据",
                    "data": {},
                    "total": 0
                }
                
            # 转换数据为字典
            data = {}
            for row in rows:
                key = row[0]
                value = row[1]
                
                # 尝试解析JSON字符串
                if isinstance(value, str) and (value.startswith('{') or value.startswith('[')):
                    try:
                        value = json.loads(value)
                    except:
                        pass
                        
                data[key] = value
                
            conn.close()
            
            return {
                "status": "正常",
                "message": f"成功获取键值对数据，共{total}对",
                "data": data,
                "total": total
            }
            
        except Exception as e:
            self.logger.error(f"获取键值对数据失败: {e}", "DbManager")
            return {
                "status": "错误",
                "message": f"获取键值对数据失败: {str(e)}",
                "data": {},
                "total": 0
            }
            
    def search_keys(self, keyword, table_name="ItemTable", key_column="key", value_column="value", limit=100):
        """搜索键
        
        Args:
            keyword: 关键字
            table_name: 表名，默认为ItemTable
            key_column: 键列名，默认为key
            value_column: 值列名，默认为value
            limit: 限制返回的行数
            
        Returns:
            dict: 搜索结果
        """
        if not self.db_path or not os.path.exists(self.db_path):
            return {
                "status": "错误",
                "message": "数据库文件不存在",
                "data": {},
                "total": 0
            }
            
        try:
            # 连接数据库
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 搜索键
            cursor.execute(f"SELECT [{key_column}], [{value_column}] FROM [{table_name}] WHERE [{key_column}] LIKE ? LIMIT {limit};", (f"%{keyword}%",))
            rows = cursor.fetchall()
            
            if not rows:
                conn.close()
                return {
                    "status": "正常",
                    "message": "没有找到匹配的数据",
                    "data": {},
                    "total": 0
                }
                
            # 转换数据为字典
            data = {}
            for row in rows:
                key = row[0]
                value = row[1]
                
                # 尝试解析JSON字符串
                if isinstance(value, str) and (value.startswith('{') or value.startswith('[')):
                    try:
                        value = json.loads(value)
                    except:
                        pass
                        
                data[key] = value
                
            conn.close()
            
            return {
                "status": "正常",
                "message": f"成功找到{len(data)}条匹配数据",
                "data": data,
                "total": len(data)
            }
            
        except Exception as e:
            self.logger.error(f"搜索键失败: {e}", "DbManager")
            return {
                "status": "错误",
                "message": f"搜索键失败: {str(e)}",
                "data": {},
                "total": 0
            }
            
    def set_key_value(self, key, value, table_name="ItemTable", key_column="key", value_column="value"):
        """设置键值对
        
        Args:
            key: 键
            value: 值
            table_name: 表名，默认为ItemTable
            key_column: 键列名，默认为key
            value_column: 值列名，默认为value
            
        Returns:
            dict: 操作结果
        """
        if not self.db_path or not os.path.exists(self.db_path):
            return {
                "status": "错误",
                "message": "数据库文件不存在"
            }
            
        try:
            # 连接数据库
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 如果值是字典或列表，转换为JSON字符串
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)
                
            # 查询键是否存在
            cursor.execute(f"SELECT COUNT(*) FROM [{table_name}] WHERE [{key_column}] = ?;", (key,))
            exists = cursor.fetchone()[0] > 0
            
            if exists:
                # 更新现有键值对
                cursor.execute(f"UPDATE [{table_name}] SET [{value_column}] = ? WHERE [{key_column}] = ?;", (value, key))
                message = f"成功更新键 '{key}' 的值"
            else:
                # 插入新键值对
                cursor.execute(f"INSERT INTO [{table_name}] ([{key_column}], [{value_column}]) VALUES (?, ?);", (key, value))
                message = f"成功添加新键值对 '{key}'"
                
            conn.commit()
            conn.close()
            
            self.logger.info(message, "DbManager")
            return {
                "status": "正常",
                "message": message
            }
            
        except Exception as e:
            self.logger.error(f"设置键值对失败: {e}", "DbManager")
            return {
                "status": "错误",
                "message": f"设置键值对失败: {str(e)}"
            }
            
    def delete_key(self, key, table_name="ItemTable", key_column="key"):
        """删除键
        
        Args:
            key: 键
            table_name: 表名，默认为ItemTable
            key_column: 键列名，默认为key
            
        Returns:
            dict: 操作结果
        """
        if not self.db_path or not os.path.exists(self.db_path):
            return {
                "status": "错误",
                "message": "数据库文件不存在"
            }
            
        try:
            # 连接数据库
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 查询键是否存在
            cursor.execute(f"SELECT COUNT(*) FROM [{table_name}] WHERE [{key_column}] = ?;", (key,))
            exists = cursor.fetchone()[0] > 0
            
            if not exists:
                conn.close()
                return {
                    "status": "错误",
                    "message": f"键 '{key}' 不存在"
                }
                
            # 删除键
            cursor.execute(f"DELETE FROM [{table_name}] WHERE [{key_column}] = ?;", (key,))
            conn.commit()
            conn.close()
            
            self.logger.info(f"成功删除键 '{key}'", "DbManager")
            return {
                "status": "正常",
                "message": f"成功删除键 '{key}'"
            }
            
        except Exception as e:
            self.logger.error(f"删除键失败: {e}", "DbManager")
            return {
                "status": "错误",
                "message": f"删除键失败: {str(e)}"
            }
            
    def clear_table(self, table_name="ItemTable"):
        """清空表
        
        Args:
            table_name: 表名，默认为ItemTable
            
        Returns:
            dict: 操作结果
        """
        if not self.db_path or not os.path.exists(self.db_path):
            return {
                "status": "错误",
                "message": "数据库文件不存在"
            }
            
        try:
            # 连接数据库
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 清空表
            cursor.execute(f"DELETE FROM [{table_name}];")
            conn.commit()
            conn.close()
            
            self.logger.info(f"成功清空表 '{table_name}'", "DbManager")
            return {
                "status": "正常",
                "message": f"成功清空表 '{table_name}'"
            }
            
        except Exception as e:
            self.logger.error(f"清空表失败: {e}", "DbManager")
            return {
                "status": "错误",
                "message": f"清空表失败: {str(e)}"
            }
            
    def backup_database(self, backup_path=None):
        """备份数据库
        
        Args:
            backup_path: 备份文件路径，如果为None则使用默认路径
            
        Returns:
            dict: 操作结果
        """
        if not self.db_path or not os.path.exists(self.db_path):
            return {
                "status": "错误",
                "message": "数据库文件不存在"
            }
            
        try:
            # 如果没有指定备份路径，生成一个默认路径
            if not backup_path:
                backup_dir = os.path.join(os.path.dirname(self.db_path), "backups")
                os.makedirs(backup_dir, exist_ok=True)
                backup_path = os.path.join(backup_dir, f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
                
            # 复制数据库文件
            import shutil
            shutil.copy2(self.db_path, backup_path)
            
            self.logger.info(f"成功备份数据库到 '{backup_path}'", "DbManager")
            return {
                "status": "正常",
                "message": f"成功备份数据库到 '{backup_path}'",
                "backup_path": backup_path
            }
            
        except Exception as e:
            self.logger.error(f"备份数据库失败: {e}", "DbManager")
            return {
                "status": "错误",
                "message": f"备份数据库失败: {str(e)}"
            }
            
    def restore_database(self, backup_path):
        """从备份还原数据库
        
        Args:
            backup_path: 备份文件路径
            
        Returns:
            dict: 操作结果
        """
        if not backup_path or not os.path.exists(backup_path):
            return {
                "status": "错误",
                "message": "备份文件不存在"
            }
            
        if not self.db_path:
            return {
                "status": "错误",
                "message": "未设置数据库路径"
            }
            
        try:
            # 确保数据库文件关闭
            try:
                conn = sqlite3.connect(self.db_path)
                conn.close()
            except:
                pass
                
            # 复制备份文件到数据库文件
            import shutil
            shutil.copy2(backup_path, self.db_path)
            
            self.logger.info(f"成功从 '{backup_path}' 还原数据库", "DbManager")
            return {
                "status": "正常",
                "message": f"成功从 '{backup_path}' 还原数据库"
            }
            
        except Exception as e:
            self.logger.error(f"还原数据库失败: {e}", "DbManager")
            return {
                "status": "错误",
                "message": f"还原数据库失败: {str(e)}"
            }
            
    def export_to_json(self, export_path=None, table_name="ItemTable", key_column="key", value_column="value"):
        """导出表数据到JSON文件
        
        Args:
            export_path: 导出文件路径，如果为None则使用默认路径
            table_name: 表名，默认为ItemTable
            key_column: 键列名，默认为key
            value_column: 值列名，默认为value
            
        Returns:
            dict: 操作结果
        """
        if not self.db_path or not os.path.exists(self.db_path):
            return {
                "status": "错误",
                "message": "数据库文件不存在"
            }
            
        try:
            # 如果没有指定导出路径，生成一个默认路径
            if not export_path:
                export_dir = os.path.join(os.path.dirname(self.db_path), "exports")
                os.makedirs(export_dir, exist_ok=True)
                export_path = os.path.join(export_dir, f"{table_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
                
            # 获取键值对数据
            result = self.get_key_value_pairs(table_name, key_column, value_column, limit=100000)
            if result["status"] != "正常":
                return result
                
            # 导出到JSON文件
            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(result["data"], f, ensure_ascii=False, indent=4)
                
            self.logger.info(f"成功导出表 '{table_name}' 数据到 '{export_path}'", "DbManager")
            return {
                "status": "正常",
                "message": f"成功导出表 '{table_name}' 数据到 '{export_path}'",
                "export_path": export_path
            }
            
        except Exception as e:
            self.logger.error(f"导出到JSON失败: {e}", "DbManager")
            return {
                "status": "错误",
                "message": f"导出到JSON失败: {str(e)}"
            }
            
    def import_from_json(self, import_path, table_name="ItemTable", key_column="key", value_column="value"):
        """从JSON文件导入数据到表
        
        Args:
            import_path: 导入文件路径
            table_name: 表名，默认为ItemTable
            key_column: 键列名，默认为key
            value_column: 值列名，默认为value
            
        Returns:
            dict: 操作结果
        """
        if not import_path or not os.path.exists(import_path):
            return {
                "status": "错误",
                "message": "导入文件不存在"
            }
            
        if not self.db_path or not os.path.exists(self.db_path):
            return {
                "status": "错误",
                "message": "数据库文件不存在"
            }
            
        try:
            # 从JSON文件导入数据
            with open(import_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            if not isinstance(data, dict):
                return {
                    "status": "错误",
                    "message": "导入文件格式不正确，应为JSON对象"
                }
                
            # 连接数据库
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 导入数据
            for key, value in data.items():
                # 如果值是字典或列表，转换为JSON字符串
                if isinstance(value, (dict, list)):
                    value = json.dumps(value, ensure_ascii=False)
                    
                # 查询键是否存在
                cursor.execute(f"SELECT COUNT(*) FROM [{table_name}] WHERE [{key_column}] = ?;", (key,))
                exists = cursor.fetchone()[0] > 0
                
                if exists:
                    # 更新现有键值对
                    cursor.execute(f"UPDATE [{table_name}] SET [{value_column}] = ? WHERE [{key_column}] = ?;", (value, key))
                else:
                    # 插入新键值对
                    cursor.execute(f"INSERT INTO [{table_name}] ([{key_column}], [{value_column}]) VALUES (?, ?);", (key, value))
                    
            conn.commit()
            conn.close()
            
            self.logger.info(f"成功从 '{import_path}' 导入 {len(data)} 条数据到表 '{table_name}'", "DbManager")
            return {
                "status": "正常",
                "message": f"成功从 '{import_path}' 导入 {len(data)} 条数据到表 '{table_name}'"
            }
            
        except Exception as e:
            self.logger.error(f"从JSON导入失败: {e}", "DbManager")
            return {
                "status": "错误",
                "message": f"从JSON导入失败: {str(e)}"
            } 