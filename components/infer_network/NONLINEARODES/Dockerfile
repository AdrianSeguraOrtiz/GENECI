FROM python:3.6.0

LABEL Khaos Research Group <khaos.uma.es>

LABEL Adrián Segura Ortiz <adrianseor.99@gmail.com>

# Update pip command
RUN pip install --upgrade pip

# Install packages
RUN pip install typer pandas xgboost==0.82 scikit-learn==0.24.2 numpy==1.16.3

COPY components /usr/local/src/components
WORKDIR /usr/local/src/

ENTRYPOINT ["python", "components/infer_network/NONLINEARODES/NONLINEARODES.py"]