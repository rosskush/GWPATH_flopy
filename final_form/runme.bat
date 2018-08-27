# create a modflow model and store it in \workspace
python S01_make_model_grid.py

# run modflow model in flopy
python S02_flopy_make.py

#run modpath model
python S03_modpath.py

# create convexhull shapefile for 10 years
python S04_read_timeseries.py

# create stats table comparing  10 year capture zones
python S05_compare_capturezones.py