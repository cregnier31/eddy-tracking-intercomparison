FROM mambaorg/micromamba:2.3.0-alpine3.19

ENV DATE_START="2025-01-01"
ENV DATE_END="2025-01-20"
ENV XMIN=-19
ENV XMAX=5
ENV YMIN=26
ENV YMAX=56
ENV MODE=NRT
ENV MODEL_ACRO=GLO
ENV OBS_ACRO=AVISO
ENV DATA_DIR=/output-data

COPY --chown=$MAMBA_USER:$MAMBA_USER env.yaml /tmp/env.yaml
COPY --chown=$MAMBA_USER:$MAMBA_USER eddy_detect /tmp/eddy_detect/
COPY --chown=$MAMBA_USER:$MAMBA_USER eddy_diags /tmp/eddy_diags/
COPY --chown=$MAMBA_USER:$MAMBA_USER eddy_load /tmp/eddy_load/
COPY --chown=$MAMBA_USER:$MAMBA_USER eddy_run /tmp/eddy_run/

RUN micromamba install -y -n base -c conda-forge git=2.49.0
RUN micromamba install -y -n base -f /tmp/env.yaml && \
    micromamba clean --all --yes

ARG MAMBA_DOCKERFILE_ACTIVATE=1

RUN git clone https://github.com/svangennip/py-eddy-tracker.git
RUN cd py-eddy-tracker && pip install -e .

WORKDIR /tmp

CMD [ "bash", "-c", "python eddy_run/__main__.py ${DATE_START} ${DATE_END} ${XMIN} ${XMAX} ${YMIN} ${YMAX} ${MODE} ${MODEL_ACRO} ${OBS_ACRO} ${DATA_DIR}" ]
