FROM python:3.10.6-bullseye

COPY . /service
WORKDIR /service
RUN pip install -r requirements.txt
RUN pip install .

# create new user and execute as that user
RUN useradd --create-home appuser
WORKDIR /home/appuser
USER appuser

ENV PYTHONUNBUFFERED=1

# Please adapt to package name:
#ENTRYPOINT ["python /serivce/src/producer.py"]
#CMD ["python", "/service/src/producer.py"]
