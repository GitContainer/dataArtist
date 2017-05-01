from .CorrectCamera import CorrectCamera
from .PerspectiveImageStitching import PerspectiveImageStitching
from .PerspectiveCorrection import PerspectiveCorrection
from .ScaleIntensity import ScaleIntensity
from .InPlaneImageStitching import InPlaneImageStitching


tools = (CorrectCamera, PerspectiveCorrection,
         PerspectiveImageStitching, ScaleIntensity, InPlaneImageStitching)
# position='right'
secondRow = True
color = 'red'
show = {'simple': False, 'advanced': True}
