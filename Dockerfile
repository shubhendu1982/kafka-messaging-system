FROM python:3.10-slim-buster

COPY . /service
WORKDIR /service


RUN pip install -r requirements.txt
RUN pip install .

# remove unneeded packages with vulnerabilities

RUN apt-get update -y
RUN apt-get purge -y curl "libcurl*" "libxslt*"
RUN apt-get autoremove -y

# create new user and execute as that user
RUN useradd --create-home appuser
WORKDIR /home/appuser
USER appuser

ENV PYTHONUNBUFFERED=1

# Please adapt to package name:
#ENTRYPOINT ["python /serivce/src/producer.py"]
#CMD ["python", "/service/src/producer.py"]
