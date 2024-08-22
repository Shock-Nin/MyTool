#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common import com
import argparse
import importlib

if __name__ == '__main__':

    # 引数受け取り
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--module')
    parser.add_argument('-e', '--event')
    args = parser.parse_args()

    class_name = args.module.split('.')[len(args.module.split('.')) - 1]
    class_name = "".join([name[0].upper() + name[1:] for name in class_name.split('_')])
    print(args)
    instance = importlib.import_module('business.' + (args.module.split('/')[0] if 'Tweet' == args.event else args.module))
    module = getattr(instance, class_name.split('/')[0])

    # メニュー系CSV読み込み
    if com.get_menu():
        if 'Tweet' == args.event:
            module(args.event).tweet()
        else:
            module(args.event).do()
