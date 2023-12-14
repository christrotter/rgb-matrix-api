FROM python:3.9
WORKDIR /code

COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
RUN mkdir /code/config_bundler

COPY . /code/config_bundler/

ENTRYPOINT ["python3", "-u", "/code/config_bundler/main.py"]
