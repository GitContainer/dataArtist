from __future__ import absolute_import
from .Axes import Axes
from .TimeLine import TimeLine
from .LockView import LockView
from .Colorbar import Colorbar
# from LinkColorbar import LinkColorbar
# from LinkView import LinkView
from .Overlay import Overlay
from .Transform import Transform
from .IsColor import IsColor
from .SwitchBetweenGridAndStackedView import SwitchBetweenGridAndStackedView
from .ToPlot import ToPlot
color = 'blue'
show = True
tools = (LockView, Colorbar, Axes, TimeLine,
         Transform, IsColor, Overlay,
         SwitchBetweenGridAndStackedView, ToPlot)
