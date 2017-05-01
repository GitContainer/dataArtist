# coding=utf-8

###
#This script needs an existing plot/image widget with at least one layer
###

print('print some information about the data of the current display:')
print('shape: %s' %str(d.l.shape))
print('maximum: %s' % d.l.max())
print('minimum: %s' % d.l.min())
print('average: %s' % np.mean(d.l))
