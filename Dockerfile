FROM r-base:4.1.2

MAINTAINER Adrián Segura Ortiz <adrianseor.99@gmail.com>

libssl-dev

# CRAN packages
RUN R -e "install.packages('BiocManager', repos='http://cran.us.r-project.org', dependencies = TRUE)" \
  && R -e "install.packages('bc3net', repos='http://cran.us.r-project.org', dependencies = TRUE)" \
  && R -e "install.packages('c3net', repos='http://cran.us.r-project.org', dependencies = TRUE)" \
  && R -e "install.packages('gdata', repos='http://cran.us.r-project.org', dependencies = TRUE)" \
  && R -e "install.packages('pROC', repos='http://cran.us.r-project.org', dependencies = TRUE)" \
  && R -e "install.packages('parallel', repos='http://cran.us.r-project.org', dependencies = TRUE)" 

# Bioconductor packages
RUN R -e "BiocManager::install('DREAM4', dependencies = TRUE)" \
  && R -e "BiocManager::install('grndata', dependencies = TRUE)" \
  && R -e "BiocManager::install('minet', dependencies = TRUE)" \
  && R -e "BiocManager::install('GENIE3', dependencies = TRUE)" \
  && R -e "BiocManager::install('CeTF', dependencies = TRUE)" 

COPY . /usr/local/src/
WORKDIR /usr/local/src/

CMD ["R"]