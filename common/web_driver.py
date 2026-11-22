#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

from common import com
from const import cst
# import chromedriver_binary
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, WebDriverException, InvalidSelectorException
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
    except (WebDriverException, Exception) as e:
        com.log(f'WebDriver初期化エラー（リトライ中）: {str(e)}', 'W')
        try:
            if headless:
                wd = webdriver.Chrome(options=options)
            else:
                wd = webdriver.Chrome(options=None)
        except Exception as e:
            com.log('WebDriver error: ' + str(e), 'E')

    if wd is not None:
        wd.implicitly_wait(5)

    return wd


def find_element(wd, element):
    """
    複数の方法で要素を検索
    XPATHの場合は直接XPATH、それ以外はID, NAME, XPATH, LINK_TEXT, CSS_SELECTORの順に試行
    """
    # XPathの場合は直接XPathで検索
    if element.startswith('/') or element.startswith('('):
        try:
            return wd.find_element(By.XPATH, element)
        except NoSuchElementException:
            com.log(f'要素が見つかりませんでした: {element}', 'W')
            return None

    try:
        return wd.find_element(By.ID, element)
    except (NoSuchElementException, InvalidSelectorException):
        pass
    try:
        return wd.find_element(By.NAME, element)
    except (NoSuchElementException, InvalidSelectorException):
        pass
    try:
        return wd.find_element(By.XPATH, element)
    except (NoSuchElementException, InvalidSelectorException):
        pass
    try:
        return wd.find_element(By.LINK_TEXT, element)
    except (NoSuchElementException, InvalidSelectorException):
        pass
    try:
        return wd.find_element(By.CSS_SELECTOR, element)
    except (NoSuchElementException, InvalidSelectorException):
        pass

    com.log(f'要素が見つかりませんでした: {element}', 'W')
    return None

def select_click(element, index):
    select = Select(element)
    select.select_by_index(index)
