# seismicloud
[![DOI](https://zenodo.org/badge/540089839.svg)](https://zenodo.org/badge/latestdoi/540089839) [![build-and-push](https://github.com/Denolle-Lab/seismicloud/actions/workflows/docker.yml/badge.svg)](https://github.com/Denolle-Lab/seismicloud/actions/workflows/docker.yml) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) 

Workflow for template matching and ML picking with cloud capabilities.

This GitHub accompanies the Krauss et al., 2023 manuscript in Seismica: ["Seismology in the cloud: guidance for the individual researcher"](https://seismica.library.mcgill.ca/article/view/979)


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
5. The data and code used to make Figures 4-6 in the manuscript can be found in /figures.

#### Building the Docker image:
For this repository, this currently happens automatically with GitHub Actions with every commit to the 'main' branch.
This is because we have set up the build of a Docker image through GitHub continuous integration. The script that builds and pushes the Docker image on each commit can be found in .github/workflows/docker.yml. The progress of the build for each commit can be viewed on the "Actions" page of the repository.

The name of the Docker image built from this repository is ghcr.io/denolle-lab/seismicloud:latest

Alternatively, a Docker image built using an older commit is named by the commit ID: ghcr.io/denolle-lab/seismicloud:86679bd

For guidance on activating this same workflow on another repository, see:
https://docs.github.com/en/actions/publishing-packages/publishing-docker-images


## Local code execution
The code can either be run locally in the python environment if the repository is cloned locally, as demonstrated in tutorials/, or can be run through the Docker container image.

<img width="463" alt="image" src="https://github.com/Denolle-Lab/seismicloud/assets/62721445/ff093479-49f1-447d-950b-24e715bbcd99">

1. Create a config file in json format with your local specifications and pathnames, and if necessary, download waveforms and make templates. See tutorials/NotebookS1 for full documentation, and configs/test_config.json as an example.
2. Run earthquake detection in parallel using either template matching or EQTransformer. See tutorials/NotebookS2.
3. Outprocess detections to yield a final earthquake catalog in QuakeML format. See tutorials/NotebookS2.
    

#### Run with Docker
The same commands demonstrated in tutorials/NotebookS2 can be run from within the Docker container image built by Github actions. 

On a computer with Docker installed, the following command can be run to open an interactive bash shell *inside* the Docker image.
Since our workflow set-up requires a local directory of waveforms that is not within the Docker image/stored on the GitHub, you must mount the local directory to the Docker image on start-up. This is done by passing the -v argument, which mounts a volume. In the example below, you can access the /localdirectory/waveformdata directory from within the Docker image using the pathname /tmp/data/data. 

```
docker run -it --rm -v /localdirectory/waveformdata:/tmp/data/data ghcr.io/denolle-lab/seismicloud:latest
```

To launch docker with jupyter lab, use the command below. Port 8888 forwarding to 80 (http) is enabled. Token is specified as `scoped` when logging into the lab. Change `/localdirectory/waveformdata` accordingly to match where your data is.
```
docker run --rm -p 80:8888 -v /localdirectory/waveformdata:/tmp/data/data ghcr.io/denolle-lab/seismicloud:latest jupyter lab --no-browser --ip=0.0.0.0  --IdentityProvider.token=scoped
```

The -it argument specifies to create an interactive bash shell in the container, and the --rm argument automatically removes the container when it exits.

From within the container, you can then proceed to run the same commands demonstrated in tutorials/NotebookS2. Make sure you have a config file that points the scripts to the mounted volume correctly! 

## Run on Azure
<img width="492" alt="image" src="https://github.com/Denolle-Lab/seismicloud/assets/62721445/34216750-b0cc-4f31-839a-57819f970641">

The user will need to first initiate an Azure account (see tutorials/TutorialS1), an Azure storage container with waveform data (see tutorials/TutorialS2), and an Azure Batch Pool (see tutorials/TutorialS3) through the Azure desktop portal.

The user will also need a Docker image structured in the same way as this repository, with a config file that properly points the scripts to the waveform data, which will be mounted to the Azure Batch Pool as a tmp/ directory. See configs/config_batch_test.json as an example.

Once the above is accomplished, the user can send tasks to the Batch Pool following tutorials/TutorialS4.


