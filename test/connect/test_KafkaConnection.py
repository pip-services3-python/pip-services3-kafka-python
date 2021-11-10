# -*- coding: utf-8 -*-
import os
import time

import pytest
from pip_services3_commons.config import ConfigParams

from pip_services3_kafka.connect.KafkaConnection import KafkaConnection

broker_host = os.environ.get('KAFKA_SERVICE_HOST') or 'localhost'
broker_port = os.environ.get('KAFKA_SERVICE_PORT') or 9092

broker_topic = os.environ.get('KAFKA_TOPIC') or 'test'
broker_user = os.environ.get('KAFKA_USER')  # or 'kafka'
broker_pass = os.environ.get('KAFKA_PASS')  # or 'pass123'


@pytest.mark.skipif(not broker_host and not broker_port, reason="Kafka server is not configured")
class TestKafkaConnection:
    connection: KafkaConnection

    def setup_method(self):
        config = ConfigParams.from_tuples(
            'topic', broker_topic,
            'connection.protocol', 'tcp',
            'connection.host', broker_host,
            'connection.port', broker_port,
            'credential.username', broker_user,
            'credential.password', broker_pass,
            'credential.mechanism', 'plain'
        )

        self.connection = KafkaConnection()
        self.connection.configure(config)

    def test_open_close(self):
        self.connection.open(None)
        assert self.connection.is_open() is True
        assert self.connection.get_connection() is not None

        self.connection.close(None)
        assert self.connection.is_open() is False
        assert self.connection.get_connection() is None

    def test_list_topics(self):
        self.connection.open(None)
        assert self.connection.is_open() is True
        assert self.connection.get_connection() is not None

        topics = self.connection.read_queue_names()
        assert isinstance(topics, list)

        self.connection.close(None)
        assert self.connection.is_open() is False
        assert self.connection.get_connection() is None

    def test_create_delete_topics(self):
        topics = ['new_topic1', 'new_topic2']
        self.connection.open(None)

        self.connection.create_queue(topics[0])
        self.connection.create_queue(topics[1])
        time.sleep(0.5)

        kafka_topics = self.connection.read_queue_names()

        assert topics[0] in kafka_topics
        assert topics[1] in kafka_topics

        self.connection.delete_queue(topics[0])
        self.connection.delete_queue(topics[1])
        time.sleep(0.5)

        kafka_topics = self.connection.read_queue_names()

        assert topics[0] not in kafka_topics
        assert topics[1] not in kafka_topics
