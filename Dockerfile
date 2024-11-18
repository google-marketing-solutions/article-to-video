FROM python:3.13.0-slim

ENV PYTHONUNBUFFERED 1

WORKDIR /usr/src/app

RUN mkdir output

RUN apt-get update && apt-get install -y apt-utils
RUN pip install --upgrade pip

# Dependencies for scipy
RUN apt-get update && apt-get install -y build-essential gcc g++ gfortran libopenblas-dev liblapack-dev pkg-config curl

# NodeJS
RUN apt-get update && apt-get install -y nodejs npm
RUN npm install -g n
RUN n stable

RUN apt-get update && apt-get install -y ffmpeg

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY . ./

# Build the UI files
WORKDIR /usr/src/app/ui
RUN npm install -g @angular/cli
RUN npm install
RUN ng build

WORKDIR /usr/src/app

# Run the web service on container startup.
# Use gunicorn webserver with one worker process and 8 threads.
# For environments with multiple CPU cores, increase the number of workers
# to be equal to the cores available.
# Timeout is set to 0 to disable the timeouts of the workers to allow Cloud Run to handle instance scaling.
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 video_generation_from_articles:app