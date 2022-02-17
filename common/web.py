#!/usr/bin/env python
# -*- coding: utf-8 -*-

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager


def driver():
    return webdriver.Chrome(ChromeDriverManager().install())


def find_element(wd, name):
    try:
        return wd.find_element_by_id(name)
    except: pass
    try:
        return wd.find_element_by_name(name)
    except: pass
    try:
        return wd.find_element_by_xpath(name)
    except: pass
    try:
        return wd.find_element_by_link_text(name)
    except: pass
    try:
        return wd.find_element_by_css_selector(name)
    except: pass

    return None
