#
#   Perform template matching on continuous data
#
#   Zoe Krauss
#   Oct. 5th, 2022
###########################################

import sys
import glob
import time
import json
import gc
import os

import argparse
import pickle
import logging
import warnings

warnings.filterwarnings(action="ignore")

parser = argparse.ArgumentParser(description="Template matching in continuous data.")
parser.add_argument("-n", "--network", required=True)
parser.add_argument("-d", "--day", required=True)
parser.add_argument("-c", "--config", required=True)
parser.add_argument("-y", "--year", required=True, type=int)
parser.add_argument("-r", "--rank", default=0, type=int)
parser.add_argument("-v", "--verbose", default=0, type=int)
parser.add_argument("-p", "--pid", default=0, type=int)
args = parser.parse_args()

year = args.year
network = args.network
day = args.day
rank = args.rank
verbose = args.verbose
pid = args.pid
mypid = os.getpid()

## load configure file
fconfig = args.config
with open(fconfig, "r") as f:
    config = json.load(f)

jobs_path = config["workflow"]["jobs_path"]
logs_path = config["log"]["logs_path"]
picks_path = config["workflow"]["picks_path"]
templates_path = config["workflow"]["templates_path"]
detections_path = config["workflow"]["detections_path"]
mseed_path = config["workflow"]["mseed_path"]
stations = config["workflow"]["stations"]
os.environ["OPENBLAS_NUM_THREADS"] = config["environment"]["OPENBLAS_NUM_THREADS"]
os.environ["MKL_NUM_THREADS"] = '1'
os.environ["NUMEXPR_NUM_THREADS"] = '1'
os.environ["OMP_NUM_THREADS"] = '1'

import obspy
import numpy as np
import pandas as pd
import eqcorrscan


logs = open(f"{logs_path}/{rank}.log", "a")
sys.stdout = logs

print(f"--------------{network}.{year}-----------------", flush=True)
print(f"{rank} | \tmaster PID {pid}", flush=True)
print(f"{rank} | \tPID {mypid}", flush=True)

templates = eqcorrscan.core.match_filter.tribe.Tribe().read(templates_path)

print(
    f"{rank} | \tloaded templates ({templates_path})",
    flush=True,
)

t0 = time.time()
doy = day
sdoy = str(doy).zfill(3)

    # Read day-long stream
s = obspy.core.stream.Stream()
for sta in stations:
    fpath = (
        mseed_path
        + str(network)
        + "/"
        + str(year)
        + "/"
        + str(day)
        + "/"
        + sta
        + "."
        + network
        + "."
        + str(year)
        + "."
        + str(day)
        )
    if os.path.exists(fpath):
        stream = obspy.core.stream.read(fpath)
        s += stream
    else:
        continue
            
print("Data pulled in")
s.merge()
print("Data merged")

if len(s) > 0:

    # Catch for short streams due to data gaps
    # Run with smaller process length if so
    stream_check = [ss for ss in s if len(ss)/ss.stats.sampling_rate >= (config["templates"]["process_len"] * 0.8)]
    if len(stream) > len(stream_check):
        print("Data is too short for day " + str(day) + ", running detections with process length of 1 hour")
    
        if len(s) == 3 * len(stations):
            temp_templates = templates.copy()
            for tt in temp_templates:
                tt.process_length = 3600.0
            party = temp_templates.detect(
                s,
                threshold=config["template_matching"]["threshold"],
                threshold_type=config["template_matching"]["threshold_type"],
                trig_int=config["template_matching"]["trig_int"],
                parallel_process=False,ignore_bad_data=True
            )

            num_detects = np.sum([len(f) for f in party])
            print(
                f"{rank} | \t{year}.{sdoy}.{network} \t| Finish, found {num_detects} detections \t | {'%.3f' % (time.time() - t0)} sec",
                flush=True,
            )

            # Save day-long party if there were detections
            # if num_detects > 0:
            save_name = f"{detections_path}/{network}_{year}_{doy}"
            party.write(save_name + ".xml", format="quakeml", overwrite=True)

            gc.collect()

        else:
            print("Data missing for some stations")    

    else:
        # try:
        picks = []
        #s.resample(config["templates"]["samp_rate"])
        #s.merge()
        if len(s) == 3 * len(stations):
            
            for tt in templates:
                tt.process_length = 3600.0
            
            party = templates.detect(
                    s,
                    threshold=config["template_matching"]["threshold"],
                    threshold_type=config["template_matching"]["threshold_type"],
                    trig_int=config["template_matching"]["trig_int"],
                    parallel_process=False,ignore_bad_data=True
                )

            num_detects = np.sum([len(f) for f in party])
            print(
                    f"{rank} | \t{year}.{sdoy}.{network} \t| Finish, found {num_detects} detections \t | {'%.3f' % (time.time() - t0)} sec",
                    flush=True,
                )

                # Save day-long party if there were detections
               # if num_detects > 0:
            save_name = f"{detections_path}/{network}_{year}_{doy}"
            party.write(save_name + ".xml", format="quakeml", overwrite=True)

            gc.collect()

        else:
            print("Data missing for some stations")

            # except:
            #    print(
            #        f"{rank} | \t{year}.{sdoy}.{network} \t| Error",
            #        flush=True,
            #    )
else:
    if verbose > 0:
        print(
                f"{rank} | \t{year}.{sdoy}.{network} \t| Skip: no data",
                flush=True,
            )

print(f"--------------{network}.{year}-----------------", flush=True)
logs.close()
