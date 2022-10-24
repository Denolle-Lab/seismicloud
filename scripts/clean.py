#
#   clean up past results and logs
#
#   Yiyu Ni
#   niyiyu@uw.edu
#   Oct. 24th, 2022
###########################################

import os
import json
import argparse

parser = argparse.ArgumentParser(
    description="Phase detection on continuous mSEED data archive"
)
parser.add_argument("-c", "--config", required=True)
args = parser.parse_args()

fconfig = args.config
with open(fconfig, "r") as f:
    config = json.load(f)

os.removedirs(config["workflow"]["jobs_path"])
os.removedirs(config["workflow"]["picks_path"])
os.removedirs(config["log"]["logs_path"])
os.removedirs(config["workflow"]["catalog_path"])
