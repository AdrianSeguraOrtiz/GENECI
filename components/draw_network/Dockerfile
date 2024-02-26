FROM python:3.10.2

LABEL Khaos Research Group <khaos.uma.es>

LABEL Adrián Segura Ortiz <adrianseor.99@gmail.com>

RUN apt-get update && apt-get install -y \
   curl \
   libssl-dev \
   libcurl4-openssl-dev \
   libxml2-dev

# Update pip command
RUN pip install --upgrade pip

# Install packages
RUN pip install typer networkx matplotlib plotly scipy d3graph pyvis seaborn scikit-learn

COPY components /usr/local/src/components
WORKDIR /usr/local/src/

ENTRYPOINT ["python", "components/draw_network/draw_network.py"]
