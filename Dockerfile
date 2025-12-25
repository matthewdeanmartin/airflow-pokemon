# User requested Python 3.14
FROM python:3.14

# Set Airflow Home to a directory we can easily mount volumes to
ENV AIRFLOW_HOME=/opt/airflow
ENV AIRFLOW__CORE__SIMPLE_AUTH_MANAGER_ALL_ADMINS=1
ENV AIRFLOW__CORE__SIMPLE_AUTH_MANAGER_USERS=admin:admin

# Install system deps for lxml/pandas if wheels aren't perfect for 3.14 yet
RUN apt-get update && apt-get install -y --no-install-recommends \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Install Airflow and scraping libraries
# We disable the cache to keep the image small
RUN pip install --no-cache-dir "apache-airflow>=2.10.0" \
    "flask-appbuilder" \
    "pandas" \
    "requests" \
    "lxml" \
    "pydantic>=2.0"

# Set the working directory
WORKDIR $AIRFLOW_HOME

# Expose the webserver port
EXPOSE 8080

# Run Airflow in standalone mode (Webserver + Scheduler + Triggerer)
CMD ["airflow", "standalone"]