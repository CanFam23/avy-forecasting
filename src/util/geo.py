import json
import os
from typing import Literal

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
import s3fs
import xarray as xr
from geographiclib.geodesic import Geodesic
from rasterio.transform import xy
from rasterio.warp import transform, transform_bounds
from rasterio.windows import from_bounds
from shapely import Polygon
from shapely.geometry import Point

fs = s3fs.S3FileSystem(anon=True)

from src.config import COORDS_FP, LOC_TIFS_FP, TIFS_FP

def get_midpoint(lat1, lon1, lat2, lon2):
    # Compute path from 1 to 2
    g = Geodesic.WGS84.Inverse(lat1, lon1, lat2, lon2);

    # Compute midpoint starting at 1
    h1 = Geodesic.WGS84.Direct(lat1, lon1, g['azi1'], g['s12']/2);
    # print(h1['lat2'],h1['lon2'])
    return h1

def get_bbox(lat: float, lon: float, ret_val: Literal["gdf", "poly"] = "gdf") -> gpd.GeoDataFrame:
    chunk_index = xr.open_zarr(s3fs.S3Map("s3://hrrrzarr/grid/HRRR_chunk_index.zarr", s3=fs))

    # open HRRR grid metadata (Zarr)
    lats = chunk_index.latitude.values
    lons = chunk_index.longitude.values

    # Find the nearest grid cell index
    dist = np.sqrt((lats - lat)**2 + (lons - lon)**2)
    iy, ix = np.unravel_index(np.argmin(dist), dist.shape)

    # Get neighbors
    neighbor_offsets = [(-1, 0), (-1,-1), (0, -1), (1, -1),
                        (1, 0), (1, 1), (0, 1), (-1, 1)]

    bbox = []
    coords = []
    for dy, dx in neighbor_offsets:
        ny, nx = iy + dy, ix + dx

        midpoint = get_midpoint(lat,lon,lats[ny, nx], lons[ny, nx])

        if 0 <= ny < lats.shape[0] and 0 <= nx < lats.shape[1]:
            bbox.append({
                "index_y": ny,
                "index_x": nx,
                "lat": midpoint['lat2'],
                "lon": midpoint['lon2'],
                "geometry": Point(midpoint['lon2'],midpoint['lat2'])
            })
            
            coords.append((midpoint['lon2'],midpoint['lat2']))

    if ret_val == "gdf":
        return gpd.GeoDataFrame(bbox, geometry="geometry", crs="EPSG:4326")
    else:
        poly = Polygon(coords)

        return gpd.GeoDataFrame([{
            "index_y": iy,
            "index_x": ix,
            "geometry": poly
        }], crs="EPSG:4326")
    
def calculate_elevation(gdf: gpd.GeoDataFrame, rast_file_path: str) -> float:
    min_lat = gdf['lat'].min()
    max_lat = gdf['lat'].max()
    min_lon = gdf['lon'].min()
    max_lon = gdf['lon'].max()
    
    with rasterio.open(rast_file_path) as src:
        # Transform bbox to raster CRS
        bbox_proj = transform_bounds("EPSG:4326", src.crs,
                                    min_lon, min_lat, max_lon, max_lat)
        
        # Create a window for that bounding box
        window = from_bounds(*bbox_proj, transform=src.transform)

        # Read elevation subset
        subset = src.read(1, window=window)
        
        # Get transform for subset
        subset_transform = src.window_transform(window)

        # Get rows and cols
        rows, cols = np.indices(subset.shape)

        # Convert each pixel (row, col) to x/y in raster CRS
        xs, ys = xy(subset_transform, rows, cols)
        xs = np.array(xs)
        ys = np.array(ys)

        # Flatten everything for easy use
        elev = subset.flatten()
        xs = xs.flatten()
        ys = ys.flatten()

        # Convert back to lat/lon
        lons, lats = transform(src.crs, "EPSG:4326", xs, ys) # type: ignore

    # Combine into a DataFrame for convenience
    df = pd.DataFrame({
        "lon": lons,
        "lat": lats,
        "elevation_m": elev
    })
    
    df = df[df["elevation_m"] >= 0] # Missing values are -999,999 in tif files, so need to filter those out
    
    if df.empty:
        return -1
    
    return df['elevation_m'].mean()

def find_elevation(id: int, lat: float, lon: float) -> float:
    with open(LOC_TIFS_FP, "r") as file:
        json_data = json.load(file)
    if str(id) in json_data.keys():
        return json_data.get(str(id))['elevation']
    
    bbox = get_bbox(lat,lon, "gdf")
    
    # If elevation isn't found in the file above, need to check all tif files to see if it can be found
    # This is pretty slow, which is why the elevations are saved in a json file. 
    for tif_file in os.listdir(TIFS_FP):
        elevation = calculate_elevation(bbox, os.path.join(TIFS_FP, tif_file))
        if elevation != -1:
            json_data[str(id)] = {
                "elevation": elevation,
                "tif_file": tif_file
            }
            with open(LOC_TIFS_FP, "w") as file:
                json.dump(obj=json_data, fp=file,default=float, indent=2)
            return elevation

    raise ValueError(f"No tif file found for point #{id} at {lat}, {lon}")