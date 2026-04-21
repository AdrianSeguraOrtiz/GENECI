FROM rocker/r2u:24.04

ARG DYNGEN_VERSION=1.1.1
ENV DEBIAN_FRONTEND=noninteractive \
    R_CRAN_MIRROR=https://cloud.r-project.org \
    DYNGEN_CACHE_DIR=/opt/dyngen-cache

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        git \
        libgit2-dev \
        libglpk-dev \
        r-cran-jsonlite \
        r-cran-remotes \
        unzip \
    && rm -rf /var/lib/apt/lists/*

RUN R -q -e "options(bspm.sudo = TRUE); install.packages(c('assertthat', 'dplyr', 'dynutils', 'ggplot2', 'ggraph', 'GillespieSSA2', 'igraph', 'lmds', 'Matrix', 'patchwork', 'pbapply', 'purrr', 'rlang', 'tibble', 'tidygraph', 'tidyr', 'tidyselect', 'viridis'), repos = Sys.getenv('R_CRAN_MIRROR'))" \
    && R -q -e "options(bspm.sudo = TRUE); remotes::install_version('dyngen', version = Sys.getenv('DYNGEN_VERSION'), repos = Sys.getenv('R_CRAN_MIRROR'), upgrade = 'never', dependencies = FALSE)" \
    && R -q -e "stopifnot(as.character(utils::packageVersion('dyngen')) == Sys.getenv('DYNGEN_VERSION'))"

RUN mkdir -p \"$DYNGEN_CACHE_DIR\" \
    && R -q -e "options(bspm.sudo = TRUE, dyngen_download_cache_dir = Sys.getenv('DYNGEN_CACHE_DIR')); zip <- tempfile(fileext = '.zip'); utils::download.file('https://github.com/dynverse/dyngen/archive/data_files.zip', zip, quiet = TRUE); utils::unzip(zip, exdir = Sys.getenv('DYNGEN_CACHE_DIR'), overwrite = TRUE, junkpaths = TRUE)"

WORKDIR /app

COPY components/generate_data_dev/generators/dyngen/run_simulator.R /app/run_simulator.R

RUN chmod +x /app/run_simulator.R

ENTRYPOINT ["Rscript", "/app/run_simulator.R", "--request", "/work/request/simulator-run-request.json", "--output-dir", "/work/out"]
