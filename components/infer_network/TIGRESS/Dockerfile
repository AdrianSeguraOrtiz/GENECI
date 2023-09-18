FROM r-base:4.1.2

LABEL Khaos Research Group <khaos.uma.es>

LABEL Adrián Segura Ortiz <adrianseor.99@gmail.com>

RUN apt-get update && apt-get install -y \
   curl \
   libssl-dev \
   libcurl4-openssl-dev \
   libxml2-dev \
   libfontconfig1-dev \
   libharfbuzz-dev \
   libfribidi-dev \
   libfreetype6-dev \
   libpng-dev \
   libtiff5-dev \
   libjpeg-dev

# Install packages
RUN R -e "install.packages('gdata', repos='http://cran.us.r-project.org')"
RUN R -e "install.packages('devtools', repos='http://cran.us.r-project.org');"
RUN R -e "devtools::install_github('jpvert/tigress')"

COPY components /usr/local/src/components
WORKDIR /usr/local/src/

ENTRYPOINT ["Rscript", "--vanilla", "components/infer_network/TIGRESS/TIGRESS.R"]
