FROM rocker/r-ver:4.4.1

ARG MINET_VERSION=3.68.0
ARG MINET_TARBALL=https://bioconductor.org/packages/3.22/bioc/src/contrib/minet_3.68.0.tar.gz

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    build-essential \
    gfortran \
    libcurl4-openssl-dev \
    libssl-dev \
    libxml2-dev \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN R -q -e "install.packages(c('jsonlite','infotheo'), repos='https://cloud.r-project.org')" \
  && R -q -e "install.packages('${MINET_TARBALL}', repos=NULL, type='source')" \
  && R -q -e "stopifnot(as.character(utils::packageVersion('minet')) == '${MINET_VERSION}')"

COPY run_tool.sh /app/run_tool.sh
COPY run_tool.R /app/run_tool.R

RUN chmod +x /app/run_tool.sh

ENTRYPOINT ["/app/run_tool.sh"]
