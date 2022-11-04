# seismicloud
[![build-and-push](https://github.com/Denolle-Lab/seismicloud/actions/workflows/docker.yml/badge.svg)](https://github.com/Denolle-Lab/seismicloud/actions/workflows/docker.yml)

Workflow for template matching and ML picking with cloud capabilities


## Usage

### Template Matching
For template matching.
    ```
    mpirun -np 9 python scripts/template_matching/distributed_detection.py -c configs/config_zoe.json -n NV -y 2017
    ```

### Machine Learninig Event Detection
1. Setting up data archive and configure file.
2. Create job list.
    ```
    python scripts/picking/create_joblist.py --config configs/config_mldetect.json
    ```
3. Do ML phase picking.
    ```
    mpirun -np 10 python scripts/picking/network_detection.py -c configs/config_mldetect.json -n NV -y 2017
    ```
4. Associate detected phase to events.
    ```
    python scripts/associate/association.py -c configs/config_mldetect.json --year 2017
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
