# coding=utf-8
#from scipy.ndimage import sobel, laplace
import cv2
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
            'name': 'Method',
            'type': 'list',
            'value': 'Edge gradient',
            'limits': ['Edge gradient', 'Sobel-H',
                       'Sobel-V', 'Laplace']})
        
        self.pKsize = pa.addChild({
            'name': 'kernel size',
            'type': 'int',
            'value': 3,
            'limits': [3,15]})
        
    @staticmethod
    def _filter(img, method, k):
        if method == 'Edge gradient':
            sy = cv2.Sobel(img, ddepth=cv2.CV_64F, dx=0, dy=1, ksize=k)
            sx = cv2.Sobel(img, ddepth=cv2.CV_64F,dx=1, dy=0, ksize=k)
#             sx = sobel(img, axis=0, mode='constant')
#             sy = sobel(img, axis=1, mode='constant')
            return np.hypot(sx, sy)
        if method == 'Sobel-H':
            return cv2.Sobel(img, ddepth=cv2.CV_64F,dx=0, dy=1, ksize=k)
        #sobel(img, axis=0, mode='constant')
        if method == 'Sobel-V':
            return cv2.Sobel(img, ddepth=cv2.CV_64F,dx=1, dy=0, ksize=k)
        #sobel(img, axis=1, mode='constant')
        if method == 'Laplace':
            return cv2.Laplacian(img, ddepth=cv2.CV_64F,ksize=5)
        #laplace(img)

    def activate(self):
        out = np.empty_like(self.display.widget.image)
        for n, i in enumerate(self.display.widget.image):
            out[n] = self._filter(i, self.pConvMethod.value(), self.pKsize.value())

        self.handleOutput(out, title='Edge filtered (sobel)')
