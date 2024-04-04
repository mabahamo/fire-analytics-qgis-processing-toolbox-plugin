#!python3
"""
POLYGON TREATMENT SENSIBLE INSTANCE GENERATOR

Inputs:
1. Config dictionary (num_treatments and ranges for values and costs)

Outputs: A feasible instance
1. Current status in "current_treatment.tif" and "current_value.tif"
2. Possible treatments in
3. treatment names, total area and budget in params.txt

USAGE: RUN IN THE QGIS PYTHON CONSOLE
- overwrites existing tif rasters and csv.files(check last line for the path)
- then solve using the polygon treatment algorithm
"""
from os import getcwd

import string

import numpy as np

np.set_printoptions(precision=2)  # , formatter={'float_kind': '{: 0.2f}'.format})

# config = {
values = [1000, 2000]
costs = [100, 200]
px_area = 10
W = 90
H = 60
TR = 7
nodata = -1
# }

# treatments are random three letter words
treat_names = ["".join(np.random.choice(list(string.ascii_lowercase), 3)) for _ in range(TR)]

# helper for putting random no data values
rnd_idx = lambda: (np.random.choice(range(H)), np.random.choice(range(W)))
rnd_idxs = lambda n: [(np.random.choice(range(H)), np.random.choice(range(W))) for _ in range(n)]
nodata_idx = []

# current
current_treatment = np.random.choice(range(TR), (H, W))
current_value = np.random.uniform(*values, size=(H, W))


# put in a random index a nodata value
current_value[rnd_idx()] = nodata
nodata_idx += list(zip(*np.where(current_value == nodata)))
current_treatment[rnd_idx()] = nodata
nodata_idx += list(zip(*np.where(current_treatment == nodata)))

# treatment costs
treat_cost = np.random.uniform(*costs, size=(TR, TR))
treat_cost[np.eye(TR, dtype=bool)] = 0

# treatment value
target_value = np.random.uniform(*values, size=(TR, H, W))
# put nodata wherever current_treatment
target_value[current_treatment == np.arange(TR)[:, None, None]] = nodata
target_value

# view
print(f"{W=}, {H=}, {TR=}")
print(f"{treat_names=}")
print(f"{current_treatment=}, {current_treatment.shape=}")
print("current_treatment\n", np.vectorize(lambda tr: treat_names[tr])(current_treatment))
print(f"{current_value=}, {current_value.shape=}")
print(f"{treat_cost=}, {treat_cost.shape=}")

# assert each pixel has a valid treatment
assert np.all(np.any(target_value[:, w, h] != nodata) for w in range(W) for h in range(H))

# for each pixel (h, w), get the indexes of valid treatments
tr, hh, ww = np.where(target_value != nodata)
feasible_set = {(h, w, t) for t, h, w in zip(tr, hh, ww)}
feasible_ratio = len(feasible_set) / (W * H * TR)
print(f"{feasible_ratio=: 0.2f}")

area = feasible_ratio * 0.618 * (W * H * TR) * px_area
print(f"{area=: 0.2f}")

budget = treat_cost[treat_cost != 0].mean() * area
print(f"{budget=: 0.2f}")

#
# write files
with open("raster_params.txt", "w") as params_file:
    params_file.write(f"{treat_names=}\n")
    params_file.write(f"{area=}\n")
    params_file.write(f"{budget=}\n")
# treat matrix
from pandas import DataFrame

DataFrame(treat_cost, index=treat_names, columns=treat_names).to_csv("raster_treatment_costs.csv", float_format="%.6f")

# rasters to tifs
from osgeo.gdal import GDT_Float32, GDT_Int16, GetDriverByName, UseExceptions

UseExceptions()

for name, data, dtype in zip(
    ["current_treatment", "current_value"], [current_treatment, current_value], [GDT_Int16, GDT_Float32]
):
    ds = GetDriverByName("GTiff").Create(name + ".tif", W, H, 1, dtype)
    ds.SetGeoTransform((0, px_area, 0, 0, 0, px_area))  # specify coords
    # ds.SetProjection(base_raster.crs().authid())  # export coords to file
    band = ds.GetRasterBand(1)
    band.SetUnitType(name)
    if 0 != band.SetNoDataValue(nodata):
        feedback.pushWarning(f"Set No Data failed for {name}")
    if 0 != band.WriteArray(data):
        feedback.pushWarning(f"WriteArray failed for {name}")
    ds.FlushCache()  # write to disk
    ds = None

name = "target_value"
data = target_value
dtype = GDT_Float32
ds = GetDriverByName("GTiff").Create(name + ".tif", W, H, TR, dtype)
ds.SetGeoTransform((0, px_area, 0, 0, 0, px_area))  # specify coords
# ds.SetProjection(base_raster.crs().authid())  # export coords to file
for i in range(TR):
    band = ds.GetRasterBand(i + 1)
    band.SetUnitType(name)
    if 0 != band.SetNoDataValue(nodata):
        feedback.pushWarning(f"Set No Data failed for {name}")
    if 0 != band.WriteArray(data[i]):
        feedback.pushWarning(f"WriteArray failed for {name}")
    band = None
ds.FlushCache()  # write to disk
ds = None

print("files are @", getcwd())