# Use an official Python runtime as a parent image
FROM python:3.10.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app/

# Install the dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expose port 8000 for the app
EXPOSE 800

# Define the command to run the application
CMD ["python", "manage.py", "runserver", "0.0.0.0:800"]

