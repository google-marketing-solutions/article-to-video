FROM node:23.8.0-bookworm-slim

ENV PYTHONUNBUFFERED 1
ENV MSGPACK_PUREPYTHON 1

WORKDIR /usr/src/app

RUN mkdir output

RUN apt-get update && apt-get install -y apt-utils

# Dependencies
RUN apt-get update && apt-get install -y build-essential gcc g++ gfortran libopenblas-dev liblapack-dev pkg-config curl python3 python3-pip
RUN apt-get update && apt-get install -y imagemagick ffmpeg

# Required for ImageMagick to work with moviepy on Ubuntu
# https://github.com/Zulko/moviepy/issues/693#issuecomment-355587113
RUN sed -i.bak '/<policy domain="path" rights="none" pattern="@\*"\/>/d' /etc/ImageMagick-6/policy.xml

COPY requirements.txt ./
RUN pip install --break-system-packages --no-deps --require-hashes -r requirements.txt

COPY . ./

# Build the UI files
WORKDIR /usr/src/app/ui
RUN npm install
RUN node_modules/@angular/cli/bin/ng.js build

WORKDIR /usr/src/app

# Run the web service on container startup.
# Use gunicorn webserver with one worker process and 8 threads.
# For environments with multiple CPU cores, increase the number of workers
# to be equal to the cores available.
# Timeout is set to 0 to disable the timeouts of the workers to allow Cloud Run to handle instance scaling.
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 video_generation_from_articles:app