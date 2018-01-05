#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/12/29 0029 16:23
# @Author  : Hadrianl 
# @File    : order_detail_sub.py
# @License : (C) Copyright 2013-2017, 凯瑞投资

"""
该脚本的订阅端脚本，需要输入发布端的IP与端口号
"""

import zmq
import pandas as pd
from datetime import datetime
import time
from colorama import init, Fore, Back, Style
import logging.config
import sys

logging.config.fileConfig('log.conf')
logger = logging.getLogger('order_subscribe')
init(autoreset=True)
try:
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    ip = input('输入IP：')
    port = input('请输入端口号(默认为5000):')
    port = port if port else '5000'
    socket.connect(f"tcp://{ip}:{port}")
    socket.setsockopt_string(zmq.SUBSCRIBE, '')
    orders_dict = {}
except Exception:
    logger.exception(f'初始化连接失败---tcp://{ip}:{port}')
    sys.exit()

logger.info(f'订阅订单变化成功  from  {ip}:{port}')
try:
    while True:
        new_order = socket.recv_pyobj()
        orders_dict.update({new_order.get('Ticket'):new_order})
        if new_order.get('Status') == 1:
            log_info = f'账户:{new_order.get("Account_ID")}--于{new_order.get("OpenTime")}开仓--{new_order.get("Symbol")}@{new_order.get("OpenPrice")}-#{new_order.get("Ticket")}'
        elif new_order.get('Status') == 0:
            log_info = f'账户:{new_order.get("Account_ID")}--于{new_order.get("OpenTime")}挂单--{new_order.get("Symbol")}@{new_order.get("OpenPrice")}-#{new_order.get("Ticket")}'
        elif new_order.get('Status') == -1:
            log_info = f'账户:{new_order.get("Account_ID")}--于{new_order.get("OpenTime")}取消挂单--{new_order.get("Symbol")}@{new_order.get("OpenPrice")}-#{new_order.get("Ticket")}'
        elif new_order.get('Status') == 2:
            tp = new_order.get('Comment').find('[tp]') != -1
            sl = new_order.get('Comment').find('[sl]') != -1
            has_comment = bool(new_order.get('Comment'))
            close_type = {0: '平仓', 1: new_order.get('Comment'), 2: '止损', 3: '止盈', 4: new_order.get('Comment')}.get(((tp << 1) + sl + 1) * has_comment)
            log_info = f'账户:{new_order.get("Account_ID")}--于{new_order.get("OpenTime")}{close_type}--{new_order.get("Symbol")}@{new_order.get("OpenPrice")}-#{new_order.get("Ticket")}'
        else:
            log_info = f'Status:{new_order.get("Status")}'
        logger.info(log_info)
except Exception as e:
    logger.exception('订阅接收异常')
    socket.close()
    df = pd.DataFrame([nd for _, nd in orders_dict.items()])
    df.to_excel('orders.xlsx')
except SystemExit:
    print('正向关闭订阅.........')
    socket.close()
    df = pd.DataFrame([nd for _, nd in orders_dict.items()])
    df.to_excel('orders.xlsx')
    time.sleep(3)