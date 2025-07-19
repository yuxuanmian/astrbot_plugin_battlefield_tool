from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register, StarTools
from astrbot.api.all import AstrBotConfig
from astrbot.api import logger

from typing import Union, Pattern
from data.plugins.astrbot_plugin_battlefield_tool.utils.requestUtil import request_api
from data.plugins.astrbot_plugin_battlefield_tool.database.BattleFieldDataBase import (
    BattleFieldDataBase,
)
from data.plugins.astrbot_plugin_battlefield_tool.utils.template import (
    bf_main_html_builder,
    bf_weapons_html_builder,
    bf_vehicles_html_builder,
    bf_servers_html_builder,
)

import re
import time
import aiohttp


class BattlefieldTool(Star):
    STAT_PATTERN = re.compile(
        r"^(\w*)(?:[，,]?game=([\w\-+.]+))?$"
    )  # 正则提取用户名和要查询的游戏
    LANG_CN = "zh-cn"
    LANG_TW = "zh-tw"

    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        self.default_game = config.get("default_game")
        self.timeout_config = config.get("timeout_config")
        self.img_quality = config.get("img_quality")
        self.bf_data_path = StarTools.get_data_dir("battleField_tool_plugin")
        self.db = BattleFieldDataBase(self.bf_data_path)  # 初始化数据库
        self._session = None

    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""
        self._session = aiohttp.ClientSession()

    @filter.command("stat")
    async def bf_stat(self, event: AstrMessageEvent):
        """查询用户数据"""
        (
            message_str,
            lang,
            qq_id,
            ea_name,
            game,
        ) = await self._handle_player_data_request(event, ["stat"])
        logger.info(f"玩家id:{ea_name}，所查询游戏:{game}")
        # 调用API查询玩家数据
        player_data = await request_api(
            game,
            "all",
            {"name": ea_name, "lang": lang, "platform": "pc"},
            self.timeout_config,
            session=self._session,
        )
        if player_data is None:
            yield event.plain_result("API调用失败，没有响应任何信息")
        if player_data.get("code") != 200:
            yield event.plain_result(player_data.get("errors")[0])
        if player_data.get("code") == 200:
            player_data["__update_time"] = time.time()
            pic_url = await self._main_data_to_pic(player_data, game)
            yield event.image_result(pic_url)

    @filter.command("weapons", alias=["武器"])
    async def bf_weapons(self, event: AstrMessageEvent):
        """查询用户武器数据"""
        (
            message_str,
            lang,
            qq_id,
            ea_name,
            game,
        ) = await self._handle_player_data_request(event, ["weapons", "武器"])
        logger.info(f"玩家id:{ea_name}，所查询游戏:{game}")
        # 调用API查询玩家数据
        player_data = await request_api(
            game,
            "weapons",
            {"name": ea_name, "lang": lang, "platform": "pc"},
            self.timeout_config,
            session=self._session,
        )
        if player_data is None:
            yield event.plain_result("API调用失败，没有响应任何信息")
        if player_data.get("code") != 200:
            yield event.plain_result(player_data.get("errors")[0])
        if player_data.get("code") == 200:
            player_data["__update_time"] = time.time()
            pic_url = await self._weapons_data_to_pic(player_data, game)
            yield event.image_result(pic_url)

    @filter.command("vehicles", alias=["载具"])
    async def bf_vehicles(self, event: AstrMessageEvent):
        """查询载具数据"""
        (
            message_str,
            lang,
            qq_id,
            ea_name,
            game,
        ) = await self._handle_player_data_request(event, ["vehicles", "载具"])
        # 调用API查询玩家数据
        logger.info(f"玩家id:{ea_name}，所查询游戏:{game}")
        player_data = await request_api(
            game,
            "vehicles",
            {"name": ea_name, "lang": lang, "platform": "pc"},
            self.timeout_config,
            session=self._session,
        )
        if player_data is None:
            yield event.plain_result("API调用失败，没有响应任何信息")
        if player_data.get("code") != 200:
            yield event.plain_result(player_data.get("errors")[0])
        if player_data.get("code") == 200:
            player_data["__update_time"] = time.time()
            pic_url = await self._vehicles_data_to_pic(player_data, game)
            yield event.image_result(pic_url)

    @filter.command("servers", alias=["服务器"])
    async def bf_servers(self, event: AstrMessageEvent):
        """查询战地五用户数据"""
        (
            message_str,
            lang,
            qq_id,
            server_name,
            game,
        ) = await self._handle_player_data_request(event, ["servers", "服务器"])
        if server_name is None:
            raise ValueError("不能查所有哦~")
        logger.info(f"查询服务器:{server_name}，所查询游戏:{game}")
        # 调用API查询玩家数据
        servers_data = await request_api(
            game,
            "servers",
            {
                "name": server_name,
                "lang": lang,
                "platform": "pc",
                "region": "all",
                "limit": 30,
            },
            self.timeout_config,
            session=self._session,
        )
        if servers_data is None:
            yield event.plain_result("API调用失败，没有响应任何信息")
        if servers_data.get("code") != 200:
            yield event.plain_result(servers_data.get("errors")[0])
        if servers_data.get("code") == 200:
            if servers_data["servers"] is not None and len(servers_data["servers"]) > 0:
                servers_data["__update_time"] = time.time()
                pic_url = await self._servers_data_to_pic(servers_data, game)
                yield event.image_result(pic_url)
            else:
                yield event.plain_result("暂无数据")

    @filter.command("bind", alias=["绑定"])
    async def bf_bind(self, event: AstrMessageEvent):
        """绑定本插件默认查询的用户"""
        (
            message_str,
            lang,
            qq_id,
            ea_name,
            game,
        ) = await self._handle_player_data_request(event, ["bind", "绑定"])
        # 调用bfv的接口查询用户是否存在
        player_data = await request_api(
            self.default_game,
            "stats",
            {"name": ea_name, "lang": "zh-cn", "platform": "pc"},
            self.timeout_config,
            session=self._session,
        )
        if player_data is None:
            yield event.plain_result("API调用失败，没有响应任何信息")
        if player_data.get("code") != 200:
            yield event.plain_result(player_data.get("errors")[0])
        if player_data.get("code") == 200:
            ea_id = player_data["userId"]
            logger.debug(f"已查询到{ea_name}的ea_id：{ea_id}")
            # 持久化绑定数据
            msg = await self.upsert_user_bind(qq_id, ea_name, ea_id)
            yield event.plain_result(msg)

    async def _handle_player_data_request(
        self, event: AstrMessageEvent, str_to_remove_list: list
    ):
        """
        从消息中提取参数
        Args:
            event: AstrMessageEvent
            str_to_remove_list: 去除指令
        Returns:
            message_str,lang,qq_id,ea_name,game
        """
        message_str = event.message_str
        lang = self.LANG_CN
        qq_id = event.get_sender_id()
        # 解析命令
        ea_name, game = self._parse_input_regex(
            str_to_remove_list, self.STAT_PATTERN, message_str, self.default_game
        )
        # 如果没有传入ea_name则查询已绑定的
        if ea_name is None:
            bind_data = await self._query_bind_user(qq_id)
            if bind_data is None:
                raise ValueError("请先使用bind [ea_name]绑定")
            else:
                ea_name = bind_data["ea_name"]
        # 战地1使用繁中
        if game == "bf1":
            lang = self.LANG_TW
        return message_str, lang, qq_id, ea_name, game

    def _parse_input_regex(
        self,
        str_to_remove_list: list[str],
        pattern: Union[Pattern[str], None],
        base_string: str,
        default_game: str,
    ):
        """私有方法：从base_string中移除str_to_remove_list并去空格，然后根据正则取出参数
        Args:
            str_to_remove_list: 需要移除的子串list
            base_string: 原始字符串
            default_game: 默认查询的游戏
        Returns:
            处理后的字符串
        """
        # 移除目标子串和空格
        for str_to_remove in str_to_remove_list:
            base_string = base_string.replace(str_to_remove, "")
        clean_str = base_string.replace(" ", "")
        # 用正则提取输入的参数
        if pattern is not None:
            match = pattern.match(clean_str.strip())
            if not match:
                raise ValueError("格式错误，正确格式：[用户名][,game=游戏名]")
            ea_name = match.group(1) or None
            game = match.group(2) or default_game
        else:
            ea_name = clean_str.strip()
            game = default_game
        return ea_name, game

    async def upsert_user_bind(self, qq_id: str, ea_name: str, ea_id: str):
        """
        根据qq号更新或插入EA账号绑定
        Args:
            qq_id: 用户QQ号
            ea_name: 游戏ID名称
            ea_id: EA账号ID
        Returns:
            返回绑定消息
        """
        # 1. 尝试获取旧数据
        old_data = await self._query_bind_user(qq_id)
        # 2. 执行插入或更新
        await self.db.exec_sql(
            """
                         INSERT INTO battleField_user_binds (qq_id, ea_name, ea_id)
                         VALUES (?, ?, ?) ON CONFLICT(qq_id) DO
                         UPDATE SET
                             ea_name = excluded.ea_name,
                             ea_id = excluded.ea_id
                         """,
            (qq_id, ea_name, ea_id),
        )
        if old_data is not None:
            msg = f"更新绑定记数据: {old_data['ea_name']}-->{ea_name}"
        else:
            msg = f"成功绑定EA_NAME：{ea_name}"
        return msg  # 返回旧数据或None

    async def _query_bind_user(self, qq_id: str):
        """
        根据qq号查询绑定的ea_name
            Args:
                qq_id: 用户QQ号
        Returns:
            返回数据（没有则返回None）
        """
        return await self.db.query(
            "SELECT * FROM battleField_user_binds WHERE qq_id = ?",
            (qq_id,),
            fetch_all=False,
        )

    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""

    async def _main_data_to_pic(self, data: dict, game: str):
        """将查询的全部数据转为图片
        Args:
            data:查询到的战绩数据等
        Returns:
            返回生成的图片
        """
        html = bf_main_html_builder(data, game)
        url = await self.html_render(
            html,
            {},
            True,
            {
                "timeout": 10000,
                "quality": self.img_quality,
                "clip": {"x": 0, "y": 0, "width": 700, "height": 2353},
            },
        )
        return url

    async def _weapons_data_to_pic(self, data: dict, game: str):
        """将查询的数据转为图片
        Args:
            data:查询到的战绩数据等
        Returns:
            返回生成的图片
        """
        html = bf_weapons_html_builder(data, game)
        url = await self.html_render(
            html,
            {},
            True,
            {
                "timeout": 10000,
                "quality": self.img_quality,
                "clip": {"x": 0, "y": 0, "width": 700, "height": 10000},
            },
        )
        return url

    async def _vehicles_data_to_pic(self, data: dict, game: str):
        """将查询的数据转为图片
        Args:
            data:查询到的战绩数据等
        Returns:
            返回生成的图片
        """
        html = bf_vehicles_html_builder(data, game)
        url = await self.html_render(
            html,
            {},
            True,
            {
                "timeout": 10000,
                "quality": self.img_quality,
                "clip": {"x": 0, "y": 0, "width": 700, "height": 10000},
            },
        )
        return url

    async def _servers_data_to_pic(self, data: dict, game: str):
        """将查询的服务器数据转为图片
        Args:
            data:查询到的战绩数据等
        Returns:
            返回生成的图片
        """
        # 数据量较少时设置高度
        height = 10000
        if data["servers"] is not None and len(data["servers"]) == 1:
            height = 450
        elif data["servers"] is not None and len(data["servers"]) == 2:
            height = 620
        html = bf_servers_html_builder(data, game)
        url = await self.html_render(
            html,
            {},
            True,
            {
                "timeout": 10000,
                "quality": self.img_quality,
                "clip": {"x": 0, "y": 0, "width": 700, "height": height},
            },
        )
        return url
