FROM r-base:4.1.2

LABEL Khaos Research Group <khaos.uma.es>

MAINTAINER Adrián Segura Ortiz <adrianseor.99@gmail.com>

RUN apt-get update && apt-get install -y \
   curl \
   libssl-dev \
   libcurl4-openssl-dev \
   libxml2-dev \
   libgdal-dev

# CRAN packages
RUN R -e "install.packages('BiocManager', repos='http://cran.us.r-project.org')" \
   && R -e "install.packages('gdata', repos='http://cran.us.r-project.org')" \
   && R -e "install.packages('sqldf', repos='http://cran.us.r-project.org')" \
   && R -e "install.packages('pROC', repos='http://cran.us.r-project.org')" \
   && R -e "install.packages('parallel', repos='http://cran.us.r-project.org')" \
   && R -e "install.packages('dplyr', repos='http://cran.us.r-project.org')" \
   && R -e "install.packages('igraph', repos='http://cran.us.r-project.org')" \
   && R -e "install.packages('rlang', repos='http://cran.us.r-project.org')" \
   && R -e "install.packages('entropy', repos='http://cran.us.r-project.org')" \
   && R -e "install.packages('modEvA', repos='http://cran.us.r-project.org')" \
   && R -e "install.packages('reshape', repos='http://cran.us.r-project.org')" \
   && R -e "install.packages('ROCR', repos='http://cran.us.r-project.org')" \
   && R -e "install.packages('readr', repos='http://cran.us.r-project.org')" \
   && R -e "install.packages('tidyr', repos='http://cran.us.r-project.org')"

# Bioconductor packages
RUN R -e "BiocManager::install('minet')" \
   && R -e "BiocManager::install('Rgraphviz')"

COPY components /usr/local/src/components
WORKDIR /usr/local/src/

ENTRYPOINT ["Rscript", "--vanilla", "components/infer_network/MEOMI/MEOMI.R"]
