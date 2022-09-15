FROM openjdk:17-buster

LABEL Khaos Research Group <khaos.uma.es>

MAINTAINER Adrián Segura Ortiz <adrianseor.99@gmail.com>

WORKDIR /usr/local/src
COPY ./EAGRN-JMetal/target/AEGRN-1.0-SNAPSHOT-jar-with-dependencies.jar ./AEGRN-1.0-SNAPSHOT-jar-with-dependencies.jar

RUN echo 'java -cp AEGRN-1.0-SNAPSHOT-jar-with-dependencies.jar eagrn.WeightedConfRunner $@ && chmod -R 777 ./tmp' > myScript.sh
ENTRYPOINT ["bash", "myScript.sh"]