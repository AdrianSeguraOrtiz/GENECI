FROM python:3.10.2

LABEL Khaos Research Group <khaos.uma.es>

LABEL Adrián Segura Ortiz <adrianseor.99@gmail.com>

# Update pip command
RUN pip install --upgrade pip

# Install packages
RUN pip install typer pandas inferelator

COPY components /usr/local/src/components
WORKDIR /usr/local/src/

ENTRYPOINT ["python", "components/infer_network/INFERELATOR/INFERELATOR.py"]