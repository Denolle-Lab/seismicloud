#
#   Deploy continuous phase detection on continuous mSEED data archive
#   Phase detection is done using EQTransformer via SeisBench. 
#   Launch detection for each station for each day of the year.
#   
#   Parallelization is done using MPI, and follows the joblist created by create_joblist.py
#

#   This script is designed to be run with an MPI command. The nproc specified in the MPI command must match the joblist. There are three required inputs arguments that must be passed with the call to the script:

#   -n,--network: which network of stations to run detection for; this must agree with the data archive, the config file and the job list; string
#   -y,--year: which year to run detection for; this must agree with the data archive, the config file and the job list; integer
#   -c, --config: path to config file; string

# This script checks which of the CPUs it is running on, filters the job list to only include jobs assigned to that CPU, and then iterates over those jobs to complete them.
# The actual detection is performed by a call to the script single_station_detection.py

# Status of the running script is written to logs, with a master log from the CPU with rank 0 and a sublog for each individual CPU
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
parser.add_argument("-y", "--year", type=int, required=True)
parser.add_argument("-c", "--config", required=True)
parser.add_argument("--appendlog", default=False, type=int)

args = parser.parse_args()
network = args.network
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
gpus = config["environment"]["CUDA_VISIBLE_DEVICES"]

if len(gpus) == 0:
    gpu = False
else:
    gpu = True

jobs = pd.read_csv(f"{jobs_path}/{network}_{year}_joblist.csv")

# Get number of processors from job list
nproc = len(jobs['rank'].unique())


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
    print(
        f"#Jobs:              {len(jobs[['station', 'rank']].drop_duplicates())}",
        flush=True,
    )
    print(f"#Cores:             {nproc}", flush=True)
    print(f"#GPU:               {len(gpus)}", flush=True)
    print(f"Submission time:    {time.strftime('%Z %x %X')}", flush=True)
    print(f"Verbose:            {verbose}", flush=True)
    print(f"-----------------------------------", flush=True)
    t0 = time.time()

comm.Barrier()

jobs = jobs[jobs["rank"] == rank]

for station in jobs["station"].unique():
    if gpu:
        gpuid = rank % len(gpus)
        current_time = time.strftime("%Z %x %X")
        os.system(
            f"echo 'master | \tsubmit {network}.{station}.{year} to C{rank}|G{gpuid} \t| {current_time}' >> {logs_path}/master.log"
        )
        os.system(
            f"{config['workflow']['interpreter']} /tmp/scripts/picking/single_station_detection.py"
            + f" -n {network} -s {station} -y {year} -r {rank} --gpuid {gpuid} -v {verbose} -c {fconfig} --pid {pid} "
        )
    else:
        current_time = time.strftime("%Z %x %X")
        os.system(
            f"echo 'master | \tsubmit {network}.{station}.{year} to C{rank} \t| {current_time}' >> {logs_path}/master.log"
        )
        os.system(
            f"{config['workflow']['interpreter']} /tmp/scripts/picking/single_station_detection.py"
            + f" -n {network} -s {station} -y {year} -r {rank} --gpuid {-1} -v {verbose} -c {fconfig} --pid {pid} "
        )

comm.Barrier()
if rank == 0:
    os.system(f"echo '-----------------------------------' >> {logs_path}/master.log")
    os.system(f"echo 'End of detection' >> {logs_path}/master.log")
    os.system(
        f"echo 'Run time:           {'%.3f' % (time.time() - t0)} seconds' >> {logs_path}/master.log"
    )
    logs.close()
