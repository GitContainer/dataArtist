# coding=utf-8

import lxml.html
import urllib.request  # , urllib.parse, urllib.error
import tempfile

from fancytools.os.PathStr import PathStr



def html2data(html):
    '''
    extract either tables or images from html code
    '''
    paths = []
#     data = []
    doc = lxml.html.fromstring(html)
    #images in html
    for img in doc.cssselect("img"):#doc.xpath('img'):
        # get the scr-path of the image:
        imgsrc = img.get('src')
        fname = PathStr(imgsrc).basename()
        if not hasattr(html2data, 'TMP_IMG_DIR'):
            html2data.TMP_IMG_DIR = PathStr(tempfile.mkdtemp('tmpImgDir'))
        fpath = html2data.TMP_IMG_DIR.join(fname)
        #in case img src is within HTML code:
        if not fname.filetype():
            ftype = imgsrc[imgsrc.index('image/')+6:imgsrc.index(';')]
            fpath = fpath.setFiletype(ftype)
        # download the image in a temporary folder:
        urllib.request.urlretrieve(imgsrc, fpath)
        paths.append(fpath)
        
    #TODO: doesnt work and table import from internet 
    #...is not really needed
#     # tables
#     table = _html2PyTable(doc)
#     if table:
#         data.append(table)
    return paths#, data




# def _html2PyTable(doc):
#     table = []
#     try:
#         rows = doc.cssselect("tr")
#         # TODO:
#     except:  # lxml.cccselect uses __import__ which doesnt work with pyinstaller
#         print('dynamic import error in lxml.cccselect')
#         return []
#     for row in rows:
#         table.append(list())
#         for td in row.cssselect("td"):
#             table[-1].append(str(td.text_content()))
#     return table