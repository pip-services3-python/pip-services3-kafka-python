# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod

from confluent_kafka import Message


class IKafkaMessageListener(ABC):
    """
    The IKafkaMessageListener interface defines a Kafka message listener.
    """

    @abstractmethod
    def on_message(self, topic: str, partition: int, message: Message):
        """
        Defines the actions to be done after a message is received.

        :param topic: topic
        :param partition: partition
        :param message: message
        """
        ...
