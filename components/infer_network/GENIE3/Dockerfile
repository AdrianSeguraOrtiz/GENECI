FROM python:3.10.2

LABEL Khaos Research Group <khaos.uma.es>

MAINTAINER Adrián Segura Ortiz <adrianseor.99@gmail.com>

RUN apt-get update && apt-get install -y \
   curl \
   libssl-dev \
   libcurl4-openssl-dev \
   libxml2-dev

# Update pip command
RUN pip install --upgrade pip

# Install packages
RUN pip install typer pandas arboreto 

COPY . /usr/local/src/
WORKDIR /usr/local/src/

ENTRYPOINT ["python", "components/infer_network/GENIE3/GENIE3.py"]
