FROM ubuntu:20.04
WORKDIR /code

RUN apt-get update && apt-get install -y git make build-essential python3 python3-pip python3-distutils python3-dev libjpeg-dev zlib1g-dev
RUN git clone https://github.com/hzeller/rpi-rgb-led-matrix.git
RUN cd rpi-rgb-led-matrix && make build-python PYTHON=$(which python3)
RUN cd rpi-rgb-led-matrix && make install-python PYTHON=$(which python3)
RUN mkdir /code/app-client

COPY ./requirements.txt /code/requirements.txt
# https://stackoverflow.com/questions/69624327/failed-building-wheel-for-pillow
RUN pip install -U setuptools

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY . /code/app-client

ENTRYPOINT ["python3", "-u", "/code/app-client/mainClient.py"]
