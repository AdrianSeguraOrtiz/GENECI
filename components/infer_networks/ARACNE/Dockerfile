FROM r-base:4.1.2

LABEL Khaos Research Group <khaos.uma.es>

MAINTAINER Adrián Segura Ortiz <adrianseor.99@gmail.com>

RUN apt-get update && apt-get install -y \
   curl \
   libssl-dev \
   libcurl4-openssl-dev \
   libxml2-dev

# CRAN packages
RUN R -e "install.packages('BiocManager', repos='http://cran.us.r-project.org')"

# Bioconductor packages
RUN R -e "BiocManager::install('minet')"


COPY . /usr/local/src/
WORKDIR /usr/local/src/

ENTRYPOINT ["Rscript", "--vanilla", "ARACNE.R"]
