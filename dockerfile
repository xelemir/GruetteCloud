# Dockerfile

# Set the base image
FROM python:3.7

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install any dependencies
RUN pip install -r requirements.txt

# Copy the content of the local src directory to the working directory
COPY src/ .

# Specify the command to run on container start
CMD [ "gunicorn", "-b", ":5000", "app.flask_app:flask_app" ]
