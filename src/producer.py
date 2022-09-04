"""
    Kafka producer
"""

import json
from time import sleep

from kafka import KafkaProducer


def produce():
    """
    produce
    """
# create producer with certificates mounted in /data
producer = KafkaProducer(
bootstrap_servers=['my-cluster-kafka-bootstrap:9093'],
value_serializer=lambda m: json.dumps(m).encode('ascii'),
security_protocol='SSL',
ssl_check_hostname=True,
ssl_cafile='/data/crt/ca.crt',
ssl_certfile='/data/usercrt/user.crt',
ssl_keyfile='/data/usercrt/user.key',
)

# Post some random data in topic called my-topic in 60 sec interval
for i in range(100):
    producer.send("my-topic", {i: i})
    print(f"message published, {i}")

if __name__ == "__main__":
    while True:
        produce()
        sleep(60)
