import datetime
import json
import argparse
import obspy
import eqcorrscan
import numpy as np
import pandas as pd
import tarfile
import os

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

# Parameters from config
path = config["mseed_download"]["mseed_path"]
stations = config["mseed_download"]["stations"]
network = config["mseed_download"]["network"]
channel = config["mseed_download"]["channels"]
resamp = config["mseed_download"]["resamp"]
samp_rate = config["mseed_download"]["samp_rate"]

# Add network to pathname
path = path + network + '/'

# Loop over days and download each (unprocessed) into a directory
t1 = config["mseed_download"]["t1"]
t1 = datetime.datetime.strptime(t1, "%Y,%m,%d,%H,%M,%S")
t2 = config["mseed_download"]["t2"]
t2 = datetime.datetime.strptime(t2, "%Y,%m,%d,%H,%M,%S")

client = obspy.clients.fdsn.client.Client("IRIS")

time_bins = np.arange(t1, t2, pd.Timedelta(1, "days"))
time_bins = [pd.to_datetime(t) for t in time_bins]

for t in time_bins:

    t1 = obspy.UTCDateTime(t)
    t2 = obspy.UTCDateTime(t + pd.Timedelta(1, "day"))

    print(t1)
    for station in stations:

        dirname = path + str(t1.year) + '/' + str(t1.julday)
        if not os.path.isdir(dirname):
            os.makedirs(dirname)

        
        pathname = path + str(t1.year) + '/' + str(t1.julday) + "/" + station + "." + network + "." + str(t1.year) + "." + str(t1.julday)

#        try:
        st = client.get_waveforms(network, station, "", channel, t1, t2)
        if resamp == "True":
            st.resample(samp_rate)
        st.write(pathname, format="MSEED")
        print("Written!")
#        except:
#            print("Did not work for " + str(t1.julday))
