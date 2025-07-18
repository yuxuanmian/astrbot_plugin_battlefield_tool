import json,asyncio,aiohttp

from astrbot import logger
from pathlib import Path


API_SITE = "https://api.gametools.network/"


async def request_api(game, prop='stats', params=None,timeout=10):
    """
    异步请求API
        Args:
        game: 游戏代号(bfv/bf1/bf4)
        prop: 请求属性(stats/servers等)
        params: 查询参数
    Returns:
        JSON响应数据
    Raises:
        aiohttp.ClientError: 网络或HTTP错误
        json.JSONDecodeError: 响应不是合法JSON
    """
    if params is None:
        params = {}
    url = API_SITE + f'{game}/{prop}'
    logger.info(f"Battlefield Tool Request Gametools API: {url}，请求参数: {params}")

    async with aiohttp.ClientSession() as session:
        try:
            timeout_obj = aiohttp.ClientTimeout(total=timeout)
            async with session.get(url, params=params, timeout=timeout_obj) as response:
                if response.status == 200:
                    result = await response.json()
                    result['code'] = response.status
                    return result
                else:
                    # 携带状态码和错误信息抛出
                    error_dict = await response.json()
                    error_dict['code'] = response.status
                    logger.error(f"Battlefield Tool 调用接口失败，错误信息{error_dict}")
                    return error_dict
        except aiohttp.ClientError as e:
            error_msg = f"网络请求异常: {str(e)}"
            logger.error(error_msg)
            raise ConnectionError(error_msg) from e
        except json.JSONDecodeError as e:
            error_msg = f"JSON解析失败: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg) from e
        except asyncio.TimeoutError as e:
            error_msg = f"请求超时: {timeout}秒内未收到响应"
            logger.error(error_msg)
            raise TimeoutError(error_msg) from e
