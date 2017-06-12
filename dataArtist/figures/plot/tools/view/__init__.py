# coding=utf-8
from __future__ import absolute_import
# from Colors import Colors
from .ErrorBar import ErrorBar
from .Legend import Legend
from .PlotStyle import PlotStyle
# from LineWidth import LineWidth
# from SymbolColor import SymbolColor
# from Symbols import Symbols
from dataArtist.figures.image.tools.view.Axes import Axes
from dataArtist.figures.image.tools.view.LockView import LockView
from dataArtist.figures.image.tools.data.Reload import Reload
from .ToImage import ToImage

# from LinkView import LinkView
from .ToTable import ToTable

color = 'blue'
show = True
tools = (Reload, LockView, Axes, Legend, PlotStyle, ErrorBar, ToImage, ToTable)
