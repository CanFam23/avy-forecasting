EXP_COLS = ['time','valid_time','fxx','t','prate','sde','tp', 'sdswrf','suswrf','sdlwrf','sulwrf', 'point_id','t2m','r2','si10','wdir10','max_10si']
REQ_COLS = ['time','valid_time','fxx','point_id']

COORDS_SUBSET_FP = "../data/FAC/zones/grid_coords_subset.geojson"
COORDS_FP = "../data/FAC/zones/grid_coords.geojson"
TIFS_FP = "../data/FAC/tif"
LOC_TIFS_FP = "src/util/loc_tif.json"
SNO_FP = "data/input/sno"

SURF_REG = r":(?:TMP|SNOD|PRATE|APCP|.*WRF|RH|ASNOW):surface"
M2_REG = r":(?:TMP|RH):2 m"
WIND_REG = r":WIND|GRD:10 m above"
REGS = [SURF_REG,M2_REG,WIND_REG]