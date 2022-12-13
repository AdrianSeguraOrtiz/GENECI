FROM r-base:4.1.2

LABEL Khaos Research Group <khaos.uma.es>

MAINTAINER Adrián Segura Ortiz <adrianseor.99@gmail.com>

RUN apt-get update && apt-get install -y \
   build-essential \
   curl \
   libssl-dev \
   libcurl4-openssl-dev \
   libxml2-dev \
   cmake \
   libfontconfig1-dev \
   gfortran \
   libz-dev \
   zlib1g-dev \
   libfftw3-dev \
   libfftw3-doc

# Install BiocManager
RUN R -e "install.packages('BiocManager', repos='http://cran.us.r-project.org')"

# Bioconductor packages
RUN R -e "BiocManager::install('snpStats')"

# CRAN packages
RUN R -e "install.packages('gdata', repos='http://cran.us.r-project.org')" \
   && R -e "install.packages('remotes', repos='http://cran.us.r-project.org')" \
   && R -e "install.packages('data.table', repos='http://cran.us.r-project.org')" \
   && R -e "install.packages('GenomicTools.fileHandler', repos='http://cran.us.r-project.org')" \
   && R -e "install.packages('circlize', repos='http://cran.us.r-project.org')" \
   && R -e "install.packages('stringr', repos='http://cran.us.r-project.org')" \
   && R -e "install.packages('RcppArmadillo', repos='http://cran.us.r-project.org')"

# Install latest version of ggtree
RUN R -e "remotes::install_github('YuLab-SMU/ggtree')"

# Install gMWT and GenomicTools from archive
RUN R -e "url <- 'https://cran.r-project.org/src/contrib/Archive/gMWT/gMWT_1.2.tar.gz'; pkgFile <- 'gMWT_1.2.tar.gz'; download.file(url = url, destfile = pkgFile); install.packages(pkgs=pkgFile, type='source', repos=NULL); unlink(pkgFile)"
RUN R -e "url <- 'https://cran.r-project.org/src/contrib/Archive/GenomicTools/GenomicTools_0.2.9.7.tar.gz'; pkgFile <- 'GenomicTools_0.2.9.7.tar.gz'; download.file(url = url, destfile = pkgFile); install.packages(pkgs=pkgFile, type='source', repos=NULL); unlink(pkgFile)"

# Install CeTF from bioconductor
RUN R -e "BiocManager::install('CeTF')"

COPY components /usr/local/src/components
WORKDIR /usr/local/src/

ENTRYPOINT ["Rscript", "--vanilla", "components/infer_network/PCIT/PCIT.R"]
