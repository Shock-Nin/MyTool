#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

from common import com
from const import cst
import chromedriver_binary
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


def driver(headless=False):
    options = Options()
    options.add_argument('--headless')
    # options.add_argument('--no-sandbox')

    wd = None
    try:
        if headless:
            wd = webdriver.Chrome(ChromeDriverManager().install(), options=options)
        else:
            wd = webdriver.Chrome(ChromeDriverManager().install())
    except:
        com.log('Change WebDriver local')
        path = os.getcwd() + '/item/setting/' + (
            'Windows/chromedriver.exe' if 'Win' == cst.PC else 'mac/chromedriver')
        try:
            if headless:
                wd = webdriver.Chrome(path, options=options)
            else:
                wd = webdriver.Chrome(path)
        except:
            com.log('Change WebDriver Binary')
            try:
                if headless:
                    wd = webdriver.Chrome(options=options)
                else:
                    wd = webdriver.Chrome()
            except Exception as e:
                com.log('WebDriver local error: ' + str(e))

    if wd is not None:
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

def select_click(element, index):
    select = Select(element)
    select.select_by_index(index)
