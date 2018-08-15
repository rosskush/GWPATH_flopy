import flopy
import numpy as np
import matplotlib.pyplot as plt
import flopy.utils.binaryfile as bf
import os
import geopandas as gpd
import shutil

modelname = 'test_3'
exe = os.path.join('gw_codes','mf2k-chprc08spl.exe')
model_ws = os.path.join('workspace')
mf = flopy.modflow.Modflow(modelname, version='mf2k', exe_name =exe,model_ws=model_ws)

proj4 = '+proj=aea +lat_1=27.5 +lat_2=35 +lat_0=31.25 +lon_0=-100 +x_0=1500000 +y_0=6000000 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=us-ft +no_defs'
xul, yul = 5661342.80316535942256451, 19628009.74438977241516113


#DIS
Lx = 8000.
Ly = 8000.
ztop = 150.
zbot = 0
nlay = 1
nrow, ncol = 100, 100
delr, delc = int(Lx/ncol), int(Ly/nrow)
delv = (ztop - zbot) / nlay
botm = np.linspace(ztop, zbot, nlay + 1)
nper = 10 # annual for 10 years, find a way to do a steady-state period and then pipe in the values
perlen = 365.2

dis = flopy.modflow.ModflowDis(mf, nlay, nrow, ncol, delr=delr, delc=delc, top=ztop, botm=botm[1:],nper=nper,perlen=perlen,xul=xul,yul=yul,proj4_str=proj4,lenuni=1)

#BAS

# linear stepdown
south_to_north = np.linspace(100,60,nrow)
print(south_to_north.shape)

# exit()

ibound = np.ones((nlay, nrow, ncol), dtype=np.int32)
ibound[:, 0, :] = -1
ibound[:, -1, :] = -1
ibound[:, :, 0] = -1
ibound[:, :, -1] = -1
strt = np.ones((nlay, nrow, ncol), dtype=np.float32)*ztop
strt[:, :, :] = 100
strt[:, 0, :] = 100.
strt[:, -1, :] = 60.
for i in range(ncol-1):
    strt[:, :, i] = south_to_north
strt[:, :, 0] = south_to_north
strt[:, :, -1] = south_to_north

fig, ax = plt.subplots()
plt.imshow(strt[0])
plt.colorbar()

bas = flopy.modflow.ModflowBas(mf, ibound=ibound, strt=strt)
bas.export(os.path.join('grid','bas.shp'))
shutil.copy(os.path.join('grid','grid.prj'),os.path.join('grid','bas.prj'))
#LPF change hydraulic conductivity here
gdf = gpd.read_file(os.path.join('grid_hk','grid_hk.shp'))
hk_array = np.ones((nlay, nrow, ncol), dtype=np.int32)
for i in range(len(gdf)):
    r = gdf.iloc[i]['row']
    c = gdf.iloc[i]['column']
    val = gdf.iloc[i]['Hk']
    hk_array[0][r-1, c-1] = val
print(hk_array)
lpf = flopy.modflow.ModflowLpf(mf, hk=hk_array, vka=hk_array, ipakcb=53)

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
wel1 = [0, 9*2, 14*2, -38500]
wel2 = [0, 17*2, 39*2,  -77000]
wel3 = [0, 28*2, 23*2,  -96250]
wel4 = [0, 41*2, 17*2,  -57750]
wells = []
wells2 = wells.append(wel1)
wells2 = wells.append(wel2)
wells2 = wells.append(wel3)
wells2 = wells.append(wel4)
wel_spd = {0: wells, 1: wells, 2: wells, 3: wells, 4: wells, 5: wells, 6: wells, 7: wells,
           8: wells, 9: wells}
wel = flopy.modflow.ModflowWel(mf,stress_period_data=wel_spd,ipakcb=53)
wel.export(os.path.join('grid','wel.shp'))
shutil.copy(os.path.join('grid','grid.prj'),os.path.join('grid','wel.prj'))

#write the modflow input files
mf.write_input()

# Run the MODFLOW model
success, buff = mf.run_model(silent=False)


mf.plot()


plt.show()