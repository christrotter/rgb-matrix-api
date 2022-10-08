FROM python:3.9
WORKDIR /code

COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
RUN mkdir /code/app-api

COPY . /code/app-api/

CMD ["uvicorn", "app-api.mainAPI:app", "--host", "0.0.0.0", "--port", "8000"]
