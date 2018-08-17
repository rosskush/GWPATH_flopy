import pandas as pd
import os
import numpy as np
import geopandas as gpd
from shapely.geometry import Point, MultiPoint
from flopy.utils.reference import SpatialReference
import flopy.utils.binaryfile as bf
import shutil
import flopy
import matplotlib.pyplot as plt
pd.set_option("display.max_rows",8)

model_ws = os.path.join('workspace')
modelname = 'test_3'

names = ['Time Point Index','Cumulative Time Step','Tracking Time','Particle ID','Particle Group','Global X','Global Y','Global Z','Grid','Layer','Row','Column','Local X','Local Y','Local Z']
names = [item.replace(' ','_') for item in names]
ts = pd.read_csv(os.path.join(model_ws,modelname+'.mp.tim_ser'),skiprows=3,names=names,delim_whitespace=True)
ts = ts.loc[ts['Tracking_Time'] <= 3652]

mf = flopy.modflow.Modflow.load(modelname+'.nam',model_ws=model_ws)

sr = mf.sr
Lx = np.sum(mf.dis.delr.array)
Ly = np.sum(mf.dis.delc.array)

def get_gamx(globalx,xul,Lx):
    gamx = xul - globalx + Lx
    dif = xul - gamx
    gamx = xul + Lx + dif
    return gamx

def get_gamy(globaly,yul,Ly):
    gamy = yul - globaly + Ly
    dif = yul - gamy
    gamy = yul + dif
    return gamy


ts['GAMX'] = sr.xul - ts['Global_X'] + Lx
ts['GAMY'] = sr.yul - ts['Global_Y']# + (ts['Global_Y'] - sr.yll)

ts['GAMX'] = ts.apply(lambda xy: get_gamx(xy['Global_X'],sr.xul,Lx),axis=1)
ts['GAMY'] = ts.apply(lambda xy: get_gamy(xy['Global_Y'],sr.yul,Ly),axis=1)

print(ts[['GAMX','GAMY']].head())

ts['geometry'] = ts.apply(lambda xy: Point(xy['GAMX'],xy['GAMY']),axis=1)

gdf = gpd.GeoDataFrame(ts,geometry='geometry')

# gdf.to_file(os.path.join('shapefiles','ending_pt.shp'))
# shutil.copy(os.path.join('grid','grid.prj'),os.path.join('shapefiles','ending_pt.prj'))

# fig, ax = plt.subplots()
# ax.scatter(ts['GAMX'],ts['GAMY'])
gdf = gdf[gdf['Tracking_Time']>=3650]
points = gdf['geometry']
point_collection = MultiPoint(list(points))
convex_hull_polygon = point_collection.convex_hull

print(convex_hull_polygon)

chDF = pd.DataFrame({'geometry':[convex_hull_polygon]})

ch = gpd.GeoDataFrame(chDF,geometry='geometry')
ch.to_file(os.path.join('shapefiles','convex.shp'))
shutil.copy(os.path.join('grid','grid.prj'),os.path.join('shapefiles','convex.prj'))


