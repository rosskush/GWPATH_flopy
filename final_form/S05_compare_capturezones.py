import os
import geopandas as gpd
import pandas as pd



mp6_shp = gpd.read_file(os.path.join('outputs','shapefiles','mp6_10_yrs_poly.shp'))
mp6_area = mp6_shp.iloc[0].geometry.area

for row in pd.DataFrame(mp6_shp.bounds).iterrows():
	index, data = row
	minx6, miny6, maxx6, maxy6 = data
print(minx6, miny6, maxx6, maxy6)
# 


gwpath_shp = gpd.read_file(os.path.join('gwpath_digitized','fig_21_10_yr_capture_zone.shp'))
gwpath_shp.geometry = gwpath_shp.geometry.to_crs(mp6_shp.crs)

gwpath_area = gwpath_shp.iloc[0].geometry.area
for row in pd.DataFrame(gwpath_shp.bounds).iterrows():
	index, data = row
	gw_minx, gw_miny, gw_maxx, gw_maxy = data
# print(minx6, miny6, maxx6, maxy6)

columns = ['Case','Area_sqft','Area_acre','Left_extent','Lower_extent','Right_extent','Upper_extent']

data = {'Case' : ['GWpath','Modpath6'],'Area_sqft':[gwpath_area, mp6_area],'Area_acre':[gwpath_area*2.2957e-5, mp6_area*2.2957e-5],'Left_extent':[gw_minx,minx6],'Lower_extent':[gw_miny,miny6],'Right_extent':[gw_maxx,maxx6],'Upper_extent':[gw_maxy,maxy6]}
df = pd.DataFrame(data)

df.to_csv(os.path.join('outputs','well_capture_stats.csv'),index=False)





