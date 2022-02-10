#!/usr/bin/env python
# -*- coding: utf-8 -*-

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager


def driver():
    return webdriver.Chrome(ChromeDriverManager().install())


def get_tag():
    pass


def get_text():
    pass
