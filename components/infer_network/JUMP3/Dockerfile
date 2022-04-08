FROM mathworks/matlab:r2022a

LABEL Khaos Research Group <khaos.uma.es>

MAINTAINER Adrián Segura Ortiz <adrianseor.99@gmail.com>

RUN apt-get update && apt-get install -y \
   curl \
   libssl-dev \
   libcurl4-openssl-dev \
   libxml2-dev

COPY . /usr/local/src/
WORKDIR /usr/local/src/

ENTRYPOINT ["matlab", "-batch", "JUMP3"]
