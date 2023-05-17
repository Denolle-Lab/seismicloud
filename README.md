# seismicloud
[![build-and-push](https://github.com/Denolle-Lab/seismicloud/actions/workflows/docker.yml/badge.svg)](https://github.com/Denolle-Lab/seismicloud/actions/workflows/docker.yml)

Workflow for template matching and ML picking with cloud capabilities.

This GitHub accompanies the Krauss et al., 2023 manuscript: "Seismology in the cloud for template matching and machine-learning earthquake detection" (in prep).


## Usage

This repository is set up to be automatically built as a Docker container image following the included Dockerfile.

Although anyone could run the Docker image built from this repository following the commands below, the config files (json format) in this repository are written with specific file path configurations to run on the author's local and cloud infrastructure. 

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

2. We include tutorials in Jupyter Notebook format to demonstrate the running of the workflow:
- tutorials/NotebookS1.ipynb: set-up of the config file, how to download waveform data, and create templates.
- tutorials/NotebookS2.ipynb: how to locally run earthquake detection through both template matching and EQTransformer in parallel.
- tutorials/NotebookS3.ipynb: how to post-process the detections from both template matching and EQTransformer into QuakeML files.
- tutorials/NotebookS4.ipynb: how to connect to a pre-built Azure Batch Pool and send tasks to run earthquake detection through both template matching and EQTransformer. 

3. We include tutorials in PDF format to demonstrate how to construct cloud resources through the Azure desktop portal:
- tutorials/TutorialS1.pdf: getting set-up on the cloud
- tutorials/TutorialS2.pdf: creating and writing to a Blob storage container
- tutorials/TutorialS3.pdf: creating a Batch Pool of virtual machines/nodes

4. The python environment needed to run the scripts is described in docker.yml. We note that the mpi4py package requires a local installation of MPI.
5. The file to build the container image with Docker is Dockerfile.

#### Building the Docker image:
Note: this currently happens automatically with GitHub Actions with every commit to the 'main' branch.
```
docker buildx build . -t seismicloud:latest
```
?? Can we add a link here to help people get the github action going??

## Local code execution
The code can either be run locally in the python environment if the repository is cloned locally, as demonstrated in tutorials/, or can be run through the Docker container image.

<img width="463" alt="image" src="https://github.com/Denolle-Lab/seismicloud/assets/62721445/ff093479-49f1-447d-950b-24e715bbcd99">

1. Create a config file in json format with your local specifications and pathnames, and if necessary, download waveforms and make templates. See tutorials/NotebookS1 for full documentation, and configs/test_config.json as an example.
2. Run earthquake detection in parallel using either template matching or EQTransformer. See tutorials/NotebookS2.
3. Outprocess detections to yield a final earthquake catalog in QuakeML format. See tutorials/NotebookS2.
    

#### Run with Docker
The same commands demonstrated in tutorials/NotebookS2 can be run from within the Docker container image built by Github actions (as long as the local computer has Docker installed) by appending several statements to a python command. The commands to pull the image and then an example of how to run a script within them are seen below:
?? How to pull properly??
```
docker run -it --rm ghcr.io/denolle-lab/seismicloud:latest python --version
docker run -it --rm ghcr.io/denolle-lab/seismicloud:latest python /tmp/scripts/picking/create_joblist.py -c /tmp/configs/myconfig.json
```

## Run on Azure
<img width="492" alt="image" src="https://github.com/Denolle-Lab/seismicloud/assets/62721445/34216750-b0cc-4f31-839a-57819f970641">

The user will need to first initiate an Azure account (see tutorials/TutorialS1), an Azure storage container with waveform data (see tutorials/TutorialS2), and an Azure Batch Pool (see tutorials/TutorialS3) through the Azure desktop portal.

The user will also need a Docker image structured in the same way as this repository, with a config file that properly points the scripts to the waveform data, which will be mounted to the Azure Batch Pool as a tmp/ directory. See configs/config_batch_test.json as an example.

Once the above is accomplished, the user can send tasks to the Batch Pool following tutorials/TutorialS4.


