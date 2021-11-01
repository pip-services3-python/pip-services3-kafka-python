# -*- coding: utf-8 -*-

from typing import Any

from confluent_kafka import Consumer

from pip_services3_kafka.connect.IKafkaMessageListener import IKafkaMessageListener


class KafkaSubscription:
    """
    The KafkaSubscription class defines fields for Kafka subscriptions
    """

    def __init__(self, topic: str = None, group_id: str = None, options: Any = None, handler: Consumer = None,
                 listener: IKafkaMessageListener = None):
        """
        Creates new instance

        :param topic: topic
        :param group_id: Group id
        :param options: Options
        :param handler: Handler
        :param listener: Listener
        """
        self.topic = topic
        self.group_id = group_id
        self.options = options
        self.handler: Consumer = handler
        self.listener = listener
