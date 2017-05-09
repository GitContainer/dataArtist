from dataArtist.widgets.Tool import Tool


# TODO relative img Diff!!


class DifferenceImage(Tool):
    '''
    #####
    '''
    icon = 'differenceImage.svg'

    def __init__(self, display):
        Tool.__init__(self, display)

        pa = self.setParameterMenu()

        self.pSharp = pa.addChild({
            'name': 'Equalize sharpness',
            'type': 'bool',
            'value': True})

    def activate(self):

        img = self.display.widget.image
        s0, s1 = imgs.shape[1:3]
        # take 30% ROI from image center to speed up process
        rois = imgs[:, xxxx]
        comparingImgs
