"""
    Kafka consumer
"""

from kafka import KafkaConsumer


def consume():
    """
    consume
    """
    consumer = KafkaConsumer(
        "my-topic", group_id="my-group",
        bootstrap_servers=["my-cluster-kafka-bootstrap:9093"],
        security_protocol='SSL',
        ssl_check_hostname=True,
        ssl_cafile='/data/crt/ca.crt',
        ssl_certfile='/data/usercrt/user.crt',
        ssl_keyfile='/data/usercrt/user.key'
    )

    for message in consumer:
        print(
            f" topic: {message.topic} partition: {message.partition} "
            + f"offset: {message.offset} key: {message.key} value: {message.value} "
        )

if __name__ == "__main__":
    consume()
