import pandas as pd
import os
import numpy as np
import geopandas
from shapely.geometry import Point
from flopy.utils.reference import SpatialReference
import flopy.utils.binaryfile as bf
import shutil
import flopy
import matplotlib.pyplot as plt

# hundo = 100 X 100 grids
hundo = False
twohundotoofurious = False
halfhundo = True


model_ws = os.path.join('workspace')
modelname = 'test_3'
mf = flopy.modflow.Modflow.load(modelname+'.nam',model_ws=model_ws)
# DIS
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
    nrow, ncol = 51, 51
delr, delc = int(Lx / ncol), int(Ly / nrow)
delv = (ztop - zbot) / nlay
botm = np.linspace(ztop, zbot, nlay + 1)
nper = 10  # annual for 10 years, find a way to do a steady-state period and then pipe in the values
perlen = 365.2

# make a circle!
offset = 160 / 2
proj4 = '+proj=aea +lat_1=27.5 +lat_2=35 +lat_0=31.25 +lon_0=-100 +x_0=1500000 +y_0=6000000 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=us-ft +no_defs'
xul, yul = 5661342.80316535942256451 - offset, 19628009.74438977241516113 + offset

# get the row/column!
delcl = np.ones(nrow) * (int(Lx / ncol))
delrl = delcl
sr = SpatialReference(delr=delrl, delc=delcl, xul=xul, yul=yul)

yll = yul - 8000.  # measure from the bottom up
well3x = 3840. + offset
well3y = 8000. - 4640. - offset  # measure from the bottom up


def PointsInCircum(xul, yll, r, n=100):
    a = [[np.cos(2 * np.pi / n * i) * r, np.sin(2 * np.pi / n * i) * r] for i in range(0, n)]
    x0 = np.array([i[0] for i in a])
    y0 = np.array([i[1] for i in a])
    return [x0 + xul + well3x, y0 + yll + well3y]


test = PointsInCircum(xul, yll, 50, 100)
xcirc = test[0].tolist()
ycirc = test[1].tolist()

# make a shapefile!

circle = pd.DataFrame({'x': xcirc, 'y': ycirc})
# get model coordinates
circle['ModelX'] = circle['x'] - xul
circle['ModelY'] = yul - circle['y']
rows, cols = sr.get_rc(circle['x'].tolist(), circle['y'].tolist())
circle['Row'], circle['Column'] = rows, cols



# todo get the local coordinates
def calc_local_x(delr, col, x):
    temp_x = delr * (col)
    val = x - temp_x
    localX = val / delr
    return localX

def calc_local_y(delc, row, y, nrow):
    temp_y = delc * (row)
    val = temp_y - y
    localY = 1+(val / delc)
    return localY


circle['LocalX'] = circle.apply(lambda xy: calc_local_x(delr, xy['Column'], xy['ModelX']), axis=1)
circle['LocalY'] = circle.apply(lambda xy: calc_local_y(delc, xy['Row'], xy['ModelY'],nrow), axis=1)

# print(circle)


circle['cirque'] = circle.apply(lambda x: Point((float(x.x), float(x.y))), axis=1)
circle = geopandas.GeoDataFrame(circle, geometry='cirque')
proj4 = '+proj=aea +lat_1=27.5 +lat_2=35 +lat_0=31.25 +lon_0=-100 +x_0=1500000 +y_0=6000000 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=us-ft +no_defs'
circle.to_file(os.path.join('shapefiles', 'starting_circle.shp'), driver='ESRI Shapefile')
shutil.copy(os.path.join('grid', 'grid.prj'), os.path.join('shapefiles', 'starting_circle.prj'))


# back to normal pandas
df = pd.DataFrame(circle)
df['ParticleID'] = np.arange(1,len(df)+1)
df['GroupNumber'] = 1
df['Grid'] = 1
df['Layer'] = 1
df['LocalZ'] = .5
df['ReleaseTime'] = 0
df['Label'] = 'GP01'
df['Row'] += 1 # for writing starting loc
df['Column'] += 1
df = df[['ParticleID', 'GroupNumber', 'Grid', 'Layer', 'Row', 'Column', 'LocalX', 'LocalY', 'LocalZ', 'ReleaseTime','Label', 'x', 'y']]
df.to_csv(os.path.join(model_ws,'starting_locs.csv'), index=False)

def write_loc_file(file_nam,starting_csv,strt_time=0,input_style=1):
    df = pd.read_csv(starting_csv)
    columns = ['ParticleID', 'GroupNumber', 'Grid', 'Layer', 'Row', 'Column', 'LocalX', 'LocalY', 'LocalZ',
             'ReleaseTime', 'Label']
    grps = df['GroupNumber'].unique().tolist()

    # print(grps)
    file = open(file_nam,'w')
    file.write(f'1\n{len(grps)}\n')
    for grp in grps:
        tempDF = df[df['GroupNumber'] == grp]
        grp_nam = tempDF.iloc[0]['Label']
        file.write(f'{grp_nam}'+'\n')
        file.write(f'{len(tempDF)}\n')
    for grp in grps:
        tempDF = df[df['GroupNumber'] == grp]
        grp_nam = tempDF.iloc[0]['Label']
        for z in range(len(tempDF)):
            for j in columns:
                file.write(f'{tempDF.iloc[z][j]}  ')
            file.write('\n')

starting_loc = os.path.join(model_ws,'starting_pts.loc')

write_loc_file(starting_loc,starting_csv=os.path.join(model_ws,'starting_locs.csv'))

mp6_exe = os.path.join('gw_codes','mp6.exe')

mp = flopy.modpath.Modpath('test_3',exe_name=mp6_exe,modflowmodel=mf,model_ws=model_ws,dis_file = mf.name+'.dis',head_file=mf.name+'.hds',budget_file=mf.name+'.cbc')
mp_ibound = mf.bas6.ibound.array # use ibound from modflow model
mpb = flopy.modpath.ModpathBas(mp,-1e30,ibound=mp_ibound,prsity =.25) # make modpath bas object

sim = mp.create_mpsim(trackdir='backward', simtype='pathline', packages='starting_pts.loc',
                      start_time=(0, 0, 0))  # create simulation file

mp.write_input()
mp.run_model(silent=False)

cbb = bf.CellBudgetFile(os.path.join(model_ws,modelname+'.cbc'))


pthobj = flopy.utils.PathlineFile(os.path.join(model_ws,'test_3.mppth')) # create pathline object
epdobj = flopy.utils.EndpointFile(os.path.join(model_ws,'test_3.mpend')) # create endpoint object

fig, ax = plt.subplots()

hds = bf.HeadFile(os.path.join(model_ws,modelname+'.hds'))
times = hds.get_times()
head = hds.get_data(totim=times[-1])
levels = np.linspace(0, 10, 11)

frf = cbb.get_data(text='FLOW RIGHT FACE', totim=times[-1])[0]
fff = cbb.get_data(text='FLOW FRONT FACE', totim=times[-1])[0]

modelmap = flopy.plot.ModelMap(model=mf, layer=0)
qm = modelmap.plot_ibound()
lc = modelmap.plot_grid()

quiver = modelmap.plot_discharge(frf, fff, head=head)

well_epd = epdobj.get_alldata()
well_pathlines = pthobj.get_alldata()

print(times)

modelmap.plot_pathline(well_pathlines, travel_time='< 3652', layer='all', colors='red') # plot pathline <= time
modelmap.plot_endpoint(well_epd, direction='starting', colorbar=False) # can only plot starting of ending, not as dynamic as pathlines
modelmap.plot_bc('wel',color='k')

plt.show()
