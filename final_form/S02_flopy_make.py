import flopy
import numpy as np
import matplotlib.pyplot as plt
import flopy.utils.binaryfile as bf
import os
import geopandas as gpd
import shutil

modelname = 'test_3'
exe = os.path.join('..','gw_codes','mf2k-chprc08spl.exe')
model_ws = os.path.join('workspace')
if not os.path.exists(model_ws): os.mkdir(model_ws)

outputs = os.path.join('outputs')
if not os.path.exists(outputs): os.mkdir(outputs)

shapefiles = os.path.join('outputs','shapefiles')
if not os.path.exists(shapefiles): os.mkdir(shapefiles)

mf = flopy.modflow.Modflow(modelname, version='mf2k', exe_name =exe,model_ws=model_ws)

offset = 160/2
proj4 = '+proj=aea +lat_1=27.5 +lat_2=35 +lat_0=31.25 +lon_0=-100 +x_0=1500000 +y_0=6000000 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=us-ft +no_defs'
xul, yul = 5661342.80316535942256451 - offset, 19628009.74438977241516113 + offset

#DIS
Lx = 8000. + 160
Ly = 8000. + 160
ztop = 150.
zbot = 0
nlay = 1

nrow,ncol = 51,51

delr, delc = int(Lx/ncol), int(Ly/nrow)
delv = (ztop - zbot) / nlay
botm = np.linspace(ztop, zbot, nlay + 1)
nper = 10 # annual for 10 years, find a way to do a steady-state period and then pipe in the values
perlen = 365.25

dis = flopy.modflow.ModflowDis(mf, nlay, nrow, ncol, delr=delr, delc=delc, top=ztop, botm=botm[1:],nper=nper,perlen=perlen,xul=xul,yul=yul,proj4_str=proj4,lenuni=1)

mf.sr = flopy.utils.reference.SpatialReference(delr=dis.delr.array,delc=dis.delc.array,lenuni=1,xul=xul,yul=yul,proj4_str=proj4,prj=os.path.join('texas_gam.prj'))

#BAS

# linear stepdown for starting heads and constant head boundries 
south_to_north = np.linspace(100,60,nrow)

ibound = np.ones((nlay, nrow, ncol), dtype=np.int32)
ibound[:, 0, :] = -1
ibound[:, -1, :] = -1

strt = np.ones((nlay, nrow, ncol), dtype=np.float32)*ztop
strt[:, :, :] = 100
strt[:, 0, :] = 100.
strt[:, -1, :] = 60.
for i in range(ncol-1):
    strt[:, :, i] = south_to_north
strt[:, :, 0] = south_to_north
strt[:, :, -1] = south_to_north


bas = flopy.modflow.ModflowBas(mf, ibound=ibound, strt=strt)


# use starting heads to create constant head boundries along the left and right columns
chd_spd = {}
spd = []
for row in range(nrow):
    stage = strt[0][row,0]
    spd.append([0,row,0,stage,stage])
    spd.append([0,row,ncol-1,stage,stage])

chd_spd[0] = spd
chd = flopy.modflow.ModflowChd(mf,stress_period_data=chd_spd,ipakcb=53)

#LPF change hydraulic conductivity here
hk_gdf = gpd.read_file(os.path.join('gwpath_digitized','fig_20_block_hk_polygon.shp'))
grid_gdf = gpd.read_file(os.path.join(shapefiles,f'grid_offset_{nrow}.shp'))

gdf = gpd.sjoin(hk_gdf,grid_gdf) # spatial join for the win

hk_array = np.ones((nlay, nrow, ncol), dtype=np.int32)
for i in range(len(gdf)):
    r = gdf.iloc[i]['row']
    c = gdf.iloc[i]['column']
    val = gdf.iloc[i]['Hk']
    hk_array[0][r-1, c-1] = val
hk_array[0][:,0] = hk_array[0][:,1]
hk_array[0][0,:] = hk_array[0][1,:]

# print(hk_array)
lpf = flopy.modflow.ModflowLpf(mf, hk=hk_array, vka=hk_array, ipakcb=53)
lpf.hk.plot()
#OC
spd = {}
for sp in range(nper):
    spd[(sp, 0)] = ['print head', 'print budget', 'save head', 'save budget']
oc = flopy.modflow.ModflowOc(mf, stress_period_data=spd, compact=True)

pcg = flopy.modflow.ModflowPcg(mf)


# WEL
# well 1: 2400, 1600, 200 gpm
# well 2: 6400, 2880, 400 gpm
# well 3: 3840, 4640, 500 gpm
# well 4: 2880, 6720, 300 gpm
# 1 gpm = 192.5 ft**3 per day

gpm2cfd = 192.5


wel1 = [0, 9+1, 14+1, -200*gpm2cfd]
wel2 = [0, 17+1, 39+1,  -400*gpm2cfd]
wel3 = [0, 28+1, 23+1,  -500*gpm2cfd]
wel4 = [0, 41+1, 17+1,  -300*gpm2cfd]

wells = [wel1,wel2,wel3,wel4]

wel_spd = {0: wells, 1: wells, 2: wells, 3: wells, 4: wells, 5: wells, 6: wells, 7: wells,
           8: wells, 9: wells}
wel = flopy.modflow.ModflowWel(mf,stress_period_data=wel_spd,ipakcb=53)

#write the modflow input files
mf.write_input()

# Run the MODFLOW model
success, buff = mf.run_model(silent=False)

cbbobj = bf.CellBudgetFile(os.path.join(model_ws,modelname+'.cbc'))
# print(cbbobj.get_)

# create contour shapefile
headobj = bf.HeadFile(os.path.join(model_ws,modelname+'.hds'))
times = headobj.get_times()
head = headobj.get_data(totim=times[-1])

levels = np.arange(45,100,5)
extent = [xul,xul+Lx,yul-Ly,yul]

fig, ax = plt.subplots(figsize=(8,8))
plt.imshow(head[0],extent=extent,cmap='jet')
plt.colorbar()
plt.title('Head after 10 years (ft)'.title())
contour = plt.contour(np.flipud(head[0]),levels,extent=extent)

plt.clabel(contour, inline=1, fontsize=10,fmt='%1.0f',colors='k')



fig.tight_layout()
fig.savefig(os.path.join(outputs,'contour_head.png'))



head_shp = os.path.join(shapefiles,'head_contour.shp')
mf.sr.export_contours(head_shp,contour,prj=os.path.join('texas_gam.prj'),xul=xul,yul=yul)

plt.close('all')