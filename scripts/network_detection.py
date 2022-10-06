#
#   deploy continuous phase detection on continuous mSEED data archive
#   launch detection for each station
#
#   Yiyu Ni
#   niyiyu@uw.edu
#   Oct. 5th, 2022
###########################################

from mpi4py import MPI

import os
import sys
import time
import json
import argparse

import pandas as pd

parser = argparse.ArgumentParser(description="Picking on PNW continuous data.")
parser.add_argument("-n", "--network", required=True)
parser.add_argument("-s", "--station", default=None)
parser.add_argument("-y", "--year", type=int, required=True)
parser.add_argument("-c", "--config", required=True)
parser.add_argument("--appendlog", default=0, type=int)

args = parser.parse_args()
network = args.network
station = args.station
year = args.year
fconfig = args.config
appendlog = args.appendlog

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()
pid = os.getpid()

## load configure file
fconfig = args.config
with open(fconfig, "r") as f:
    config = json.load(f)
verbose = config['logs']["verbose"]

jobs_path = config["workflow"]["jobs_path"]
logs_path = config["logs"]["logs_path"]
picks_path = config["workflow"]["picks_path"]
gpus = config['environment']['CUDA_VISIBLE_DEVICES']

jobs = pd.read_csv(f"{jobs_path}/{network}_{year}_joblist.csv")
if station:
    jobs = jobs[jobs["station"] == station].reset_index(drop=True)
jobs = jobs["station"].unique()
jobs = sorted(jobs)

if rank == 0:
    current_time = time.strftime("%Z %x %X")

    if config["logs"]['appendlog'] > 0:
        logs = open(f"{logs_path}/master.log", "a")
    else:
        os.system(f"rm {logs_path}/*")
        logs = open(f"{logs_path}/master.log", "w")
    sys.stdout = logs

    print(f"Job description", flush=True)
    print(f"Network:            {network}", flush=True)
    print(f"Year:               {year}", flush=True)
    print(f"#Station:           {len(jobs)}", flush=True)
    print(f"Submission time:    {current_time}", flush=True)
    print(f"Verbose:            {verbose}", flush=True)
    print(f"Cores:              {size}", flush=True)
    print(f"Total jobs:         {len(jobs)}", flush=True)
    print(f"-----------------------------------", flush=True)


comm.Barrier()
for idx, station in enumerate(jobs):
    if idx % size == rank:
        gpuid = idx % len(gpus)
        current_time = time.strftime("%Z %x %X")
        os.system(
            f"echo 'master | \tsubmit {network}.{station}.{year} by rank {rank} \t| {idx + 1}/{len(jobs)} \t| {current_time}' >> {logs_path}/master.log"
        )
        os.system(
            f"{config['workflow']['interpreter']} scripts/single_station_detection.py"
            + f" -n {network} -s {station} -y {year} -r {rank} -v {verbose} -c {fconfig} --pid {pid} --gpuid {gpuid}"
        )

comm.Barrier()
if rank == 0:
    logs.close()
