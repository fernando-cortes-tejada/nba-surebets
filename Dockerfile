FROM apache/airflow:2.10.3-python3.11

USER root
RUN apt-get update \
 && apt-get install -y --no-install-recommends wget \
 && wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
 && apt-get install -y ./google-chrome-stable_current_amd64.deb \
 && rm google-chrome-stable_current_amd64.deb \
 && rm -rf /var/lib/apt/lists/*

USER airflow
WORKDIR /opt/airflow
COPY --chown=airflow:root pyproject.toml requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=airflow:root surebets ./surebets
ENV PYTHONPATH=/opt/airflow
