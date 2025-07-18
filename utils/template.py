from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from astrbot.api import logger

import time, json, os, base64

from pycparser.c_ast import Default

PARENT_FOLDER = Path(__file__).parent.parent.resolve()

# 各代的banner
BF3_BANNER = "https://s21.ax1x.com/2025/07/16/pV1jG5t.jpg"
BF4_BANNER = "https://s21.ax1x.com/2025/07/16/pV1XV1S.jpg"
BF1_BANNER = "https://s1.ax1x.com/2022/12/15/zoMaxe.jpg"
BFV_BANNER = 'https://s1.ax1x.com/2022/12/14/z54oIs.jpg'
# BF2042_BANNER = "https://s1.ax1x.com/2023/01/24/pSYXS3Q.jpg"
BANNERS = {"bf3": BF3_BANNER,"bf4": BF4_BANNER,"bf1": BF1_BANNER,"bfv": BFV_BANNER}


BF3_LOGO = "https://s21.ax1x.com/2025/07/19/pV3I9ET.png"
BF4_LOGO = "https://s21.ax1x.com/2025/07/19/pV3IRaT.png"
BF1_LOGO = "https://s21.ax1x.com/2025/07/19/pV35O3j.png"
BFV_LOGO = "https://s21.ax1x.com/2025/07/19/pV35LCQ.png"

LOGOS = {"bf3": BF3_LOGO,"bf4": BF4_LOGO,"bf1": BF1_LOGO,"bfv": BFV_LOGO}

#默认头像
DEFAULT_AVATAR = "https://s21.ax1x.com/2025/07/16/pV1Ox6e.jpg"

# 创建Jinja2环境并设置模板加载路径
template_dir = PARENT_FOLDER / 'template'
env = Environment(loader=FileSystemLoader(template_dir))

MAIN_TEMPLATE = env.get_template('template.html')
WEAPONS_TEMPLATE = env.get_template('template_weapons.html')
VEHICLES_TEMPLATE = env.get_template('template_vehicles.html')
SERVERS_TEMPLATE = env.get_template('template_servers.html')
WEAPON_CARD = env.get_template('weapon_card.html')
VEHICLE_CARD = env.get_template('vehicle_card.html')
CLASSES_CARD = env.get_template('classes_card.html')
SERVER_CARD = env.get_template('server_card.html')


def sort_list_of_dicts(list_of_dicts, key):
    """降序排序"""
    return sorted(list_of_dicts, key=lambda k: k[key], reverse=True)


def prepare_weapons_data(d: dict, lens: int):
    """提取武器数据，格式化使用时间"""
    weapons_list = d['weapons']
    weapons_list = sort_list_of_dicts(weapons_list, 'kills')
    for w in weapons_list[:lens]:
        time_equipped = w.get('timeEquipped', 0)
        w['__timeEquippedHours'] = round(time_equipped / 3600, 2)
    return [
        {**w, '__timeEquippedHours': round(w.get('timeEquipped', 0) / 3600, 2)}
        for w in weapons_list[:lens]
        if (w.get('timeEquipped', 0) > 0 and w.get('kills', 0) > 0)
    ]


def prepare_vehicles_data(d: dict, lens: int):
    """提取载具数据，格式化使用时间"""
    vehicles_list = d['vehicles']
    vehicles_list = sort_list_of_dicts(vehicles_list, 'kills')
    for v in vehicles_list[:lens]:
        time_in = v.get('timeIn', 0)
        v['__timeInHour'] = round(time_in / 3600, 2)
    return [
        {**w, '__timeInHour': round(w.get('timeIn', 0) / 3600, 2)}
        for w in vehicles_list[:lens]
        if (w.get('timeIn', 0) > 0 and w.get('kills', 0) > 0)
    ]


def bf_main_html_builder(d, game):
    """
        构建主要html
        Args:
            d: 查询到的数据
            game: 所查询的游戏
        Returns:
            构建的Html
    """
    banner = BANNERS[game]
    if d.get("avatar") is None:
        d["avatar"] = DEFAULT_AVATAR
    update_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(d['__update_time']))
    d['__hoursPlayed'] = round(d['secondsPlayed'] / 3600, 2)

    # 整理数据
    weapon_data = prepare_weapons_data(d, 5)
    vehicle_data = prepare_vehicles_data(d, 5)

    html = MAIN_TEMPLATE.render(
        banner=banner,
        update_time=update_time,
        d=d,
        weapon_data=weapon_data if weapon_data else None,
        vehicle_data=vehicle_data if vehicle_data else None,
        game=game
    )
    return html


def bf_weapons_html_builder(d, game):
    """
        构建武器html
        Args:
            d: 查询到的数据
            game: 所查询的游戏
        Returns:
            构建的Html
    """
    banner = BANNERS[game]
    if d.get("avatar") is None:
        d["avatar"] = DEFAULT_AVATAR
    update_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(d['__update_time']))

    # 整理数据
    weapon_data = prepare_weapons_data(d, 50)

    html = WEAPONS_TEMPLATE.render(
        banner=banner,
        update_time=update_time,
        d=d,
        weapon_data=weapon_data if weapon_data else None,
        game=game
    )
    return html


def bf_vehicles_html_builder(d, game):
    """
        构建主要html
        Args:
            d: 查询到的数据
            game: 所查询的游戏
        Returns:
            构建的Html
    """
    banner = BANNERS[game]
    if d.get("avatar") is None:
        d["avatar"] = DEFAULT_AVATAR
    update_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(d['__update_time']))

    # 整理数据
    vehicle_data = prepare_vehicles_data(d, 50)

    html = VEHICLES_TEMPLATE.render(
        banner=banner,
        update_time=update_time,
        d=d,
        vehicle_data=vehicle_data if vehicle_data else None,
        game=game
    )
    return html


def bf_servers_html_builder(servers_data, game):
    """
        构建主要html
        Args:
            servers_data: 查询到的数据
            game: 所查询的游戏
        Returns:
            构建的Html
    """
    banner = BANNERS[game]
    logo = LOGOS[game]
    update_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(servers_data['__update_time']))

    html = SERVERS_TEMPLATE.render(
        banner=banner,
        logo=logo,
        update_time=update_time,
        servers_data=servers_data['servers'] if servers_data else None,
        game=game
    )
    return html
