#!/usr/bin/env python
# -*- coding: utf-8 -*-

from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager


def driver():
    try:
        return webdriver.Chrome(ChromeDriverManager().install())
    except:
        return None


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
