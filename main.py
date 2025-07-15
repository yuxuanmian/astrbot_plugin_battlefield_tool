from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register, StarTools
from astrbot.api import logger

from typing import Union, Optional, Pattern
from data.plugins.astrbot_plugin_battlefield_tool.utils.requestUtil import request_api
from data.plugins.astrbot_plugin_battlefield_tool.database.BattleFiledDataBase import BattleFieldDataBase
from data.plugins.astrbot_plugin_battlefield_tool.utils.template import html_builder

import re, os, time


@register("battlefield", "SHOOTING_STAR_C", "一个BATTLEFIELD数据查询插件", "0.1")
class BattlefieldTool(Star):
    DEFAULT_GAME = "bfv"  # 默认查询哪个游戏
    PIC_FOLDER = "pic_path"  # 默认生成图片的位置
    PIC_PATH = None
    STAT_PATTERN = re.compile(r'^(\w*)(?:,?game=(\w+))?$')  # 正则提取用户名和要查询的游戏

    LANG_CN = 'zh-cn'
    LANG_TW = 'zh-tw'

    def __init__(self, context: Context):
        super().__init__(context)
        self.bf_data_path = StarTools.get_data_dir("battleFiled_tool_plugin")
        self.PIC_PATH = os.path.join(self.bf_data_path, self.PIC_FOLDER)
        self.db = BattleFieldDataBase(self.bf_data_path)  # 初始化数据库

    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""

    # 注册指令的装饰器。指令名为 stat。
    @filter.command("stat")
    async def bf_stat(self, event: AstrMessageEvent):
        """查询战地五用户数据"""
        message_str = event.message_str
        lang = self.LANG_CN
        qq_id = event.get_sender_id()
        # 解析命令
        ea_name, game = self._parse_input_regex('stat', self.STAT_PATTERN, message_str)
        # 如果没有传入ea_name则查询已绑定的
        if ea_name is None:
            bing_data = self._query_bind_user(qq_id)
            if bing_data is None:
                raise ValueError("请先使用bind [ea_name]绑定")
            else:
                ea_name = bing_data['ea_name']
        logger.info(f"玩家id:{ea_name}，所查询游戏:{game}")
        # 战地1使用繁中
        if game == "bf1":
            lang = self.LANG_TW
        # 调用API查询玩家数据
        player_data = await request_api(game, "all", {'name': ea_name, 'lang': lang, 'platform': 'pc'})
        player_data['__update_time'] = time.time()
        pic_url = await self._data_to_pic(player_data, game)

        yield event.image_result(pic_url)  # 发送一条纯文本消息

    @filter.command("bind")
    async def bf_bind(self, event: AstrMessageEvent):
        """绑定本插件默认查询的用户"""
        message_str = event.message_str
        qq_id = event.get_sender_id()
        ea_name, game = self._parse_input_regex('bind', None, message_str)
        player_data = await request_api('bfv', "stats", {'name': ea_name, 'lang': 'zh-cn', 'platform': 'pc'})
        ea_id = player_data['userId']
        logger.debug(f"已查询到{ea_name}的ea_id：{ea_id}")
        msg = self.upsert_user_bind(qq_id, ea_name, ea_id)

        yield event.plain_result(msg)

    def _parse_input_regex(self, str_to_remove: str, pattern: Union[Pattern[str], None], base_string: str,
                           default_game: str = "bfv"):
        """私有方法：从base_string中移除str_to_remove并去空格，然后根据正则取出参数
        Args:
            str_to_remove: 需要移除的子串
            base_string: 原始字符串
            default_game: 默认查询的游戏
        Returns:
            处理后的字符串
        """
        # 移除目标子串和空格
        clean_str = base_string.replace(str_to_remove, '').replace(' ', '')
        logger.info(clean_str)
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

    def upsert_user_bind(self, qq_id: str, ea_name: str, ea_id: str):
        """
        根据qq号更新或插入EA账号绑定
        Args:
            qq_id: 用户QQ号
            ea_name: 游戏ID名称
            ea_id: EA账号ID
        Returns:
            返回更新前的旧数据（如果没有旧数据则返回None）
        """
        # 1. 尝试获取旧数据
        old_data = self._query_bind_user(qq_id)
        # 2. 执行插入或更新
        self.db.exec_sql("""
                         INSERT INTO battleField_user_binds (qq_id, ea_name, ea_id)
                         VALUES (?, ?, ?) ON CONFLICT(qq_id) DO
                         UPDATE SET
                             ea_name = excluded.ea_name,
                             ea_id = excluded.ea_id
                         """, (qq_id, ea_name, ea_id))
        if old_data is not None:
            msg = f"更新绑定记数据: {old_data['ea_name']}-->{ea_name}"
        else:
            msg = f"成功绑定EA_NAME[{ea_name}]"
        return msg  # 返回旧数据或None

    def _query_bind_user(self, qq_id: str):
        """
        根据qq号查询绑定的ea_name
            Args:
                qq_id: 用户QQ号
        Returns:
            返回数据（没有则返回None）
        """
        return self.db.query(
            "SELECT * FROM battleField_user_binds WHERE qq_id = ?", (qq_id,), fetch_all=False
        )

    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""

    async def _data_to_pic(self, data: dict, game: str):
        """将查询的数据转为图片
        Args:
            data:查询到的战绩数据等
        Returns:
            返回生成的图片
        """
        html = html_builder(data, game)
        url = await self.html_render(html, {}, True, {"clip": {"x": 0, "y": 0, "width": 700, "height": 2353}})
        # url = await self.html_render(html, {}, True, {"clip": {0,0,700,10}})
        return url
