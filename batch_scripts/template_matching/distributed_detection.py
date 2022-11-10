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
import numpy as np

parser = argparse.ArgumentParser(description="Template matching in continuous data")
parser.add_argument("-n", "--network", required=True)
parser.add_argument("-y", "--year", type=int, required=True)
parser.add_argument("-c", "--config", required=True)
parser.add_argument("-b","--batchnode",type=int,required=True) # Which node in the batch pool we are working in
parser.add_argument("--appendlog", default=False, type=int)

args = parser.parse_args()
network = args.network
year = args.year
batchnode = args.batchnode

fconfig = args.config
appendlog = args.appendlog

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()
pid = os.getpid()

## load configure file:
fconfig = args.config
with open(fconfig, "r") as f:
    config = json.load(f)
verbose = config["log"]["verbose"]

jobs_path = config["workflow"]["jobs_path"]
logs_path = config["log"]["logs_path"]
os.environ["OPENBLAS_NUM_THREADS"] = config["environment"]["OPENBLAS_NUM_THREADS"]

nproc = os.cpu_count()

if batchnode == 0:
    if config["log"]["appendlog"]:
        logs = open(f"{logs_path}master_{batchnode}.log", "a")
    else:
        os.system(f"rm {logs_path}*")
        logs = open(f"{logs_path}master_{batchnode}.log", "w")
    sys.stdout = logs

    os.system(f"echo 'Job description' >> {logs_path}master_{batchnode}.log")
    os.system(f"echo 'Network:            {network}' >> {logs_path}master_{batchnode}.log")
    os.system(f"echo 'Year:               {year}' >> {logs_path}master_{batchnode}.log")
    os.system(f"echo 'Cores:             {nproc}' >> {logs_path}master_{batchnode}.log")
    os.system(f"echo 'Submission time:    {time.strftime('%Z %x %X')}' >> {logs_path}master_{batchnode}.log")
    os.system(f"echo 'Verbose:            {verbose}' >> {logs_path}master_{batchnode}.log")
    os.system(f"echo '-----------------------------------' >> {logs_path}master_{batchnode}.log")
    t0 = time.time()
    
comm.Barrier()



##################################################################
####### Reconfigure jobs list to only contain ranks = batchnode ##
## Then add a new column with reset ranks, specific to the node ##
##################################################################

jobs = pd.read_csv(f"{jobs_path}{network}_{year}_templatematching_batchlist.csv")
jobs = jobs[jobs["rank"] == batchnode]
n_new_ranks = int(np.ceil(len(jobs)/nproc))
jobs["rank"] = jobs.index.map(lambda x: int(x / n_new_ranks))



jobs = jobs[jobs["rank"] == rank]

for day in jobs["doy"].unique():
    current_time = time.strftime("%Z %x %X")
    os.system(
        f"echo 'master | \tsubmit {network}.{day}.{year} to C{rank} \t| {current_time}' >> {logs_path}master_{batchnode}.log"
    )
    os.system(
        f"{config['workflow']['interpreter']} /tmp/batch_scripts/template_matching/detection.py"
        + f" -d {day} -y {year} -r {rank} -v {verbose} -c {fconfig} -b {batchnode} "
    )

comm.Barrier()
if rank == 0:
    os.system(f"echo '-----------------------------------' >> {logs_path}master_{batchnode}.log")
    os.system(f"echo 'End of detection' >> {logs_path}master_{batchnode}.log")
    os.system(
        f"echo 'Run time:           {'%.3f' % (time.time() - t0)} seconds' >> {logs_path}master_{batchnode}.log"
    )
    logs.close()
