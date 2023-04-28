#
#   deploy phase association from continuous mSEED phase picking
#
#   Yiyu Ni
#   niyiyu@uw.edu
#   Oct. 24th, 2022
###########################################

import sys
import os
import json
import pickle
import obspy
import argparse

from obspy.core.event.base import WaveformStreamID
from obspy.core.event.origin import Origin, Pick
from obspy.core.event.event import Event
from obspy.core.event.catalog import Catalog
from obspy.core.utcdatetime import UTCDateTime as utc

import numpy as np
import pandas as pd
import seisbench
from gamma.utils import association

parser = argparse.ArgumentParser(
    description="Phase association from PNW continuous phase detection."
)
parser.add_argument("-y", "--year", required=True)
parser.add_argument("-c", "--config", required=True)

args = parser.parse_args()

## load configure file
fconfig = args.config
year = args.year
with open(fconfig, "r") as f:
    config = json.load(f)
verbose = config["log"]["verbose"]
logs_path = config["log"]["logs_path"]
association_config = config["model"]["association"]
picks_path = config["workflow"]["picks_path"]
catalog_path = association_config["catalog_path"]

if config["log"]["appendlog"]:
    logs = open(f"{logs_path}/associate.log", "a")
else:
    logs = open(f"{logs_path}/associate.log", "w")
sys.stderr = logs

# check https://github.com/AI4EPS/GaMMA/blob/master/docs/example_seisbench.ipynb for more documentation
from pyproj import CRS, Transformer

wgs84 = CRS.from_epsg(4326)
local_crs = CRS.from_epsg(9155)
transformer = Transformer.from_crs(wgs84, local_crs)

f_station = association_config["stations"]
station_df = pd.read_csv(f_station)
station_df.fillna("", inplace=True)
station_df["id"] = station_df.apply(
    lambda x: ".".join([x["network"], x["station"], x["location"]]), axis=1
)
station_df["x(km)"] = station_df.apply(
    lambda x: transformer.transform(x["latitude"], x["longitude"])[0] / 1e3, axis=1
)
station_df["y(km)"] = station_df.apply(
    lambda x: transformer.transform(x["latitude"], x["longitude"])[1] / 1e3, axis=1
)
station_df["z(km)"] = station_df["elevation"] / 1e3

association_config["bfgs_bounds"] = (
    (association_config["x(km)"][0] - 1, association_config["x(km)"][1] + 1),  # x
    (association_config["y(km)"][0] - 1, association_config["y(km)"][1] + 1),  # y
    (-10, association_config["z(km)"][1] + 1),  # x
    (None, None),  # t
)


cs = []
for doy in os.listdir("/".join([picks_path, year])):
    pick_df = []
    for net in os.listdir("/".join([picks_path, year, doy])):
        for sta in os.listdir("/".join([picks_path, year, doy, net])):
            with open("/".join([picks_path, year, doy, net, sta]), "rb") as f:
                picks = pickle.load(f)
            if len(picks) >= 1:
                for p in picks:
                    pick_df.append(
                        {
                            "id": p.trace_id,
                            "timestamp": p.peak_time.datetime,
                            "prob": p.peak_value,
                            "type": p.phase.lower(),
                            "sod": p.peak_time.timestamp
                            - utc(f"{year}{doy}").timestamp,
                        }
                    )
    pick_df = pd.DataFrame(pick_df)

    if len(pick_df) > 0:
        for h in range(24):
            pick_df_hour = pick_df[
                (pick_df["sod"] > h * 60 * 60) & (pick_df["sod"] < (h + 1) * 60 * 60)
            ]
            if len(pick_df_hour) > 1:
                try:
                    c, assignments = association(
                        pick_df_hour,
                        station_df,
                        association_config,
                        method=association_config["method"],
                    )
                    for i in c:
                        i["picks"] = []
                    for i in assignments:
                        c[i[1]]["picks"].append(dict(pick_df_hour.loc[i[0]]))
                    cs += c
                except:
                    pass

cat = Catalog()
for e in cs:
    event = Event()
    event.origins.append(Origin(time=utc(e["time"])))
    for p in e["picks"]:
        net, sta, loc = p["id"].split(".")
        pick = Pick(
            time=utc(p["timestamp"]),
            waveform_id=WaveformStreamID(
                network_code=net, station_code=sta, location_code=loc
            ),
            phase_hint=p["type"].upper(),
        )
        event.picks.append(pick)

    cat.append(event)
cat.write(f"{catalog_path}/{year}.xml", format="QUAKEML")
