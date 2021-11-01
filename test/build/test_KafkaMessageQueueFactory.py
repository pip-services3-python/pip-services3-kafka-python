# -*- coding: utf-8 -*-

from pip_services3_commons.refer import Descriptor

from pip_services3_kafka.build.KafkaMessageQueueFactory import KafkaMessageQueueFactory
from pip_services3_kafka.queues.KafkaMessageQueue import KafkaMessageQueue


class TestKafkaMessageQueueFactory:

    def test_create_message_queue(self):
        factory = KafkaMessageQueueFactory()
        descriptor = Descriptor("pip-services", "message-queue", "kafka", "test", "1.0")

        can_result = factory.can_create(descriptor)
        assert can_result is not None

        queue: KafkaMessageQueue = factory.create(descriptor)
        assert queue is not None
        assert queue.get_name() == 'test'
