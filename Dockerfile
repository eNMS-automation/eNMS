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

# Clone the eNMS repository
#RUN git clone https://github.com/eNMS-automation/eNMS.git .

# Copy the local directory content into the container
COPY . /eNMS

# Change to the eNMS directory and install Python requirements
WORKDIR /eNMS
RUN pip install -r build/requirements/requirements.txt

# Download the latest release of eNMS
#RUN wget https://github.com/afourmy/eNMS/archive/refs/tags/v4.7.tar.gz && \
#    tar --strip-components=1 -xzf v4.2.tar.gz -C /eNMS && \
#    rm v4.7.tar.gz

# Install gunicorn
RUN pip install gunicorn

# Install correct version of Flask_WTF
RUN pip3 install flask_wtf==v1.0.1

# Install correct version of werkzueg
RUN pip install werkzeug===2.2.2

# Add a command to list the contents of /eNMS
#RUN ls -l /eNMS

# Set the command to run when the container starts
WORKDIR /eNMS
CMD ["gunicorn", "-c", "gunicorn.py", "eNMS.server:server"]
