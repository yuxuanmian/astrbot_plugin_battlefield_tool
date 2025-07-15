from typing import Tuple, Optional, Union, Dict, List
from astrbot.api.star import StarTools
from astrbot.api import logger

import sqlite3
import os


class BattleFieldDataBase:
    bf_db_name = "battle_filed_tool.db"

    def __init__(self, bf_db_path: str = None):
        super().__init__()
        if bf_db_path is None:
            self.bf_db_path = os.path.join(StarTools.get_data_dir("battleFiled_tool_plugin"), self.bf_db_name)
        else:
            self.bf_db_path = os.path.join(bf_db_path, self.bf_db_name)
        self._init_db()

    def _init_db(self):
        """初始化数据库连接"""
        sql_path = os.path.join(os.path.dirname(__file__), "sql", "battleFiled_tool_plugin_init.sql")  # 更安全的路径拼接
        with open(sql_path, encoding="utf-8") as f, \
                self._get_conn() as conn:
            try:
                conn.executescript(f.read())
            except sqlite3.Error as e:
                conn.rollback()
                raise RuntimeError(f"初始化数据库失败: {e}")

    def _get_conn(self) -> sqlite3.Connection:
        """初始化数据库"""
        conn = sqlite3.connect(self.bf_db_path)
        conn.text_factory = str
        return conn

    def exec_sql(self, sql: str, params: Tuple = None):
        """
        执行SQL

        Args:
            sql: 要执行的SQL查询语句
            params: 查询参数，可以是元组或字典
        """
        with self._get_conn() as conn:  # 使用上下文管理器自动关闭
            cursor = conn.cursor()
            cursor.execute(sql, params or ())
            conn.commit()

    def query(self, sql: str, params: Optional[Union[Tuple, Dict]] = None, fetch_all: bool = True) -> Union[
        List[Dict], Optional[Dict]]:
        """
        执行SQL查询并返回结果

        Args:
            sql: 要执行的SQL查询语句
            params: 查询参数，可以是元组或字典
            fetch_all: 是否获取所有结果（False时只返回第一条）

        Returns:
            当 fetch_all=True 时返回 List[Dict]
            当 fetch_all=False 时返回单个 Dict 或 None（无结果时）

        Raises:
            sqlite3.Error: 数据库操作失败时抛出
        """
        try:
            with self._get_conn() as conn:
                conn.row_factory = sqlite3.Row  # 使结果可转为字典
                cursor = conn.cursor()

                # 根据参数类型选择执行方式
                if isinstance(params, dict):
                    cursor.execute(sql, params)
                else:
                    cursor.execute(sql, params or ())

                if fetch_all:
                    return [dict(row) for row in cursor.fetchall()]
                else:
                    if result := cursor.fetchone():
                        return dict(result)
                    return None

        except sqlite3.Error as e:
            logger.error(f"查询失败: {e}\nSQL: {sql}\nParams: {params}")
            raise
