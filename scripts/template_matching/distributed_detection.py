#
#   Deploy continuous phase detection on continuous mSEED data archive
#   Phase detection is done using template matching via eqcorrscan. 
#   Launch detection for each day of the year.
#   
#   Parallelization is done using MPI, and follows the joblist created by create_joblist.py
#

#   This script is designed to be run with an MPI command. The nproc specified in the MPI command must match the joblist. There are three required inputs arguments that must be passed with the call to the script:

#   -n,--network: which network of stations to run detection for; this must agree with the data archive, the config file and the job list; string
#   -y,--year: which year to run detection for; this must agree with the data archive, the config file and the job list; integer
#   -c, --config: path to config file; string

# This script checks which of the CPUs it is running on, filters the job list to only include jobs assigned to that CPU, and then iterates over those jobs to complete them.
# The actual detection is performed by a call to the script detection.py

# Status of the running script is written to logs, with a master log from the CPU with rank 0 and a sublog for each individual CPU


#   Zoe Krauss, edited from Yiyu Ni
#   zkrauss@uw.edu
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

# Input arguments
args = parser.parse_args()
network = args.network
year = args.year

fconfig = args.config
appendlog = args.appendlog

# Initiate MPI
# Rank = CPU number; this is what the job list is referring to
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
# Make sure no extra multithreading occurs
os.environ["OPENBLAS_NUM_THREADS"] = config["environment"]["OPENBLAS_NUM_THREADS"]

# Read in job list
jobs = pd.read_csv(f"{jobs_path}{network}_{year}_templatematching_joblist.csv")

# Get number of processors from job list
nproc = len(jobs['rank'].unique())

# If operating on CPU with rank 0, write the master log
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

# Filter job list to only have jobs corresponding to rank of the CPU
jobs = jobs[jobs["rank"] == rank]

# Filter over the jobs that are left!
for day in jobs["doy"].unique():
    current_time = time.strftime("%Z %x %X")
    # Write to sublog, specific to rank
    os.system(
        f"echo 'master | \tsubmit {network}.{day}.{year} to C{rank} \t| {current_time}' >> {logs_path}master.log"
    )
    # Call to the script to perform the job
    # Note the many input arguments here- including rank and process id
    os.system(
        f"{config['workflow']['interpreter']} /tmp/scripts/template_matching/detection.py"
        + f" -n {network} -d {day} -y {year} -r {rank} -v {verbose} -c {fconfig} --pid {pid} "
    )

comm.Barrier()

# If finished and on CPU with rank 0, write run time to log
if rank == 0:
    os.system(f"echo '-----------------------------------' >> {logs_path}master.log")
    os.system(f"echo 'End of detection' >> {logs_path}master.log")
    os.system(
        f"echo 'Run time:           {'%.3f' % (time.time() - t0)} seconds' >> {logs_path}master.log"
    )
    logs.close()
