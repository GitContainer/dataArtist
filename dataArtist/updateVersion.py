'''
set __version__ in __init__.py to current date
'''
import os
import datetime

pkg_dir = os.path.abspath(os.curdir)
ff = os.path.join(pkg_dir, '__init__.py')
with open(ff, 'r') as f:
    l = f.readlines()
for i, li in enumerate(l):
    if '__version__' in li:
        new_li = "__version__ = '%s' ## date of packaging in DD.MM.YY\n" % datetime.datetime.today(
        ).strftime('%y.%m.%d')
        l[i] = new_li
        break
with open(ff, 'w') as f:
    l = f.writelines(l)
