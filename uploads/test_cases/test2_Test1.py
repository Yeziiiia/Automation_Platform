# -*- encoding=utf8 -*-
__author__ = "ws"

from airtest.core.api import *
from airtest.core.settings import Settings as ST


ST.OPDELAY = 5


start_app("com.tomoviee.ai")
touch(Template(r"tpl1754622220153.png", record_pos=(0.395, -0.969), resolution=(1240, 2772)))

touch(Template(r"tpl1754622375942.png", record_pos=(-0.426, -0.953), resolution=(1240, 2772)))

touch(Template(r"tpl1754622419414.png", record_pos=(-0.233, -0.737), resolution=(1240, 2772)))

touch(Template(r"tpl1754622375942.png", record_pos=(-0.426, -0.953), resolution=(1240, 2772)))

swipe(Template(r"tpl1754634216524.png", record_pos=(0.149, -0.735), resolution=(1240, 2772)), vector=[0.0757, 0.5606])

swipe(Template(r"tpl1754634365684.png", record_pos=(0.155, 0.423), resolution=(1240, 2772)), vector=[-0.0072, -0.5189])




