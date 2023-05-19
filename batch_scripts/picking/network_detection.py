#
#   Follows scripts/picking/network_detection.py with some edits to run on cloud
#
#   Extra input argument --batchid refers to the node in the Pool that this script is running on
#   Parallelization across the CPUs on this specific node is then done via MPI


#   Before iterating over jobs, job list is reconfigured to only contain jobs specific to this node number


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
parser.add_argument("-b", "--batchid", type=int, required=True)

args = parser.parse_args()
network = args.network
year = args.year

fconfig = args.config
batchid = args.batchid

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

if len(gpus) == 0:
    gpu = False
else:
    gpu = True

jobs = pd.read_csv(f"{jobs_path}/{network}_{year}_{batchid}_joblist.csv")


if rank == 0:
    os.system(f"echo 'Job description' >> {logs_path}/master_{batchid}.log")
    os.system(
        f"echo 'Network:            {network}' >> {logs_path}/master_{batchid}.log"
    )
    os.system(f"echo 'Year:               {year}' >> {logs_path}/master_{batchid}.log")
    os.system(
        f"echo 'Task ID:            {batchid}' >> {logs_path}/master_{batchid}.log"
    )
    os.system(
        f"echo '#Station:           {len(jobs['station'].unique())}' >> {logs_path}/master_{batchid}.log"
    )
    os.system(
        f"echo '#Jobs:              {len(jobs[['station', 'rank']].drop_duplicates())}' >> {logs_path}/master_{batchid}.log"
    )
    os.system(f"echo '#Cores:             {nproc}' >> {logs_path}/master_{batchid}.log")
    os.system(
        f"echo '#GPU:               {len(gpus)}' >> {logs_path}/master_{batchid}.log"
    )
    os.system(
        f"echo 'Submission time:    {time.strftime('%Z %x %X')}' >> {logs_path}/master_{batchid}.log"
    )
    os.system(
        f"echo 'Verbose:            {verbose}' >> {logs_path}/master_{batchid}.log"
    )
    os.system(
        f"echo '-----------------------------------' >> {logs_path}/master_{batchid}.log"
    )
    t0 = time.time()

comm.Barrier()

# Filter job list!!!
jobs = jobs[jobs["rank"] == rank]

for station in jobs["station"].unique():
    if gpu:
        gpuid = rank % len(gpus)
        current_time = time.strftime("%Z %x %X")
        os.system(
            f"echo 'master | \tsubmit {network}.{station}.{year} to C{rank}|G{gpuid} \t| {current_time}' >> {logs_path}/master_{batchid}.log"
        )
        os.system(
            f"{config['workflow']['interpreter']} /tmp/batch_scripts/picking/single_station_detection.py"
            + f" -n {network} -s {station} -y {year} -r {rank} --gpuid {gpuid} -v {verbose} -c {fconfig} --pid {pid} -b {batchid}"
        )
    else:
        current_time = time.strftime("%Z %x %X")
        os.system(
            f"echo 'master | \tsubmit {network}.{station}.{year} to C{rank} \t| {current_time}' >> {logs_path}/master_{batchid}.log"
        )
        os.system(
            f"{config['workflow']['interpreter']} /tmp/batch_scripts/picking/single_station_detection.py"
            + f" -n {network} -s {station} -y {year} -r {rank} --gpuid {-1} -v {verbose} -c {fconfig} --pid {pid} -b {batchid}"
        )

comm.Barrier()
if rank == 0:
    os.system(
        f"echo '-----------------------------------' >> {logs_path}/master_{batchid}.log"
    )
    os.system(f"echo 'End of detection' >> {logs_path}/master_{batchid}.log")
    os.system(
        f"echo 'Run time:           {'%.3f' % (time.time() - t0)} seconds' >> {logs_path}/master_{batchid}.log"
    )
