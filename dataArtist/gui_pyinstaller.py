'''
Created on 2 Oct 2016

@author: elkb4
'''
import ctypes
import os
import sys


# this is a temporary workaround around the following error:
# MKL FATAL ERROR: cannot load neither mkl_vml_def.dll nor mkl_vml_avx2.dll
# which occurs on win7, pyinstaller v3.2 and anaconda v3


# see
# https://github.com/pyinstaller/pyinstaller/issues/844#issuecomment-189182894
if getattr(sys, 'frozen', False):
    # Override dll search path.
    ctypes.windll.kernel32.SetDllDirectoryW(
        'C:/Users/ngj/AppData/Local/Continuum/Anaconda3/Library/bin/')
    # Init code to load external dll
    ctypes.CDLL('mkl_avx2.dll')
    ctypes.CDLL('mkl_def.dll')
    ctypes.CDLL('mkl_vml_avx2.dll')
    ctypes.CDLL('mkl_vml_def.dll')

    # Restore dll search path.
    ctypes.windll.kernel32.SetDllDirectoryW(sys._MEIPASS)


from dataArtist import gui
gui.main()
