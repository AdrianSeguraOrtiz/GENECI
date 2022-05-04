FROM openjdk:13-buster

LABEL Khaos Research Group <khaos.uma.es>

MAINTAINER Adrián Segura Ortiz <adrianseor.99@gmail.com>

RUN apt-get update && apt-get install -y \
   curl \
   libssl-dev \
   libcurl4-openssl-dev \
   libxml2-dev

RUN addgroup --system --gid 1001 appuser
RUN adduser --system --uid 1001 --group appuser
RUN chown -R appuser:appuser /opt
RUN mkdir /logs && chown -R appuser:appuser /logs
USER appuser

COPY . /usr/local/src/
WORKDIR /usr/local/src/

ENTRYPOINT ["java",  "-cp",  "EAGRN-JMetal/target/AEGRN-1.0-SNAPSHOT-jar-with-dependencies.jar", "eagrn.GRNRunnerSingleThread"]
