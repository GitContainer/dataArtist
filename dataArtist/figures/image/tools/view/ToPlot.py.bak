import numpy as np
from dataArtist.widgets.Tool import Tool
 

class ToPlot(Tool):
    '''
    Show the content of this image as mutliple plots
    '''
    icon = 'toPlot.svg'
    reinit = True
    
    def __init__(self, imageDisplay):
        Tool.__init__(self, imageDisplay)


    def activate(self):
        d = self.display
        _,s1,s2 = d.widget.image.shape
        
        x = np.arange(s1)
        names = [ str(val) for val in xrange(s2) ]
        
        for n, im in enumerate(d.widget.image):
            vals = [(x,im[:,i]) for i in xrange(s2)]
            
            d = self.display.workspace.addDisplay(
                axes=2,
                names=names,
                data=vals, 
                title='Plot view of image %s for display (%s)' %(n, d.number))

            
