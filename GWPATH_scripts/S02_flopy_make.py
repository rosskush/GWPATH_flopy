import flopy
import numpy as np
import matplotlib.pyplot as plt
import flopy.utils.binaryfile as bf
import os

modelname = 'test_3'
exe = os.path.join('gw_codes','mf2k-chprc08spl.exe')
model_ws = os.path.join('workspace')
mf = flopy.modflow.Modflow(modelname, version='mf2k', exe_name =exe,model_ws=model_ws)

#DIS
Lx = 8000.
Ly = 8000.
ztop = 150.
zbot = 0
nlay = 1
nrow = 50
ncol = 50
delr = Lx/ncol
delc = Ly/nrow
delv = (ztop - zbot) / nlay
botm = np.linspace(ztop, zbot, nlay + 1)
nper = 10 # annual for 10 years, find a way to do a steady-state period and then pipe in the values
perlen = 365.2

#BAS
ibound = np.ones((nlay, nrow, ncol), dtype=np.int32)
ibound[:, 0, :] = -1
ibound[:, -1, :] = -1
strt = np.ones((nlay, nrow, ncol), dtype=np.float32)
strt[:, 0, :] = 100.
strt[:, -1, :] = 60
bas = flopy.modflow.ModflowBas(mf, ibound=ibound, strt=strt)

#LPF change hydraulic conductivity here
# how to point to the external grid values?
# lpf = flopy.modflow.ModflowLpf(mf, hk=10, vka=10., ipakcb=53)

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
wel1 = [1, 15, 10, 38500]
wel2 = [1, 40, 18, 77000]
wel3 = [1, 24, 29, 96250]
wel4 = [1, 18, 42, 57750]