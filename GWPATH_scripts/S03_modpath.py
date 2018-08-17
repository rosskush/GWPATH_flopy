import pandas as pd
import os
import numpy as np
import geopandas
from shapely.geometry import Point
from flopy.utils.reference import SpatialReference

# hundo = 100 X 100 grids
hundo = False
twohundotoofurious = True
halfhundo = False

#DIS
Lx = 8000. + 160.
Ly = 8000. + 160.
ztop = 150.
zbot = 0
nlay = 1
if hundo:
    nrow, ncol = 101, 101
elif twohundotoofurious:
    nrow, ncol = 201, 201
else:
    nrow,ncol = 51,51
delr, delc = int(Lx/ncol), int(Ly/nrow)
delv = (ztop - zbot) / nlay
botm = np.linspace(ztop, zbot, nlay + 1)
nper = 10 # annual for 10 years, find a way to do a steady-state period and then pipe in the values
perlen = 365.2


# make a circle!
offset = 160/2
proj4 = '+proj=aea +lat_1=27.5 +lat_2=35 +lat_0=31.25 +lon_0=-100 +x_0=1500000 +y_0=6000000 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=us-ft +no_defs'
xul, yul = 5661342.80316535942256451 - offset, 19628009.74438977241516113 + offset

yll = yul - 8000. # measure from the bottom up
well3x = 3840.
well3y = 8000.-4640. # measure from the bottom up

def PointsInCircum(xul, yll, r, n=100):
    a = [[np.cos(2*np.pi/n*i)*r,np.sin(2*np.pi/n*i)*r] for i in range(0,n+1)]
    x0 = np.array([i[0] for i in a])
    y0 = np.array([i[1] for i in a])
    return [x0+xul+well3x, y0+yll+well3y]

test = PointsInCircum(xul, yll, 50, 100)
xcirc = test[0].tolist()
ycirc = test[1].tolist()

# make a shapefile!

circle = pd.DataFrame({'x':xcirc, 'y':ycirc})
# print(circle)


circle['cirque'] = circle.apply(lambda x: Point((float(x.x), float(x.y))), axis=1)

circle = geopandas.GeoDataFrame(circle, geometry = 'cirque')
circle.to_file('starting_circle.shp', driver='ESRI Shapefile')

# get the row/column!
delcl = np.ones(nrow)*(int(Lx/ncol))
delrl = delcl
sr = SpatialReference(delr=delrl, delc=delcl, xul=xul, yul=yul)

# the shapefile grid is wrong i think, because it's -1 on both sides
row_column=sr.get_rc(xcirc, ycirc)
row=row_column[0].tolist()
column=row_column[1].tolist()

# get the local x!
for i in column:
    for j in xcirc:
        print(j)
    # s1 = column[i]*delc
    # s2 = xul + s1
    # s3 = xcirc[i] - s2
    # s4 = delc - s3
    # s5 = 1 - (s4/delc)
    # print(s5)


# get the local y!
for i,j in zip(column,xcirc):
    print(xcirc[i])
    # s1 = column[i]*delc
    # s2 = xul - s1
    # s3 = xcirc[i] - s2
    # s4 = delc + s3
    # s5 = (s4/delc)
    # print(s5)
