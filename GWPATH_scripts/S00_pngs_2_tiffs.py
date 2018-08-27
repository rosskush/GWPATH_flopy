import rasterio
import os
import matplotlib.pyplot as plt
import geopandas as gpd
import imageio
import numpy as np

png_ws = os.path.join('gwpath_images')

tiff_ws = os.path.join('gwpath_rasters')

gdf = gpd.read_file(os.path.join(tiff_ws,'starting_location.shp'))
print(gdf.crs)

pngs = os.listdir(png_ws)
pngs = [item for item in pngs if item.endswith('.PNG')] # make sure the files are pngs
print(pngs)

proj4 = '+proj=aea +lat_1=27.5 +lat_2=35 +lat_0=31.25 +lon_0=-100 +x_0=1500000 +y_0=6000000 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=us-ft +no_defs'
xul, yul = 5661342.80316535942256451, 19628009.74438977241516113

for png in pngs:
    tiff = png.replace('.PNG','.tif')
    arr = np.array(imageio.imread(os.path.join(png_ws,png)))
    nrow, ncol, bands = arr.shape
    transform = rasterio.transform.from_bounds(xul,yul-8000,xul+8000,yul,width=ncol, height=nrow)
    print(transform)
    new_dataset = rasterio.open(os.path.join(tiff_ws,tiff), 'w', driver='GTiff',
                                height = arr.shape[0], width = arr.shape[1],
                                count=1, crs=proj4,dtype=(arr.dtype),
                                transform=transform)
    new_dataset.write(arr[:,:,0],1)
    new_dataset.close()


