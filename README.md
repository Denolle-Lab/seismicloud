# seismicloud
[![build-and-push](https://github.com/Denolle-Lab/seismicloud/actions/workflows/docker.yml/badge.svg)](https://github.com/Denolle-Lab/seismicloud/actions/workflows/docker.yml)

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
   For ML phase picking:
    ```
    mpirun -np 4 python scripts/picking/network_detection.py -c configs/myconfig.json -n NV -y 2017
    ```
   For template matching:
    ```
    mpirun -np 9 python scripts/template_matching/distributed_detection.py -c configs/myconfig_zoe.json -n NV -y 2017
    ```

### Run with Docker
```
docker run -it --rm ghcr.io/denolle-lab/seismicloud:latest python --version
docker run -it --rm ghcr.io/denolle-lab/seismicloud:latest python /tmp/scripts/picking/create_joblist.py -c /tmp/configs/myconfig.json
```


### Build Docker image:
Note: this currently happens automatically with GitHub Actions with every commit to the 'main' branch
```
docker buildx build . -t seismicloud:latest
```

### Run on AWS

TODO

### Run on Azure

TODO
