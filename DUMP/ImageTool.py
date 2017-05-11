# coding=utf-8
from dataArtist.widgets.Tool import Tool


# TODO: is this extra image tool actually needed?
class ImageTool(Tool):

    def getDataOrFilenames(self):
        data = self.display.widget.getData()
        if data is None:
            return self.display.filenames
        return data
