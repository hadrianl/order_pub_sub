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


init(autoreset=True)
context = zmq.Context()
socket = context.socket(zmq.SUB)
ip = input('输入IP：')
# ip = ip if ip else '*'
port = input('请输入端口号(默认为5000):')
port = port if port else '5000'
socket.connect(f"tcp://{ip}:{port}")
socket.setsockopt_string(zmq.SUBSCRIBE, '')
orders_dict = {}
def order_type_mapping(order_comment):
    if 'cancelled' in order_comment:
        return '取消订单'
    elif '[sl]' in order_comment:
        return '止损'
    elif '[tp]' in order_comment:
        return '止盈'
    else:
        return '平仓'

print('订阅订单变化成功.................')
while True:
    try:
        new_order = socket.recv_pyobj()
        # todo LOG
        orders_dict.update(new_order)
        if new_order.get('Status') == 1:
            text = f"""{Fore.WHITE}{str(datetime.now()):}{Fore.RESET}
{Back.BLUE}#{new_order.get('Ticket')}---开仓{Back.RESET}：{new_order}
            """
        elif new_order.get('Status') == 2:
            text = f"""{Fore.WHITE}{str(datetime.now()):}{Fore.RESET}
{Back.YELLOW}#{new_order.get('Ticket')}---{order_type_mapping(new_order.get('Comment'))}{Back.RESET}：{new_order}
            """
        elif new_order.get('Status') == 0:
            text = f"""{Fore.WHITE}{str(datetime.now()):}{Fore.RESET}
{Back.BLUE}#{new_order.get('Ticket')}---挂单{Back.RESET}：{new_order}
            """
        elif new_order.get('Status') == -1:
            text = f"""{Fore.WHITE}{str(datetime.now()):}{Fore.RESET}
{Back.LIGHTWHITE_EX}#{new_order.get('Ticket')}---取消订单{Back.RESET}：{new_order}
            """
        else:
            text = f"""{Fore.WHITE}{str(datetime.now()):}{Fore.RESET}
{Back.YELLOW}#{new_order.get('Ticket')}---{Back.RESET}：{new_order}
            """

        print(text)
    except Exception as e:
        print('关闭监测CLIENT！', e)
        socket.close()
        df = pd.DataFrame(orders_dict)
        df.to_excel('orders.xlsx')
        time.sleep(10)
        break
