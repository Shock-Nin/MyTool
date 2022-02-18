#!/usr/bin/env python
# -*- coding: utf-8 -*-

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager


def driver():
    return webdriver.Chrome(ChromeDriverManager().install())


def find_element(wd, element):
    try:
        return wd.find_element_by_id(element)
    except: pass
    try:
        return wd.find_element_by_name(element)
    except: pass
    try:
        return wd.find_element_by_xpath(element)
    except: pass
    try:
        return wd.find_element_by_link_text(element)
    except: pass
    try:
        return wd.find_element_by_css_selector(element)
    except: pass

    return None
