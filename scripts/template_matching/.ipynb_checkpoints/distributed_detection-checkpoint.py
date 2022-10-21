#
#   deploy continuous phase detection on continuous mSEED data archive
#   launch detection for each station
#
#   Zoe Krauss, edited from Yiyu Ni
#   Basically just replaced the "station" argument with "day"
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

parser = argparse.ArgumentParser(description="Template matching in continuous data")
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
nproc = config["environment"]["NPROC"]

jobs = pd.read_csv(f"{jobs_path}{network}_{year}_templatematching_joblist.csv")


if rank == 0:
    if config["log"]["appendlog"]:
        logs = open(f"{logs_path}master.log", "a")
    else:
        os.system(f"rm {logs_path}*")
        logs = open(f"{logs_path}master.log", "w")
    sys.stdout = logs

    print(f"Job description", flush=True)
    print(f"Network:            {network}", flush=True)
    print(f"Year:               {year}", flush=True)
    print(f"#Cores:             {nproc}", flush=True)
    print(f"Submission time:    {time.strftime('%Z %x %X')}", flush=True)
    print(f"Verbose:            {verbose}", flush=True)
    print(f"-----------------------------------", flush=True)
    t0 = time.time()

comm.Barrier()

jobs = jobs[jobs["rank"] == rank]
print(jobs)

for day in jobs["doy"].unique():
    current_time = time.strftime("%Z %x %X")
    os.system(
        f"echo 'master | \tsubmit {network}.{day}.{year} to C{rank} \t| {current_time}' >> {logs_path}master.log"
    )
    os.system(
        f"{config['workflow']['interpreter']} scripts/template_matching/detection.py"
        + f" -n {network} -d {day} -y {year} -r {rank} -v {verbose} -c {fconfig} --pid {pid} "
    )

comm.Barrier()
if rank == 0:
    os.system(f"echo '-----------------------------------' >> {logs_path}master.log")
    os.system(f"echo 'End of detection' >> {logs_path}master.log")
    os.system(
        f"echo 'Run time:           {'%.3f' % (time.time() - t0)} seconds' >> {logs_path}master.log"
    )
    logs.close()
