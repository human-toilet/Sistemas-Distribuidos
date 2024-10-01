FROM python

RUN mkdir -p /home/dist
COPY . /home/dist

RUN pip install -r /home/dist/requirements.txt

EXPOSE 5000

CMD [ "python3", "/home/dist/main.py" ]