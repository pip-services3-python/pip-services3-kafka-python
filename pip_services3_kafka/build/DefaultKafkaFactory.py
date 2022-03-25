# -*- coding: utf-8 -*-
from pip_services3_commons.refer import Descriptor
from pip_services3_components.build import Factory

from pip_services3_kafka.connect.KafkaConnection import KafkaConnection
from pip_services3_kafka.queues.KafkaMessageQueue import KafkaMessageQueue

from .KafkaMessageQueueFactory import KafkaMessageQueueFactory


class DefaultKafkaFactory(Factory):
    """
    The DefaultKafkaFactory class allows you to create KafkaMessageQueue components by their descriptors.
    """
    __KafkaQueueDescriptor: Descriptor = Descriptor("pip-services", "message-queue", "kafka", "*", "1.0")
    __KafkaConnectionDescriptor: Descriptor = Descriptor("pip-services", "connection", "kafka", "*", "1.0")
    __KafkaQueueFactoryDescriptor: Descriptor = Descriptor("pip-services", "queue-factory", "kafka", "*", "1.0")

    def __init__(self):
        """
        Create a new instance of the factory.
        """
        super().__init__()

        self.register(self.__KafkaQueueDescriptor,
                      lambda locator: KafkaMessageQueue(
                          None if not callable(getattr(locator, 'get_name', None)) else locator.get_name()))

        self.register_as_type(self.__KafkaConnectionDescriptor, KafkaConnection)
        self.register_as_type(self.__KafkaQueueFactoryDescriptor, KafkaMessageQueueFactory)
