# -*- coding: utf-8 -*-
import os

import pytest
from pip_services3_commons.config import ConfigParams

from pip_services3_kafka.queues.KafkaMessageQueue import KafkaMessageQueue
from test.queues.MessageQueueFixture import MessageQueueFixture

broker_host = os.environ.get('KAFKA_SERVICE_HOST') or 'localhost'
broker_port = os.environ.get('KAFKA_SERVICE_PORT') or 9092

broker_topic = os.environ.get('KAFKA_TOPIC') or 'test'
broker_user = os.environ.get('KAFKA_USER')  # or 'kafka'
broker_pass = os.environ.get('KAFKA_PASS')  # or 'pass123'


@pytest.mark.skipif(not broker_host and not broker_port, reason="Kafka server is not configured")
class TestKafkaMessageQueue:
    queue: KafkaMessageQueue
    fixture: MessageQueueFixture

    def setup_method(self):
        queue_config = ConfigParams.from_tuples(
            'queue', broker_topic,
            'connection.protocol', 'tcp',
            'connection.host', broker_host,
            'connection.port', broker_port,
            'credential.username', broker_user,
            'credential.password', broker_pass,
            'credential.mechanism', 'plain',
            'options.autosubscribe', True
        )

        self.queue = KafkaMessageQueue(broker_topic)
        self.queue.configure(queue_config)

        self.fixture = MessageQueueFixture(self.queue)

        self.queue.open(None)
        # self.queue.clear(None)

    def teardown_method(self):
        self.queue.close(None)

    def test_send_and_receive_message(self):
        self.fixture.test_send_and_receive_message()

    def test_receive_and_send_message(self):
        self.fixture.test_receive_and_send_message()

    def test_send_peek_message(self):
        self.fixture.test_send_peek_message()

    def test_peek_no_message(self):
        self.fixture.test_peek_no_message()

    def test_on_message(self):
        self.fixture.test_on_message()
