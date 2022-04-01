#!/usr/bin/env python
# -*- coding: utf-8 -*-

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


def driver(headless=False):
    options = Options()
    options.add_argument('--headless')

    wd = None
    try:
        if headless:
            wd = webdriver.Chrome(ChromeDriverManager().install(), options=options)
        else:
            wd = webdriver.Chrome(ChromeDriverManager().install())
    except: pass

    wd.implicitly_wait(5)
    return wd


def find_element(wd, element):
    try:
        return wd.find_element(By.ID, element)
    except: pass
    try:
        return wd.find_element(By.NAME, element)
    except: pass
    try:
        return wd.find_element(By.XPATH, element)
    except: pass
    try:
        return wd.find_element(By.LINK_TEXT, element)
    except: pass
    try:
        return wd.find_element(By.CSS_SELECTOR, element)
    except: pass

    return None
