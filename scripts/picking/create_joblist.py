#
#   deploy continuous phase detection on continuous mSEED data archive
#
#   Yiyu Ni
#   niyiyu@uw.edu
#   Oct. 5th, 2022
###########################################

from mpi4py import MPI
import sys
import os
import json
import warnings
import argparse
import math

warnings.simplefilter(action="ignore", category=FutureWarning)

## import user defined packages
import pandas as pd

## intialize MPI
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

## prepare arg parser
parser = argparse.ArgumentParser(
    description="Phase detection on continuous mSEED data archive"
)
parser.add_argument("-c", "--config", required=True)
args = parser.parse_args()


## load configure file
fconfig = args.config
with open(fconfig, "r") as f:
    config = json.load(f)
workflow_config = config["workflow"]

mseed_path = config["workflow"]["mseed_path"]
assert os.path.exists(mseed_path)

jobs_path = config["workflow"]["jobs_path"]
os.makedirs(jobs_path, exist_ok=True)

logs_path = config["log"]["logs_path"]
os.makedirs(logs_path, exist_ok=True)

picks_path = config["workflow"]["picks_path"]
os.makedirs(picks_path, exist_ok=True)

catalog_path = config["workflow"]["catalog_path"]
os.makedirs(catalog_path, exist_ok=True)

nproc = config["environment"]["NPROC"]
gpus = config["environment"]["CUDA_VISIBLE_DEVICES"]


## assuming a data archive
## NET
##  |- YYYY
##     |- DOY
##        |- STA.NET.YYYY.DOY

## create job list based on the data archive
nets = os.listdir(mseed_path)
for n in nets:
    years = os.listdir("/".join([mseed_path, n]))
    for y in years:
        df = []
        doys = os.listdir("/".join([mseed_path, n, y]))
        for d in doys:
            stas = os.listdir("/".join([mseed_path, n, y, d]))
            for s in stas:
                df.append(
                    [s.split(".")[0], n, y, d, "/".join([mseed_path, n, y, d, s])]
                )

        df = pd.DataFrame(df, columns=["station", "network", "year", "doy", "fpath"])
        df = df.sort_values(by=["station", "doy"])
        df.reset_index(drop=True, inplace=True)
        njobs = math.ceil(len(df) / nproc)
        df["rank"] = df.index.map(lambda x: int(x / njobs))

        df.to_csv("/".join([jobs_path, f"{n}_{y}_joblist.csv"]), index=False)

# warm-up the model
model_pnw = sbm.EQTransformer.from_pretrained(config["model"]["picking"]["pretrained"])