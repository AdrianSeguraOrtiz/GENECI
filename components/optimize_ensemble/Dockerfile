FROM openjdk:13-buster

LABEL Khaos Research Group <khaos.uma.es>

MAINTAINER Adrián Segura Ortiz <adrianseor.99@gmail.com>

RUN apt-get update && apt-get install -y \
   curl \
   libssl-dev \
   libcurl4-openssl-dev \
   libxml2-dev

# create a non-root user named nonroot, 
# give them the password "nonroot" put them in the sudo group
RUN useradd -d /home/nonroot -m -s /bin/bash nonroot && echo "nonroot:nonroot" | chpasswd && adduser nonroot sudo

# start working in the "nonroot" home directory
COPY . /usr/local/src/
WORKDIR /usr/local/src/

# Make the files owned by nonroot
RUN chown -R nonroot:nonroot /home/nonroot

# Switch to your new user in the docker image
USER nonroot

ENTRYPOINT ["java",  "-cp",  "EAGRN-JMetal/target/AEGRN-1.0-SNAPSHOT-jar-with-dependencies.jar", "eagrn.GRNRunner"]
