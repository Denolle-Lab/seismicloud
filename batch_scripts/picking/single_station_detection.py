#
#   deploy continuous phase detection on continuous mSEED data archive
#   detection based on the job passed by the network_detection.py
#
#   Yiyu Ni
#   niyiyu@uw.edu
#   Oct. 5th, 2022
###########################################

import sys
import glob
import time
import json
import gc
import os

import argparse
import pickle
import logging
import warnings

warnings.filterwarnings(action="ignore")

parser = argparse.ArgumentParser(description="Picking on PNW continuous data.")
parser.add_argument("-n", "--network", required=True)
parser.add_argument("-s", "--station", required=True)
parser.add_argument("-c", "--config", required=True)
# parser.add_argument('-c', '--channel', required=True)
parser.add_argument("-g", "--gpuid", default=0, type=int)
parser.add_argument("-y", "--year", required=True, type=int)
parser.add_argument("-r", "--rank", default=0, type=int)
parser.add_argument("-v", "--verbose", default=0, type=int)
parser.add_argument("-p", "--pid", default=0, type=int)
args = parser.parse_args()

year = args.year
network = args.network
station = args.station
# channel = args.channel
rank = args.rank
verbose = args.verbose
pid = args.pid
mypid = os.getpid()
gpuid = args.gpuid

## load configure file
fconfig = args.config
with open(fconfig, "r") as f:
    config = json.load(f)

jobs_path = config["workflow"]["jobs_path"]
logs_path = config["log"]["logs_path"]
picks_path = config["workflow"]["picks_path"]
os.environ["OPENBLAS_NUM_THREADS"] = config["environment"]["OPENBLAS_NUM_THREADS"]

import obspy
from obspy.core.utcdatetime import UTCDateTime as utc
import numpy as np
import pandas as pd

os.environ["CUDA_VISIBLE_DEVICES"] = str(gpuid)
import seisbench
import seisbench.models as sbm
import torch

seisbench.logger.setLevel(logging.ERROR)
logs = open(f"{logs_path}/{rank}.log", "a")
sys.stdout = logs

print(f"--------------{network}.{station}.{year}-----------------", flush=True)
print(f"{rank} | \tmaster PID {pid}", flush=True)
print(f"{rank} | \tPID {mypid}", flush=True)

model_pnw = sbm.EQTransformer.from_pretrained(config["model"]["picking"]["pretrained"])
model_pnw.to(torch.device("cuda"))
model_pnw.default_args = config["model"]["picking"]["default_args"]
print(
    f"{rank} | \tloaded model ({config['model']['picking']['pretrained'].upper()}) to GPU:{gpuid}",
    flush=True,
)

jobs = pd.read_csv(f"{jobs_path}/{network}_{year}_joblist.csv")
jobs = jobs[jobs["station"] == station].reset_index(drop=True)
jobs = jobs[jobs["rank"] == rank].reset_index(drop=True)
jobs = jobs.sort_values("doy")
jobs = jobs.reset_index(drop=True)
print(f"{rank} | \ttotal {len(jobs)} days of data", flush=True)

for idx, i in jobs.iterrows():
    t0 = time.time()
    doy = i["doy"]
    fpath = i["fpath"]
    sdoy = str(doy).zfill(3)
    ss = []
    picks = []
    if config["model"]["picking"]["hourly_detection"]:
        # append hour-long stream
        for h in range(24):
            stime = utc(f"{year}{sdoy}T{str(h).zfill(2)}:00:00.000000")
            etime = utc(f"{year}{sdoy}T{str(h).zfill(2)}:59:59.999999")
            ss += [obspy.read(fpath, starttime=stime, endtime=etime)]
    else:
        # add day-long stream
        ss = [obspy.read(fpath)]

    for ih, s in enumerate(ss):
        if len(s) > 0:
            if len(s.get_gaps()) > config["model"]["picking"]["max_gap"]:
                print(
                    f"{rank} | \t{year}.{sdoy}.{network}.{station}.{ih} \t| Skip: too many gaps",
                    flush=True,
                )
            else:
                if verbose > 1:
                    print(
                        f"{rank} | \t{year}.{sdoy}.{network}.{station}.{ih} \t|",
                        s,
                        flush=True,
                    )
                elif verbose > 0:
                    current_time = time.strftime("%Z %x %X")
                    print(
                        f"{rank} | \t{year}.{sdoy}.{network}.{station}.{ih} \t| {current_time}",
                        flush=True,
                    )
                s.resample(100)
                s.detrend()
                s.normalize()
                s.filter("highpass", freq=2)
                try:
                    p, _ = model_pnw.classify(
                        s, strict=False, **config["model"]["picking"]["detection_args"]
                    )
                    picks += p
                except:
                    print(
                        f"{rank} | \t{year}.{sdoy}.{network}.{station}.{ih} \t| Skip: got error.",
                        flush=True,
                    )
                    pass

        else:
            if verbose > 0:
                print(
                    f"{rank} | \t{year}.{sdoy}.{network}.{station} \t| Skip: no data",
                    flush=True,
                )

    if len(picks) > 0:
        os.makedirs(f"{picks_path}/{year}/{sdoy}/{network}", exist_ok=True)
        with open(
            f"{picks_path}/{year}/{sdoy}/{network}/{station}.{network}.{year}.{sdoy}",
            "wb",
        ) as f:
            pickle.dump(picks, f)
        if verbose > 1:
            print(
                f"{rank} | \tdump picks to {picks_path}/{year}/{sdoy}/{network}/{station}.{network}.{year}.{sdoy}"
            )

    gc.collect()
    print(
        f"{rank} | \t{year}.{sdoy}.{network}.{station} \t| Finish, found {len(picks)} picks \t | {'%.3f' % (time.time() - t0)} sec",
        flush=True,
    )

    del picks, s

print(f"--------------{network}.{station}.{year}-----------------", flush=True)
logs.close()
