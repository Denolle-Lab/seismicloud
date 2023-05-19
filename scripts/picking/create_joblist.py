#
#   Script to create a job list in .csv format, following which waveform files are available in a data archive
#   The job list distributes the names of these waveform files across the chosen number of CPUs

#   This script is for the machine learning/EQTransformer workflow, in which jobs are parallelized over each station for each day of the year. Detection via EQTransformer is performed on all stations for each day of the year separately, and picks for each station are associated into events after initial detection. 

#   Two required input arguments:
#       -c, --config: path to config file; string
#       -p, --nproc: number of CPUs to parallelize across; integer

#   Yiyu Ni
#   niyiyu@uw.edu
#   Oct. 5th, 2022
###########################################

import sys
import os
import json
import warnings
import argparse
import math

warnings.simplefilter(action="ignore", category=FutureWarning)

## import user defined packages
import pandas as pd
import seisbench.models as sbm



## prepare arg parser
parser = argparse.ArgumentParser(
    description="Phase detection on continuous mSEED data archive"
)
parser.add_argument("-c", "--config", required=True)
parser.add_argument("-p","--nproc",required=True,type=int)
args = parser.parse_args()

# Number of CPUs to distribute jobs over:
nproc = args.nproc
# Path to config file:
fconfig = args.config

## load configure file
with open(fconfig, "r") as f:
    config = json.load(f)
workflow_config = config["workflow"]

# Make sure that the directory with waveform data is accessible
mseed_path = config["workflow"]["mseed_path"]
assert os.path.exists(mseed_path)

# Directory to write job list to 
jobs_path = config["workflow"]["jobs_path"]
os.makedirs(jobs_path, exist_ok=True)

logs_path = config["log"]["logs_path"]
os.makedirs(logs_path, exist_ok=True)

picks_path = config["workflow"]["picks_path"]
os.makedirs(picks_path, exist_ok=True)

catalog_path = config["workflow"]["catalog_path"]
os.makedirs(catalog_path, exist_ok=True)


gpus = config["environment"]["CUDA_VISIBLE_DEVICES"]


###########################################
# CREATE JOB LIST BASED ON THE DATA ARCHIVE

## assuming a data archive with the following format:
## NET
##  |- YYYY
##     |- DOY
##        |- STA.NET.YYYY.DOY

# First loop over networks
nets = os.listdir(mseed_path)
for n in nets:
    # Then years
    years = os.listdir("/".join([mseed_path, n]))
    for y in years:
        df = []
        # Then days of the year
        doys = os.listdir("/".join([mseed_path, n, y]))
        for d in doys:
            # Then stations!!!!
            stas = os.listdir("/".join([mseed_path, n, y, d]))
            for s in stas:
                df.append(
                    [s.split(".")[0], n, y, d, "/".join([mseed_path, n, y, d, s])]
                )

        # Make a table with all of the filepaths corresponding to station per day of the year in the data archive
        df = pd.DataFrame(df, columns=["station", "network", "year", "doy", "fpath"])
        
        # Divide the station per day of the year to process amongst the chosen number of CPUs
        df = df.sort_values(by=["station", "doy"])
        df.reset_index(drop=True, inplace=True)
        njobs = math.ceil(len(df) / nproc)
        df["rank"] = df.index.map(lambda x: int(x / njobs))
        
        # Write the job list to file!
        df.to_csv("/".join([jobs_path, f"{n}_{y}_joblist.csv"]), index=False)

# warm-up the model
model_pnw = sbm.EQTransformer.from_pretrained(config["model"]["picking"]["pretrained"])
