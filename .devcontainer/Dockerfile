# See here for image contents: https://github.com/microsoft/vscode-dev-containers/tree/v0.158.0/containers/python-3/.devcontainer/base.Dockerfile

# [Choice] Python version: 3, 3.9, 3.8, 3.7, 3.6
ARG VARIANT="3"
FROM mcr.microsoft.com/vscode/devcontainers/python:0-${VARIANT}


# [Optional] If your pip requirements rarely change, uncomment this section to add them to the image.
COPY processor/requirements.txt /tmp/pip-tmp/processor_requirements.txt
COPY webserver/requirements.txt /tmp/pip-tmp/webserver_requirements.txt
RUN pip3 --disable-pip-version-check --no-cache-dir install -r /tmp/pip-tmp/processor_requirements.txt -r /tmp/pip-tmp/webserver_requirements.txt \
   && rm -rf /tmp/pip-tmp


# [Optional] Uncomment this section to install additional OS packages.
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends iputils-ping