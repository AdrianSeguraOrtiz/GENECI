FROM r-base:4.1.2

MAINTAINER Adrián Segura Ortiz <adrianseor.99@gmail.com>

RUN apt-get update && apt-get install -y \
   curl \
   libssl-dev \
   libcurl4-openssl-dev \
   libxml2-dev \
   cmake

# CRAN packages
RUN R -e "install.packages('BiocManager', repos='http://cran.us.r-project.org')" \
  && R -e "install.packages('bc3net', repos='http://cran.us.r-project.org')" \
  && R -e "install.packages('c3net', repos='http://cran.us.r-project.org')" \
  && R -e "install.packages('gdata', repos='http://cran.us.r-project.org')" \
  && R -e "install.packages('pROC', repos='http://cran.us.r-project.org')" \
  && R -e "install.packages('parallel', repos='http://cran.us.r-project.org')" 

# Bioconductor packages
RUN R -e "BiocManager::install('DREAM4')" \
  && R -e "BiocManager::install('grndata')" \
  && R -e "BiocManager::install('minet')" \
  && R -e "BiocManager::install('GENIE3')" \
  && R -e "BiocManager::install('CeTF')" 

COPY . /usr/local/src/
WORKDIR /usr/local/src/

CMD ["R"]