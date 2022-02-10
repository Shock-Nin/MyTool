#!/usr/bin/env python
# -*- coding: utf-8 -*-

# display
from common import display
dialog = display.dialog
question = display.question
progress = display.progress
interrupt = display.interrupt

# log
from common import log
log = log.log

# matching
from common import matching
move_pos = matching.move_pos
click_pos = matching.click_pos
match = matching.match

# times
from common import times
str_time = times.str_time
get_method = times.get_method

# web
from common import web
driver = web.driver
get_tag = web.get_tag
get_text = web.get_text
