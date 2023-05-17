# seismicloud
[![build-and-push](https://github.com/Denolle-Lab/seismicloud/actions/workflows/docker.yml/badge.svg)](https://github.com/Denolle-Lab/seismicloud/actions/workflows/docker.yml)

Workflow for template matching and ML picking with cloud capabilities.

This GitHub accompanies the Krauss et al., 2023 manuscript: "Seismology in the cloud for template matching and machine-learning earthquake detection" (in prep).


## Usage

This repository is set up to be automatically built as a container image following the included Dockerfile, docker.yml.

Although anyone could run commands through the Docker image built from this repository following the commands below, the config files (json format) in this repository are written with specific file path configurations to run on the author's local and cloud infrastructure. 

We therefore suggest that users copy the scripts from this repository into their own new repository, modify the config files, and initiate a Github action on that repository to form their own Docker image in which to run the codes.

## Contents

1. The folders that pertain to the running of the workflow are the following:
- configs/
- data/
- jobs/
- logs/

For running on local (not cloud):
- scripts/

For running on Azure cloud batch Pools:
- batch_scripts/

2. We also include tutorials in Jupyter Notebook format to demonstrate the running of the workflow:
- tutorials/NotebookS1: 
- tutorials/NotebookS2:
- tutorials/NotebookS3:
- tutorials/NotebookS4:

3. The file that describes both the python environment and is used by Docker to create a container image of the repository is docker.yml 




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



### Run on Azure


