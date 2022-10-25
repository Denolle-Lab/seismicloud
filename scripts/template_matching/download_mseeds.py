import obspy
import eqcorrscan
import numpy as np
import pandas as pd
import tarfile
import os

############################################
############### INITIALIZE #################
############################################

parser = argparse.ArgumentParser(description="Creating templates from continuous data based on a starting catalog.")
parser.add_argument("-c", "--config", required=True)
args = parser.parse_args()

## load configure file
fconfig = args.config
with open(fconfig, "r") as f:
    config = json.load(f)
    
# Pathnames
templates_path = config["workflow"]["templates_path"] # this should be a .tgz filename
mseed_path = config["workflow"]["mseed_path"]
starting_cat_path = config["workflow"]["starting_cat_path"]

stations = config["workflow"]["stations"]
network = config["workflow"]["network"]

# Read in starting catalog
cat = obspy.core.event.catalog.read_events(starting_cat_path)
print("Read in catalog")

# Get list of stations and channels from QuakeML
picks = [p.picks for p in cat.events]
picks = sum(picks,[])

channels = [p.waveform_id.channel_code[0:2] + '*' for p in picks]
# Toss pressure channels:
channelToRemove = 'HD*'
channels = [value for value in channels if value != channelToRemove]
channel = ",".join((np.unique(channels)).tolist())

# Loop over days and download each (unprocessed) into a directory
path = 'endeavour2/NV/2017/'
t1 = obspy.UTCDateTime(2017,6,1)
t2 = obspy.UTCDateTime(2017,7,1)

client = obspy.clients.fdsn.client.Client('IRIS')

time_bins = np.arange(t1.datetime,t2.datetime,pd.Timedelta(1,'days'))
time_bins = [pd.to_datetime(t) for t in time_bins]

for t in time_bins:

    t1 = obspy.UTCDateTime(t)
    t2 = obspy.UTCDateTime(t + pd.Timedelta(1,'day'))
    
    print(t1)
    for station in stations:
        
        dirname = path + str(t1.julday)
        if not os.path.isdir(dirname):
            os.makedirs(dirname)
            
        pathname = path + str(t1.julday) + '/' + station + '.NV.2017.' + str(t1.julday)
        #pathname = path + t1.strftime("%Y%m%d")+'.mseed'

        st = client.get_waveforms(network,station,'',channel,t1,t2)

        st.write(pathname,format='MSEED')