FROM r-base:4.3.3

ARG TIGRESS_REF=de70cd256840b08a64f0471c0c63dbb01314b35a

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    build-essential \
    gfortran \
    git \
    libcurl4-openssl-dev \
    libssl-dev \
    libxml2-dev \
    r-cran-jsonlite \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN R -q -e "install.packages(c('lars','remotes'), repos='https://cloud.r-project.org')" \
  && R -q -e "remotes::install_github('jpvert/tigress@${TIGRESS_REF}')"

COPY run_tool.sh /app/run_tool.sh
COPY run_tool.R /app/run_tool.R

RUN chmod +x /app/run_tool.sh

ENTRYPOINT ["/app/run_tool.sh"]
