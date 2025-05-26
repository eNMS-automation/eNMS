# Set the base image
FROM python:3.9

# Set environment variables
ENV UNSEAL_VAULT_KEY1=key1
ENV UNSEAL_VAULT_KEY2=key2
# Add more environment variables if needed...

# Install required packages
RUN apt-get update && apt-get install -y git supervisor wget

# Create and set work directory
WORKDIR /eNMS


# Copy only the requirements files first to cache dependencies
COPY build/requirements/requirements.txt /tmp/requirements.txt
COPY build/requirements/requirements_db.txt /tmp/requirements_db.txt
COPY build/requirements/requirements_dev.txt /tmp/requirements_dev.txt
COPY build/requirements/requirements_optional.txt /tmp/requirements_optional.txt

# Install Python dependencies
RUN pip install -r /tmp/requirements.txt
RUN pip install -r /tmp/requirements_db.txt
RUN pip install -r /tmp/requirements_dev.txt
RUN pip install -r /tmp/requirements_optional.txt

# Copy the local directory content into the container
COPY . /eNMS

# Set the command to run when the container starts
WORKDIR /eNMS
CMD ["gunicorn", "-c", "gunicorn.py", "eNMS.server:server"]
