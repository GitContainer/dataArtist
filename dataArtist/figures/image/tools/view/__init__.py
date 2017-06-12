# coding=utf-8
from .Axes import Axes
from .TimeLine import TimeLine
from .LockView import LockView
from .Colorbar import Colorbar
# from LinkColorbar import LinkColorbar
# from LinkView import LinkView
from .Overlay import Overlay
from .Transform import Transform
from .SwitchBetweenGridAndStackedView import SwitchBetweenGridAndStackedView

color = 'blue'
show = True
tools = (LockView, Colorbar, Axes, TimeLine,
         Overlay, Transform,
         SwitchBetweenGridAndStackedView)
