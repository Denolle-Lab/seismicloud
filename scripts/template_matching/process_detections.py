##########################################
# This script reads in individual daily .xml files of earthquake detections from template matching,
# removes duplicate detections between different templates,
# and combines all detections into one obspy catalog object
# It then writes this summary obspy catalog to a QuakeML file at the path specified

# Inputs:
# input = complete file path to where individual .xml files of daily detections are stored
# output = file name of where the summary earthquake catalog should be written to, in QuakeML format
# threshold = time in seconds to call two detections, made by different templates, duplicates

# Zoe Krauss
# zkrauss@uw.edu
##########################################


import obspy
import glob
import numpy as np
import datetime
import argparse

## prepare arg parser
parser = argparse.ArgumentParser(description="Combining template matching picks")
parser.add_argument("--input", required=True)
parser.add_argument("--output",required=True)
parser.add_argument("--threshold",required=True,type=int)
args = parser.parse_args()

input_folder = args.input
output_file = args.output
time_int = args.threshold

# Function for removing duplicates
def remove_dupes(starting_catalog,time_int):
    
    evs = [ev for ev in starting_catalog]
    
    keep_cat = obspy.core.event.catalog.Catalog()


    # Sort catalog by time
    times = []
    for ev in evs:
        times.append(ev.picks[0].time.datetime)
    sort_ind = np.argsort(times)
    times.sort()
    evs = [evs[si] for si in sort_ind]

    # Go through catalog and keep only events with
    # the highest detection value that occur more than time_int apart

    base_ind = 0
    while base_ind < len(evs):
        diffs = [t-times[base_ind] for t in times]
        comp_ind = [ind for ind,d in enumerate(diffs) if np.abs(d) < datetime.timedelta(seconds=time_int)]
        if len(comp_ind) > 1:
            vals = [float(evs[ci].comments[2].text.split('=')[1]) for ci in comp_ind]
            keep_ind = np.argmax(vals)
            keep_cat.extend([evs[comp_ind[keep_ind]]])
            base_ind = np.max(comp_ind) + 1
        else:
            keep_cat.extend([evs[base_ind]])
            base_ind += 1
           
    return(keep_cat)

# Create empty catalog to start
tm_cat = obspy.core.event.catalog.Catalog()

# Read in all daily files one by one,
# removing duplicates as we go
input_files = input_folder + '*.xml'
dfiles = glob.glob(input_files)
for d in dfiles:
    with_dupes = obspy.core.event.read_events(d)
    without_dupes = remove_dupes(with_dupes,time_int=time_int)
    tm_cat.extend(without_dupes)

# Write the output catalog!
tm_cat.write(output_file,format="QUAKEML")