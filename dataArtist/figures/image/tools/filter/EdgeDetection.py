from scipy.ndimage import sobel, laplace
import numpy as np

from dataArtist.widgets.Tool import Tool



class EdgeDetection(Tool):
    '''
    Execute edge detection (Sobel, Laplace)
    '''
    icon = 'edgeDetection.svg'

    def __init__(self, imageDisplay):
        Tool.__init__(self, imageDisplay)        
        pa = self.setParameterMenu() 
        self.createResultInDisplayParam(pa)

        self.pConvMethod = pa.addChild({
            'name':'Method',
            'type':'list',
            'value':'Edge gradient',
            'limits':['Edge gradient', 'Sobel-H', 
                      'Sobel-V', 'Laplace']})


    @staticmethod
    def _filter(img, method):
        if method == 'Edge gradient':
            sx = sobel(img, axis=0, mode='constant')
            sy = sobel(img, axis=1, mode='constant')
            return np.hypot(sx, sy)
        if method == 'Sobel-H':
            return sobel(img, axis=0, mode='constant')
        if method == 'Sobel-V':
            return sobel(img, axis=1, mode='constant')
        if method == 'Laplace':
            return laplace(img)
        
        
    def activate(self):  
        out = np.empty_like(self.display.widget.image)
        for n, i in enumerate(self.display.widget.image):
            out[n] = self._filter(i, self.pConvMethod.value())

        self.handleOutput(out, title='Edge filtered (sobel)')