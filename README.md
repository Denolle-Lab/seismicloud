# seismicloud
Workflow for template matching and ML picking with cloud capabilities


## Usage

### Template Matching
TODO 

### Machine Learninig Event Detection
1. Setting up data archive and configure file.
2. Create job list.
    ```
    python scripts/create_joblist.py --config configs/myconfig.json
    ```
3. Submit jobs.
    ```
    mpirun -np 4 python scripts/network_detection.py -c configs/myconfig.json -n NV -y 2017
    ```
