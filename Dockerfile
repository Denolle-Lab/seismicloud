# syntax = docker/dockerfile:1.4
ARG MAMBA_VERSION=0.27.0

# https://github.com/mamba-org/micromamba-docker
FROM docker.io/mambaorg/micromamba:${MAMBA_VERSION} as app

ENV SHELL=/bin/bash \
    LANG=C.UTF-8  \
    LC_ALL=C.UTF-8 \ 
    # NOTE: this is needed to build on non-GPU machine
    CONDA_OVERRIDE_CUDA="11.2"

# chown for default 'mambauser' permissions
COPY --link --chown=1000:1000 environment.yml* /tmp/env.yml

RUN --mount=type=cache,target=/opt/conda/pkgs <<eot
    micromamba install -y -n base -f /tmp/env.yml
    micromamba clean --all --yes
eot

# Copy all repository files
COPY --link --chown=1000:1000 ./ /tmp

# do we need to add command in this docker image?
