FROM ubuntu:20.04
WORKDIR /code

ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC
RUN apt-get update && apt-get install -y git make build-essential \ 
    python3 python3-pip python3-distutils python3-dev \ 
    zlib1g-dev libtiff5-dev libjpeg8-dev libopenjp2-7-dev \
    libfreetype6-dev liblcms2-dev libwebp-dev tcl8.6-dev tk8.6-dev python3-tk \
    libharfbuzz-dev libfribidi-dev libxcb1-dev

RUN git clone https://github.com/hzeller/rpi-rgb-led-matrix.git
RUN cd rpi-rgb-led-matrix && make build-python PYTHON=$(which python3)
RUN cd rpi-rgb-led-matrix && make install-python PYTHON=$(which python3)
RUN mkdir /code/app-client

COPY ./requirements.txt /code/requirements.txt

RUN python3 -m pip install --upgrade pip
RUN pip3 install --force-reinstall pillow
# https://stackoverflow.com/questions/69624327/failed-building-wheel-for-pillow
RUN pip3 install -U setuptools

RUN pip3 install --no-cache-dir --upgrade -r /code/requirements.txt

COPY . /code/app-client

ENTRYPOINT ["python3", "-u", "/code/app-client/mainClient.py"]
