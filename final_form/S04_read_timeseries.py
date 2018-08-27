import pandas as pd
import os
import numpy as np
import geopandas as gpd
from shapely.geometry import Point, MultiPoint, LineString, Polygon,MultiPolygon
from flopy.utils.reference import SpatialReference
import flopy.utils.binaryfile as bf
import shutil
import flopy

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
ts['GAMY'] = sr.yul - ts['Global_Y']

ts['GAMX'] = ts.apply(lambda xy: get_gamx(xy['Global_X'],sr.xul,Lx),axis=1)
ts['GAMY'] = ts.apply(lambda xy: get_gamy(xy['Global_Y'],sr.yul,Ly),axis=1)


ts['geometry'] = ts.apply(lambda xy: Point(xy['GAMX'],xy['GAMY']),axis=1)

gdf = gpd.GeoDataFrame(ts,geometry='geometry')
gdf = gdf[gdf['Tracking_Time']>=3650] # get 10 years
points = gdf['geometry']
point_collection = MultiPoint(list(points))

# make a polygon using the points after 10 years
df2 = pd.DataFrame({'geometry':points,'end':'end_pt'})
df2['geometry'] = df2['geometry'].apply(lambda x:x.coords[0])
df2.reset_index(inplace=True,drop=True)
df2 = df2.groupby(['end'])['geometry'].apply(lambda x: Polygon(x.tolist()))
gdf2 = gpd.GeoDataFrame(df2,geometry='geometry')

outputs = os.path.join('outputs')
if not os.path.exists(outputs): os.mkdir(outputs)
shapefiles = os.path.join('outputs','shapefiles')
if not os.path.exists(shapefiles): os.mkdir(shapefiles)

gdf2.to_file(os.path.join(shapefiles,'mp6_10_yrs_poly.shp'))
shutil.copy(os.path.join('texas_gam.prj'),os.path.join(shapefiles,'mp6_10_yrs_poly.prj'))
