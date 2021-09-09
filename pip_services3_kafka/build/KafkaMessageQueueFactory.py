# -*- coding: utf-8 -*-
from pip_services3_commons.refer import Descriptor
from pip_services3_messaging.build.MessageQueueFactory import MessageQueueFactory
from pip_services3_messaging.queues import IMessageQueue

from pip_services3_kafka.queues.KafkaMessageQueue import KafkaMessageQueue


class KafkaMessageQueueFactory(MessageQueueFactory):
    """
    The KafkaMessageQueueFactory class allows you to create KafkaMessageQueue components by their descriptors.
    """
    __KafkaQueueDescriptor: Descriptor = Descriptor("pip-services", "message-queue", "kafka", "*", "1.0")

    def __init__(self):
        """
        Create a new instance of the factory.
        """
        super().__init__()

        self.register(self.__KafkaQueueDescriptor,
                      lambda locator: self.create_queue(
                          None if not callable(getattr(locator, 'get_name', None)) else locator.get_name()))

    def create_queue(self, name: str) -> IMessageQueue:
        """
        Creates a message queue component and assigns its name.

        :param name: a name of the created message queue.
        """
        queue = KafkaMessageQueue(name)

        if self._config:
            queue.configure(self._config)

        if self._references is not None:
            queue.set_references(self._references)

        return queue
