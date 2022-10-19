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
   For ML picking:
    ```
    mpirun -np 4 python scripts/phase_picking/network_detection.py -c configs/myconfig.json -n NV -y 2017
    ```
   For template matching:
   ```
    mpirun -np 9 python scripts/template_matching/distributed_detection.py -c configs/myconfig_zoe.json -n NV -y 2017
    ```
