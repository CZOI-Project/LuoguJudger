import traceback

from aiohttp import web

import config


def get_exception_details(exception) -> str:
    """
    获取异常的详细信息，包括异常类型、异常信息和堆栈跟踪信息，
    并返回一个包含这些信息的字符串。

    :param exception: 异常实例
    :return: 包含异常详情的字符串
    """
    # 获取异常类型和异常信息
    exception_type = type(exception).__name__
    exception_message = str(exception)

    # 获取堆栈跟踪信息
    stack_trace = ''.join(traceback.format_tb(exception.__traceback__))

    # 将所有信息格式化为一个字符串
    details = f"来自 Judger 的内部错误\n"
    details += f"JID: {config.jid}\n"
    details += f"Exception Type: {exception_type}\n"
    details += f"Exception Message: {exception_message}\n"
    details += f"Stack Trace:\n{stack_trace}"

    return details


def response_ok(data=None):
    if data is None:
        return web.json_response({"code": config.response_status_ok})
    else:
        return web.json_response({"code": config.response_status_ok, "data": data})


def response_code(code: int):
    return web.json_response({"code": code})


def response_error(message: str):
    return web.json_response({"code": config.response_status_error, "message": message})


def response_message(message: str):
    return web.json_response({"code": config.response_status_msg, "message": message})


def format_number(num):
    # 判断数字是否已经有小数部分
    if num != int(num):
        # 如果有小数部分，保留一位小数
        return round(num, 1)
    else:
        # 如果没有小数部分，保留整数
        return int(num)


def get_time_text(num):
    if num <= 9999:
        return f"{num}ms"
    else:
        return f"{format_number(num / 1000)}s"


def get_mem_text(num):
    if num <= 999:
        return f"{num}KB"
    else:
        return f"{format_number(num / 1024)}MB"
