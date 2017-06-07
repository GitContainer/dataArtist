#!/usr/bin/env python
# coding=utf-8
"""start dataArtist with this module if other modules are in same
root folder but not globally installed
"""
import sys
import os

PROFILE_IMPORT_SPEED = True

if PROFILE_IMPORT_SPEED:
    import cProfile
    import pstats

    pr = cProfile.Profile()
    pr.enable()

# main directory for all code:
pkg_dir = os.path.dirname(os.path.dirname(os.path.abspath(os.curdir)))
print(os.path.abspath(os.curdir))
for s in os.listdir(pkg_dir):
    # add local code to sys.path
    f = os.path.join(pkg_dir, s)
    if os.path.isdir(f):
        print(f)
        sys.path.insert(0, f)

from dataArtist import gui

if PROFILE_IMPORT_SPEED:
    pr.disable()
    s = pstats.Stats(pr)
    s.sort_stats('tottime').print_stats(500)

gui.main()
