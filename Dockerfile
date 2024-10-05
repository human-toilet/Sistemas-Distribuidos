FROM python:3.11-slim

RUN mkdir -p /home/dist
COPY . /home/dist

RUN pip install -r /home/dist/requirements.txt

CMD [ "python3", "/home/dist/main.py" ]