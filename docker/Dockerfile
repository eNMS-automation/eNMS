FROM ubuntu:latest
RUN apt-get update -y

ENV LANG=C.UTF-8 LC_ALL=C.UTF-8

RUN apt-get update --fix-missing && apt-get install -y wget git bzip2 ca-certificates \
    libglib2.0-0 libxext6 libsm6 libxrender1 \
    git mercurial subversion nano iputils-ping

RUN echo 'export PATH=/opt/conda/bin:$PATH' > /etc/profile.d/conda.sh && \
    wget --quiet https://repo.continuum.io/miniconda/Miniconda2-4.3.27-Linux-x86_64.sh -O ~/miniconda.sh && \
    /bin/bash ~/miniconda.sh -b -p /opt/conda && \
    rm ~/miniconda.sh

RUN apt-get install -y curl grep sed dpkg && \
    TINI_VERSION=`curl https://github.com/krallin/tini/releases/latest | grep -o "/v.*\"" | sed 's:^..\(.*\).$:\1:'` && \
    curl -L "https://github.com/krallin/tini/releases/download/v${TINI_VERSION}/tini_${TINI_VERSION}.deb" > tini.deb && \
    dpkg -i tini.deb && \
    rm tini.deb && \
    apt-get clean

ENV PATH /opt/conda/bin:$PATH

ENV CONDA_ENV_PATH /opt/conda
ENV MY_CONDA_PY3ENV "python34"
ENV CONDA_ACTIVATE "source $CONDA_ENV_PATH/bin/activate $MY_CONDA_PY3ENV"

#Create CONDA
RUN conda create -y -n $MY_CONDA_PY3ENV python=3.4
RUN conda update --quiet --yes conda
RUN echo "alma101" # invalidate the cache
# Setup for ssh onto github

WORKDIR /app/eNMS
ADD requirements.txt /requirements.txt
RUN /bin/bash -c "$CONDA_ACTIVATE && pip install -r /requirements.txt"

#ENTRYPOINT [ "/usr/bin/tini", "--" ]
ENTRYPOINT [ "/bin/bash","-c"]
WORKDIR /app/eNMS/source
CMD [ "source activate python34 && export PORT=8080 && exec python flask_app.py"]
EXPOSE 8080