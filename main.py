from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, StarTools, register
from astrbot.api.all import AstrBotConfig
from astrbot.api import logger

from typing import Union, Pattern
from data.plugins.astrbot_plugin_battlefield_tool.utils.requestUtil import request_api
from data.plugins.astrbot_plugin_battlefield_tool.database.BattleFieldDataBase import (
    BattleFieldDataBase,
)
from data.plugins.astrbot_plugin_battlefield_tool.database.BattleFieldDBService import (
    BattleFieldDBService,
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


@register(
    "astrbot_plugin_battlefield_tool",  # name
    "SHOOTING_STAR_C",  # author
    "战地风云战绩查询插件",  # desc
    "v1.0.5",  # version
)
class BattlefieldTool(Star):
    STAT_PATTERN = re.compile(
        r"^(\w*)(?:[，,]?game=([\w\-+.]+))?$"
    )  # 正则提取用户名和要查询的游戏
    LANG_CN = "zh-cn"
    LANG_TW = "zh-tw"

    def __init__(self, context: Context, config: AstrBotConfig = None):
        super().__init__(context)
        self.config = config

        # 防御性配置处理：如果config为None，使用默认值
        if config is None:
            logger.warning("BattlefieldTool: 未提供配置文件，将使用默认配置")
            self.default_game = "bfv"
            self.timeout_config = 15
            self.img_quality = 90
        else:
            logger.info("BattlefieldTool: 使用用户配置文件")
            self.default_game = config.get("default_game", "bfv")
            self.timeout_config = config.get("timeout_config", 15)
            self.img_quality = config.get("img_quality", 90)

        self.bf_data_path = StarTools.get_data_dir("battleField_tool_plugin")
        self.db = BattleFieldDataBase(self.bf_data_path)  # 初始化数据库
        self.db_service = BattleFieldDBService(self.db)  # 初始化数据库服务
        self._session = None

    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""
        self._session = aiohttp.ClientSession()
        await self.db.initialize()  # 添加数据库初始化调用

    @filter.command("stat")
    async def bf_stat(self, event: AstrMessageEvent):
        """查询用户数据"""
        (
            message_str,
            lang,
            qq_id,
            ea_name,
            game,
            server_name,
            error_msg,
        ) = await self._handle_player_data_request(event, ["stat"])

        if error_msg:
            yield event.plain_result(error_msg)
            return

        logger.info(f"玩家id:{ea_name}，所查询游戏:{game}")
        player_data = await request_api(
            game,
            "all",
            {"name": ea_name, "lang": lang, "platform": "pc"},
            self.timeout_config,
            session=self._session,
        )

        async for result in self._process_api_response(
            event, player_data, "stat", game
        ):
            yield result

    @filter.command("weapons", alias=["武器"])
    async def bf_weapons(self, event: AstrMessageEvent):
        """查询用户武器数据"""
        (
            message_str,
            lang,
            qq_id,
            ea_name,
            game,
            server_name,
            error_msg,
        ) = await self._handle_player_data_request(event, ["weapons", "武器"])

        if error_msg:
            yield event.plain_result(error_msg)
            return

        logger.info(f"玩家id:{ea_name}，所查询游戏:{game}")
        player_data = await request_api(
            game,
            "weapons",
            {"name": ea_name, "lang": lang, "platform": "pc"},
            self.timeout_config,
            session=self._session,
        )

        async for result in self._process_api_response(
            event, player_data, "weapons", game
        ):
            yield result

    @filter.command("vehicles", alias=["载具"])
    async def bf_vehicles(self, event: AstrMessageEvent):
        """查询载具数据"""
        (
            message_str,
            lang,
            qq_id,
            ea_name,
            game,
            server_name,
            error_msg,
        ) = await self._handle_player_data_request(event, ["vehicles", "载具"])

        if error_msg:
            yield event.plain_result(error_msg)
            return

        logger.info(f"玩家id:{ea_name}，所查询游戏:{game}")
        player_data = await request_api(
            game,
            "vehicles",
            {"name": ea_name, "lang": lang, "platform": "pc"},
            self.timeout_config,
            session=self._session,
        )

        async for result in self._process_api_response(
            event, player_data, "vehicles", game
        ):
            yield result

    @filter.command("servers", alias=["服务器"])
    async def bf_servers(self, event: AstrMessageEvent):
        """查询服务器数据"""
        (
            message_str,
            lang,
            qq_id,
            ea_name,
            game,
            server_name,
            error_msg,
        ) = await self._handle_player_data_request(event, ["servers", "服务器"])

        if error_msg:
            yield event.plain_result(error_msg)
            return
        if server_name is None:
            yield event.plain_result("不能查所有哦~")
            return

        logger.info(f"查询服务器:{server_name}，所查询游戏:{game}")
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

        # 特殊处理服务器空数据情况
        if servers_data is None:
            yield event.plain_result("API调用失败，没有响应任何信息")
            return

        if servers_data.get("code") != 200:
            yield event.plain_result(servers_data.get("errors")[0])
            return

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
            server_name,
            error_msg,
        ) = await self._handle_player_data_request(event, ["bind", "绑定"])
        if error_msg:
            yield event.plain_result(error_msg)
            return
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
            return

        if player_data.get("code") != 200:
            yield event.plain_result(player_data.get("errors")[0])
            return

        if player_data.get("code") == 200:
            ea_id = player_data["userId"]
            logger.debug(f"已查询到{ea_name}的ea_id：{ea_id}")
            # 持久化绑定数据
            msg = await self.db_service.upsert_user_bind(qq_id, ea_name, ea_id)
            yield event.plain_result(msg)

    @filter.command("bf_init")
    async def bf_init(self, event: AstrMessageEvent):
        """同一机器人不同会话渠道配置不同的默认查询"""
        message_str = event.message_str
        session_channel_id = event.get_sender_id()

        if not event.is_private_chat():
            # 群聊只能机器人管理员设置渠道绑定命令
            if not event.is_admin():
                yield event.plain_result(
                    "没有权限哦，群聊只能机器人管理员使用[bf_init]命令呢"
                )
                return

            session_channel_id = event.get_group_id()

        # 解析命令
        ea_name, game = await self._parse_input_regex(
            ["bf_init"], self.STAT_PATTERN, message_str
        )
        # 由于共用解析命令所以这里赋个值
        default_game = ea_name
        if default_game is None:
            yield event.plain_result("不能设置空哦~")
        else:
            # 持久化渠道数据
            msg = await self.db_service.upsert_session_channel(
                session_channel_id, default_game
            )
            yield event.plain_result(msg)

    async def _process_api_response(self, event, api_data, data_type, game):
        """处理API响应通用逻辑"""
        if api_data is None:
            yield event.plain_result("API调用失败，没有响应任何信息")
            return

        if api_data.get("code") != 200:
            yield event.plain_result(api_data.get("errors")[0])
            return

        api_data["__update_time"] = time.time()

        # 根据数据类型调用对应的图片生成方法
        handler_map = {
            "stat": self._main_data_to_pic,
            "weapons": self._weapons_data_to_pic,
            "vehicles": self._vehicles_data_to_pic,
            "servers": self._servers_data_to_pic,
        }

        pic_url = await handler_map[data_type](api_data, game)
        yield event.image_result(pic_url)

    async def _handle_player_data_request(
        self, event: AstrMessageEvent, str_to_remove_list: list
    ):
        """
        从消息中提取参数
        Args:
            event: AstrMessageEvent
            str_to_remove_list: 去除指令
        Returns:
            tuple: (message_str, lang, qq_id, ea_name, game, error_msg)
            error_msg: 错误信息，成功时为None
        """
        message_str = event.message_str
        lang = self.LANG_CN
        qq_id = event.get_sender_id()
        session_channel_id = event.get_sender_id()
        error_msg = None
        ea_name = None
        game = None
        server_name = None
        if not event.is_private_chat():
            session_channel_id = event.get_group_id()

        try:
            # 解析命令
            ea_name, game = await self._parse_input_regex(
                str_to_remove_list, self.STAT_PATTERN, message_str
            )
            # 由于共用解析方法所以这里赋个值
            if str_to_remove_list == ["servers", "服务器"]:
                server_name = ea_name
            # 如果没有输入游戏标识则先查询渠道配置的
            if game is None:
                bd_game = await self.db_service.query_session_channel(
                    session_channel_id
                )
                if bd_game is None:
                    game = self.default_game
                else:
                    game = bd_game["default_game_tag"]
            # 如果没有传入ea_name则查询已绑定的
            if ea_name is None:
                bind_data = await self.db_service.query_bind_user(qq_id)
                if bind_data is None:
                    error_msg = "请先使用bind [ea_name]绑定"
                else:
                    ea_name = bind_data["ea_name"]
            # 战地1使用繁中
            if game == "bf1":
                lang = self.LANG_TW
        except Exception as e:
            error_msg = str(e)

        return message_str, lang, qq_id, ea_name, game, server_name, error_msg

    @staticmethod
    async def _parse_input_regex(
        str_to_remove_list: list[str],
        pattern: Union[Pattern[str], None],
        base_string: str,
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
            game = match.group(2)
        else:
            ea_name = clean_str.strip()
            game = None
        return ea_name, game

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

    @filter.command("bf_help")
    async def bf_help(self, event: AstrMessageEvent):
        """显示战地插件帮助信息"""
        help_msg = """战地风云插件使用帮助：
1. 账号绑定
命令: /bind [ea_name] 或 /绑定 [ea_name]
参数: ea_name - 您的EA账号名
示例: /bind ExamplePlayer

2. 默认查询设置
命令: /bf_init [游戏代号]
参数: 游戏代号(bf4/bf1/bfv等)
注意: 私聊都能使用，群聊中仅bot管理员可用

3. 战绩查询
命令: /stat [ea_name],game=[游戏代号]
参数:
  ea_name - EA账号名(可选，已绑定则可不填)
  game - 游戏代号(可选)
示例: /stat ExamplePlayer,game=bf1

4. 武器统计
命令: /weapons [ea_name],game=[游戏代号] 或 /武器 [ea_name],game=[游戏代号]
参数同上
示例: /weapons ExamplePlayer,game=bfv

5. 载具统计
命令: /vehicles [ea_name],game=[游戏代号] 或 /载具 [ea_name],game=[游戏代号]
参数同上
示例: /vehicles ExamplePlayer

6. 服务器查询
命令: /servers [server_name],game=[游戏代号] 或 /服务器 [server_name],game=[游戏代号]
参数:
  server_name - 服务器名称(必填)
  game - 游戏代号(可选)
示例: /servers 中文服务器,game=bf1

注: 实际使用时不需要输入[]。/为唤醒词，以实际情况为准
"""
        yield event.plain_result(help_msg)

    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件卸载/停用时会调用。"""
