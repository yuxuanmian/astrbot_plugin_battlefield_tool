from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from astrbot.api import logger

import time,json,os

PARENT_FOLDER = Path(__file__).parent.parent.resolve()

BFV_BANNER = 'https://s1.ax1x.com/2022/12/14/z54oIs.jpg'
BF1_BANNER = "https://s1.ax1x.com/2022/12/15/zoMaxe.jpg"
BF2042_BANNER = "https://s1.ax1x.com/2023/01/24/pSYXS3Q.jpg"

BANNERS = {"bfv": BFV_BANNER, "bf1": BF1_BANNER, "bf2042": BF2042_BANNER}

# 创建Jinja2环境并设置模板加载路径
template_dir = PARENT_FOLDER / 'template'
env = Environment(loader=FileSystemLoader(template_dir))

MAIN_TEMPLATE = env.get_template('template.html')
MAIN2042_TEMPLATE = env.get_template('template2042.html')
WEAPON_CARD = env.get_template('weapon_card.html')
VEHICLE_CARD = env.get_template('vehicle_card.html')
CLASSES_CARD = env.get_template('classes_card.html')
JS_PATH= PARENT_FOLDER / 'js/src.js'
STYLE_PATH = PARENT_FOLDER / 'css/style.css'


def sort_list_of_dicts(list_of_dicts, key):
    return sorted(list_of_dicts, key=lambda k: k[key], reverse=True)


def prepare_weapons_data(d: dict, lens: int):
    weapons_list = d['weapons']
    weapons_list = sort_list_of_dicts(weapons_list, 'kills')
    for w in weapons_list[:lens]:
        time_equipped = w.get('timeEquipped', 0)
        w['__timeEquippedHours'] = round(time_equipped / 3600,2)
    return weapons_list[:lens]

def prepare_vehicles_data(d: dict, lens: int):
    vehicles_list = d['vehicles']
    vehicles_list = sort_list_of_dicts(vehicles_list, 'kills')
    for v in vehicles_list[:lens]:
        time_in = v.get('timeIn', 0)
        v['__timeInHour'] = round(time_in / 3600,2)
    return vehicles_list[:lens]

def html_builder(d, game='bfv'):
    banner = BANNERS[game]
    update_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(d['__update_time']))
    d['__hoursPlayed'] = round(d['secondsPlayed'] / 3600,2)

    # 准备数据而不是渲染HTML
    weapon_data = prepare_weapons_data(d, 5)
    vehicle_data = prepare_vehicles_data(d, 5)

    html = MAIN_TEMPLATE.render(
        banner=banner,
        update_time=update_time,
        d=d,
        weapon_data=weapon_data if weapon_data else None,
        vehicle_data=vehicle_data if vehicle_data else None,
        game=game,
        js_path=JS_PATH,
        style_path=STYLE_PATH,
    )
    return html
