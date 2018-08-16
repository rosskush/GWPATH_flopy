import os
import shutil
import geopandas as gpd

#files = os.listdir()

#files = [item for item in files if item.startswith('grid_hk')]

#for file in files:
#    shutil.copy(file,file.replace('grid_hk','grid_hk_50'))

gdf = gpd.read_file('grid_hk.shp')

gdf['hk'] = gdf['Hk']

del gdf['Hk']

gdf.to_file('grid_hk_50.shp')




