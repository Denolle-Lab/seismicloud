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
# parser.add_argument("-s", "--station", default=None)
parser.add_argument("-y", "--year", type=int, required=True)
parser.add_argument("-c", "--config", required=True)
parser.add_argument("--appendlog", default=False, type=int)

args = parser.parse_args()
network = args.network
# station = args.station
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
verbose = config["log"]["verbose"]

jobs_path = config["workflow"]["jobs_path"]
logs_path = config["log"]["logs_path"]
picks_path = config["workflow"]["picks_path"]
nproc = config["environment"]["NPROC"]
gpus = config["environment"]["CUDA_VISIBLE_DEVICES"]

jobs = pd.read_csv(f"{jobs_path}/{network}_{year}_joblist.csv")


if rank == 0:
    if config["log"]["appendlog"]:
        logs = open(f"{logs_path}/master.log", "a")
    else:
        os.system(f"rm {logs_path}/*")
        logs = open(f"{logs_path}/master.log", "w")
    sys.stdout = logs

    print(f"Job description", flush=True)
    print(f"Network:            {network}", flush=True)
    print(f"Year:               {year}", flush=True)
    print(f"#Station:           {len(jobs['station'].unique())}", flush=True)
    print(f"#Cores:             {nproc}", flush=True)
    print(f"#GPU:               {len(gpus)}", flush=True)
    print(f"Submission time:    {time.strftime('%Z %x %X')}", flush=True)
    print(f"Verbose:            {verbose}", flush=True)
    print(f"-----------------------------------", flush=True)
    t0 = time.time()

comm.Barrier()

jobs = jobs[jobs["rank"] == rank]

for station in jobs["station"].unique():
    gpuid = rank % len(gpus)
    current_time = time.strftime("%Z %x %X")
    os.system(
        f"echo 'master | \tsubmit {network}.{station}.{year} to C{rank}|G{gpuid} \t| {current_time}' >> {logs_path}/master.log"
    )
    os.system(
        f"{config['workflow']['interpreter']} scripts/single_station_detection.py"
        + f" -n {network} -s {station} -y {year} -r {rank} --gpuid {gpuid} -v {verbose} -c {fconfig} --pid {pid} "
    )

comm.Barrier()
if rank == 0:
    os.system(f"echo '-----------------------------------' >> {logs_path}/master.log")
    os.system(f"echo 'End of detection' >> {logs_path}/master.log")
    os.system(
        f"echo 'Run time:           {'%.3f' % (time.time() - t0)} seconds' >> {logs_path}/master.log"
    )
    logs.close()
