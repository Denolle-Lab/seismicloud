#
#   Follows scripts/template_matching/create_joblist.py, with edits

#   input argument --batchnodes is number of virtual machines/nodes in the Pool, NOT the number of vCPUs on each node
#
# Creates a job list where the rank of each job corresponds to the node in the Pool 

#   Zoe Krauss, edited from Yiyu Ni
#   zkrauss@uw.edu
#   Oct. 5th, 2022
###########################################

from mpi4py import MPI
import sys
import os
import json
import warnings
import argparse

warnings.simplefilter(action="ignore", category=FutureWarning)


## import user defined packages
import pandas as pd
from tqdm import tqdm
import numpy as np


## prepare arg parser
parser = argparse.ArgumentParser(description="Template matching from continuous data")
parser.add_argument("-c", "--config", required=True)
parser.add_argument("-b","--batchnodes",type=int,required=True)
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

templates_path = config["workflow"]["templates_path"]  # should already exist, is a file

detections_path = config["workflow"]["detections_path"]
os.makedirs(detections_path, exist_ok=True)


stations = config["workflow"]["stations"]
network = config["workflow"]["network"]

nproc = args.batchnodes


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
            # stas = os.listdir("/".join([mseed_path, n, y, d]))
            #    for s in stas:
            df.append([n, y, d, "/".join([mseed_path, n, y, d])])

        df = pd.DataFrame(df, columns=["network", "year", "doy", "fpath"])
        df = df.sort_values(by=["doy"])
        df.reset_index(drop=True, inplace=True)
        
        # Distribute jobs amongst nodes
        # If they do not distribute evenly, distribute the extra one at a time
        njobs = int(np.ceil(len(df)/nproc))
        njobs = len(df) // nproc
        over = len(df)%nproc
        if over > 0:
            x = np.arange(nproc)
            starting_list = np.repeat(x,njobs)
            final_list = np.append(starting_list,[i for i in range(over)])
        else:
            x = np.arange(nproc)
            starting_list = np.repeat(x,njobs)
            final_list = starting_list
        df["rank"] = df.index.map(lambda x: final_list[x])

        df.to_csv(
            "/".join([jobs_path, f"{n}_{y}_templatematching_batchlist.csv"]), index=False
        )
