FROM jupyter/scipy-notebook:latest
RUN mamba install -c conda-forge geemap leafmap geopandas localtileserver osmnx -y && \
    pip install -U geemap && \
    fix-permissions "${CONDA_DIR}" && \
    fix-permissions "/home/${NB_USER}"

RUN mkdir ./examples
COPY /docs/notebooks ./examples/notebooks
COPY /docs/workshops ./examples/workshops
COPY /examples/data ./examples/data
COPY /examples/README.md ./examples/README.md

ENV PROJ_LIB='/opt/conda/share/proj'

USER root
RUN chown -R ${NB_UID} ${HOME}
USER ${NB_USER}