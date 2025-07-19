from typing import Tuple, Optional, Union, Dict, List
from astrbot.api.star import StarTools
from astrbot.api import logger

import aiosqlite
import os


class BattleFieldDataBase:
    bf_db_name = "battle_filed_tool.db"

    def __init__(self, bf_db_path: str = None):
        super().__init__()
        if bf_db_path is None:
            self.bf_db_path = (
                StarTools.get_data_dir("battleField_tool_plugin") / self.bf_db_name
            )
        else:
            self.bf_db_path = bf_db_path / self.bf_db_name
        self._conn = None

    async def initialize(self):
        """异步初始化数据库"""
        await self._init_db()
        self._conn = await self._get_conn()

    async def _init_db(self):
        """初始化数据库连接"""
        sql_path = os.path.join(
            os.path.dirname(__file__) / "sql" / "battleField_tool_plugin_init.sql"
        )
        if not os.path.exists(sql_path):
            logger.error(f"初始化SQL文件不存在: {sql_path}")
            raise FileNotFoundError(f"初始化SQL文件不存在: {sql_path}")
        try:
            with open(sql_path, encoding="utf-8") as f:
                sql_script = f.read()

            async with await self._get_conn() as conn:
                await conn.executescript(sql_script)
                await conn.commit()
                logger.info("数据库初始化成功")

        except aiosqlite.Error as e:
            logger.error(f"数据库初始化失败: {e}")
            raise RuntimeError(f"数据库初始化失败: {e}")

    async def _get_conn(self) -> aiosqlite.Connection:
        """获取异步数据库连接(复用现有连接或创建新连接)

        Returns:
            aiosqlite.Connection: 数据库连接对象

        Raises:
            RuntimeError: 当连接失败时抛出
        """
        if self._conn and not self._conn._connection.closed:
            return self._conn

        try:
            conn = await aiosqlite.connect(self.bf_db_path)
            conn.text_factory = str
            return conn
        except aiosqlite.Error as e:
            logger.error(f"数据库连接失败: {e}")
            raise RuntimeError(f"无法连接到数据库: {e}")

    async def close(self):
        """关闭数据库连接"""
        if self._conn and not self._conn._connection.closed:
            await self._conn.close()
            self._conn = None

    async def exec_sql(self, sql: str, params: Tuple = None):
        """
        执行SQL(复用现有连接)

        Args:
            sql: 要执行的SQL查询语句
            params: 查询参数，可以是元组或字典
        """
        conn = await self._get_conn()
        try:
            cursor = await conn.cursor()
            await cursor.execute(sql, params or ())
            await conn.commit()
        except aiosqlite.Error:
            await conn.rollback()
            raise

    async def query(
        self,
        sql: str,
        params: Optional[Union[Tuple, Dict]] = None,
        fetch_all: bool = True,
    ) -> Union[List[Dict], Optional[Dict]]:
        """
        执行SQL查询并返回结果(复用现有连接)

        Args:
            sql: 要执行的SQL查询语句
            params: 查询参数，可以是元组或字典
            fetch_all: 是否获取所有结果（False时只返回第一条）

        Returns:
            当 fetch_all=True 时返回 List[Dict]
            当 fetch_all=False 时返回单个 Dict 或 None（无结果时）

        Raises:
            aiosqlite.Error: 数据库操作失败时抛出
        """
        conn = await self._get_conn()
        try:
            conn.row_factory = aiosqlite.Row  # 使结果可转为字典
            cursor = await conn.cursor()

            # 根据参数类型选择执行方式
            if isinstance(params, dict):
                await cursor.execute(sql, params)
            else:
                await cursor.execute(sql, params or ())

            if fetch_all:
                return [dict(row) for row in await cursor.fetchall()]
            else:
                if result := await cursor.fetchone():
                    return dict(result)
                return None

        except aiosqlite.Error as e:
            logger.error(f"查询失败: {e}\nSQL: {sql}\nParams: {params}")
            raise
