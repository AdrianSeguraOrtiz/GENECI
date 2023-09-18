FROM openjdk:17-buster

LABEL Khaos Research Group <khaos.uma.es>

LABEL Adrián Segura Ortiz <adrianseor.99@gmail.com>

WORKDIR /usr/local/src
COPY ./EAGRN-JMetal/target/AEGRN-1.0-SNAPSHOT-jar-with-dependencies.jar ./AEGRN-1.0-SNAPSHOT-jar-with-dependencies.jar

RUN echo "total_mem=\$(free --kilo | awk '/^Mem:/ {print \$2}'); xmx=\$((total_mem * 85 / 100)); java -Xmx\${xmx}k -cp AEGRN-1.0-SNAPSHOT-jar-with-dependencies.jar eagrn.GRNRunner \$@ && chmod -R 777 ./tmp-*" > myScript.sh
ENTRYPOINT ["bash", "myScript.sh"]