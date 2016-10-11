#!/usr/bin/env python
# coding=utf-8
"""
run dataArist from taskbar
"""

import sys
from dataArtist import gui

sys.argv.append('-s')

gui.main()
