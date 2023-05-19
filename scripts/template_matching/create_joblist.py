#
#   Script to create a job list in .csv format, following which waveform files are available in a data archive
#   The job list distributes the names of these waveform files across the chosen number of CPUs

#   This script is for the template matching workflow, in which jobs are parallelized over day of the year only. Detection via template matching is performed on all stations for each day of the year simultaneously. 

#   Two required input arguments:
#       -c, --config: path to config file; string
#       -p, --nproc: number of CPUs to parallelize across; integer

#   Zoe Krauss, edited from Yiyu Ni
#   zkrauss@uw.edu
#   Oct. 5th, 2022
###########################################

import sys
import os
import json
import warnings
import argparse

warnings.simplefilter(action="ignore", category=FutureWarning)


## import user defined packages
import pandas as pd
from tqdm import tqdm



## prepare arg parser
parser = argparse.ArgumentParser(description="Template matching from continuous data")
parser.add_argument("-c", "--config", required=True)
parser.add_argument("-p","--nproc",required=True,type=int)
args = parser.parse_args()

# Number of CPUs to distribute jobs over:
nproc = args.nproc
# Path to config file:
fconfig = args.config


## load configure file
fconfig = args.config
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

detections_path = config["workflow"]["detections_path"]
os.makedirs(detections_path, exist_ok=True)

stations = config["workflow"]["stations"]
network = config["workflow"]["network"]

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
    # Then loop over years
    years = os.listdir("/".join([mseed_path, n]))
    for y in years:
        df = []
        # Then loop over days in the year
        doys = os.listdir("/".join([mseed_path, n, y]))
        for d in doys:
            df.append([n, y, d, "/".join([mseed_path, n, y, d])])
        
        # Make a table with all of the filepaths corresponding to days of the year in the data archive
        df = pd.DataFrame(df, columns=["network", "year", "doy", "fpath"])
        df = df.sort_values(by=["doy"])
        df.reset_index(drop=True, inplace=True)
        
        # Divide the days of the year to process amongst the chosen number of CPUs
        njobs = int(len(df) / nproc)
        df["rank"] = df.index.map(lambda x: int(x / njobs))
        
        # Write the job list to file!
        df.to_csv(
            "/".join([jobs_path, f"{n}_{y}_templatematching_joblist.csv"]), index=False
        )
