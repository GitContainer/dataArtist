#!/usr/bin/env python
# coding=utf-8
"""
run dataArist from taskbar
"""

DATARTIST_IS_INSTALLED = False

import sys
sys.argv.append('-s')

if DATARTIST_IS_INSTALLED:
    import gui
    gui.main()
else:
    import gui_noInstall
