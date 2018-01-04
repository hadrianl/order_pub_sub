#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/12/29 0029 14:57
# @Author  : Hadrianl 
# @File    : order_detail_pub.py
# @License : (C) Copyright 2013-2017, 凯瑞投资

"""
该脚本为新单变化的推送发布端，对接的数据库，以及开放的发布端口可在conf.ini里设置,ini内默认port为5000
"""

import pymysql as pm
import time
from zmq_pub_func import pub
import configparser
from colorama import Fore, Back, init, Style
import asyncio
from datetime import datetime
from zmq.asyncio import Context, ZMQEventLoop

init(autoreset=True)
conf = configparser.ConfigParser()
conf.read('conf.ini')
dbconfig = {'host': conf.get('MYSQL', 'host'),
            'port': conf.getint('MYSQL', 'port'),
            'user': conf.get('MYSQL', 'user'),
            'password': conf.get('MYSQL', 'password'),
            'db': conf.get('MYSQL', 'db'),
            'cursorclass': pm.cursors.DictCursor,
            }
zmq_port = conf.getint('ZMQ', 'port')
conn = pm.connect(**dbconfig)
try:
    with conn.cursor() as cursor:
        sql = 'select MAX(OpenTime) as init_time from order_detail'
        cursor.execute(sql)
        last_time = cursor.fetchone()['init_time']
        conn.commit()
except Exception as e:
    print('获取最新时间失败')
    raise e


async def run_pub():
    global last_time
    print(last_time)
    print('订阅端口----*:', zmq_port)
    orders_dict = {}
    with pub(zmq_port) as p:
        while True:
            with conn.cursor() as cursor:
                try:
                    sql = f'select * from order_detail where OpenTime>"{str(last_time)}"'
                    cursor.execute(sql)
                    new_orders = cursor.fetchall()
                    if new_orders:
                        last_time = max([d.get('OpenTime') for d in new_orders])
                        # print(str(datetime.now()))
                        for d in new_orders:
                            orders_dict.update({d.get('Ticket'): d})
                            # todo LOG
                            if d.get('Type') == 6:
                                # p.send_changed_order(d)
                                pass
                            else:
                                await p.send_changed_order(d)
                                print(f'{Back.BLUE}#{d.get("Ticket")}---开仓{Back.RESET}：{d}')
                                print('------------------------------------------------------------------------------')

                    remaining_orders = [str(t) for t, v in orders_dict.items() if
                                        v.get('Status') == 1 or v.get('Status') == 0]
                    if remaining_orders:
                        sql = f'select * from order_detail where Ticket in ({",".join(remaining_orders)}) and CloseTime>"1970-01-01 00:00:00"'
                        cursor.execute(sql)
                        closed_orders = cursor.fetchall()
                        if closed_orders:
                            for d in closed_orders:
                                orders_dict.update({d.get('Ticket'): d})
                                # todo LOG
                                if 'cancelled' in d.get('Comment'):
                                    await p.send_changed_order(d)
                                    print(f'{Back.LIGHTWHITE_EX}#{d.get("Ticket")}---取消订单{Back.RESET}：{d}')
                                    print(
                                        '------------------------------------------------------------------------------')
                                elif '[tp]' in d.get('Comment'):
                                    await p.send_changed_order(d)
                                    print(f'{Fore.YELLOW}{Back.RED}#{d.get("Ticket")}---止盈{Fore.RESET}{Back.RESET}：{d}')
                                    print(
                                        '------------------------------------------------------------------------------')
                                elif '[sl]' in d.get('Comment'):
                                    await p.send_changed_order(d)
                                    print(
                                        f'{Fore.YELLOW}{Back.GREEN}#{d.get("Ticket")}---止损{Fore.RESET}{Back.RESET}：{d}')
                                    print(
                                        '------------------------------------------------------------------------------')
                                else:
                                    await p.send_changed_order(d)
                                    print(f'{Back.YELLOW}#{d.get("Ticket")}---平仓{Back.RESET}：{d}')
                                    print(
                                        '------------------------------------------------------------------------------')
                except Exception as e:
                    print('推送订单失败:', e)
                    raise e
                finally:
                    conn.commit()
                    time.sleep(0.5)


def main():
    try:
        loop = ZMQEventLoop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(run_pub())
    except KeyboardInterrupt:
        print(f'{Fore.RED}发布终止{Fore.RESET}')
        time.sleep(3)


if __name__ == '__main__':
    main()
