FROM julia:1.8.5

LABEL Khaos Research Group <khaos.uma.es>

MAINTAINER Adrián Segura Ortiz <adrianseor.99@gmail.com>

# Install NetworkInference package
RUN julia -e 'using Pkg; Pkg.add("NetworkInference")'

COPY components /usr/local/src/components
WORKDIR /usr/local/src/

ENTRYPOINT ["julia", "components/infer_network/PIDC/PIDC.jl"]