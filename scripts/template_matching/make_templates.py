"""
Saves templates to the templates_path specified in the config file
"""


import obspy
import eqcorrscan
import numpy as np
import pandas as pd
import tarfile
import os
import argparse
import datetime
import json

############################################
############### INITIALIZE #################
############################################

parser = argparse.ArgumentParser(
    description="Creating templates from continuous data based on a starting catalog."
)
parser.add_argument("-c", "--config", required=True)
args = parser.parse_args()

## load configure file
fconfig = args.config
with open(fconfig, "r") as f:
    config = json.load(f)

# Pathnames
templates_path = config["workflow"]["templates_path"]  # this should be a .tgz filename
mseed_path = config["workflow"]["mseed_path"]
starting_cat_path = config["workflow"]["starting_cat_path"]

stations = config["workflow"]["stations"]
network = config["workflow"]["network"]

# Template parameters
lowcut = config["templates"]["lowcut"]
highcut = config["templates"]["highcut"]
filt_order = config["templates"]["filt_order"]
data_pad = config["templates"]["data_pad"]
samp_rate = config["templates"]["samp_rate"]
length = config["templates"]["length"]
prepick = config["templates"]["prepick"]
process_len = config["templates"]["process_len"]
min_snr = config["templates"]["min_snr"]
swin = config["templates"]["swin"]

# Catalog filters
min_lat = config["starting_catalog"]["min_lat"]
max_lat = config["starting_catalog"]["max_lat"]
min_lon = config["starting_catalog"]["min_lon"]
max_lon = config["starting_catalog"]["max_lon"]
min_time = config["starting_catalog"]["min_time"]
min_time = datetime.datetime.strptime(min_time, "%Y,%m,%d,%H,%M,%S")
max_time = config["starting_catalog"]["max_time"]
max_time = datetime.datetime.strptime(max_time, "%Y,%m,%d,%H,%M,%S")
min_magnitude = config["starting_catalog"]["min_magnitude"]
max_magnitude = config["starting_catalog"]["max_magnitude"]

############################################
####### PROCESS STARTING CATALOG ###########
############################################

# Read in starting catalog
cat = obspy.core.event.catalog.read_events(starting_cat_path)
print("Read in catalog")

# Filter catalog
min_time = min_time.strftime("%Y-%m-%dT%H:%M:%S")
max_time = max_time.strftime("%Y-%m-%dT%H:%M:%S")
t1_filter = "time > " + min_time
t2_filter = "time < " + max_time
lon1_filter = "longitude > " + str(min_lon)
lon2_filter = "longitude < " + str(max_lon)
lat1_filter = "latitude > " + str(min_lat)
lat2_filter = "latitude < " + str(max_lat)
mag1_filter = "magnitude > " + str(min_magnitude)
mag2_filter = "magnitude < " + str(max_magnitude)
cat = cat.filter(
    t1_filter,
    t2_filter,
    lon1_filter,
    lon2_filter,
    lat1_filter,
    lat2_filter,
    mag1_filter,
)

# Add in a phase hint to the picks
for event in cat.events:
    for pick in event.picks:
        pick_id = pick.resource_id
        arr = [a for a in event.origins[0].arrivals if a.pick_id == pick_id]
        pick.phase_hint = arr[0].phase

print("Filtered catalog")

############################################
####### CREATE TEMPLATES         ###########
############################################

template_list = []

# Start base day as none
base_day = None

# Loop over events in catalog and make a template for each
# Load one day-long stream in as needed
for i, ev in enumerate(cat):

    # Check if we need to pull in a new stream
    if ev.origins[0].time.datetime.strftime("%Y%m%d") != base_day:
        # Reset the day we are on and pull in a new stream
        base_day = ev.origins[0].time.datetime.strftime("%Y%m%d")
        print("Downloading templates for " + base_day)
        year = str(ev.origins[0].time.datetime.year)
        yearday = ev.origins[0].time.datetime.strftime("%j")
        # Loop through stations to make the complete stream
        st = obspy.core.stream.Stream()
        for sta in stations:
            path = (
                mseed_path
                + str(network)
                + "/"
                + year
                + "/"
                + yearday
                + "/"
                + sta
                + "."
                + network
                + "."
                + year
                + "."
                + yearday
            )
            stream = obspy.core.stream.read(path)
            st += stream
        st.resample(samp_rate)

    temp_cat = obspy.core.event.Catalog(events=[ev])

    # Process stream
    template_st = eqcorrscan.core.template_gen.template_gen(
        method="from_meta_file",
        st=st,
        lowcut=lowcut,
        highcut=highcut,
        samp_rate=samp_rate,
        length=length,
        filt_order=filt_order,
        prepick=prepick,
        meta_file=temp_cat,
        data_pad=data_pad,
        process_len=process_len,
        min_snr=min_snr,
        parallel=False,
        swin=swin,
        delayed=True,
        skip_short_chans=True,
    )

    # Make template from processed waveform
    template = eqcorrscan.core.match_filter.template.Template(
        name=str(ev.resource_id.id)[-6:],
        st=template_st[0],
        lowcut=lowcut,
        highcut=highcut,
        samp_rate=samp_rate,
        filt_order=filt_order,
        process_length=process_len,
        prepick=prepick,
        event=ev,
    )
    template_list.append(template)

# Make a "tribe" from the templates
# Make sure that resource id in the tribe events matches the template
tribe = eqcorrscan.core.match_filter.tribe.Tribe(templates=template_list)
for i, t in enumerate(tribe):
    tribe[i].event.origins[0].resource_id = t.name

# Write templates to file, if desired
tribe.write(templates_path)
