# -*- coding: utf-8 -*-

import logging
import socket
import sys
import threading
import time
from threading import Thread
from typing import Any, List, Optional

from confluent_kafka import Producer, Consumer, TopicPartition, KafkaError
from confluent_kafka.admin import AdminClient
from confluent_kafka.cimpl import NewTopic
from pip_services3_commons.config import ConfigParams, IConfigurable
from pip_services3_commons.errors import ConnectionException, InvalidStateException
from pip_services3_commons.refer import IReferenceable, IReferences
from pip_services3_commons.run import IOpenable
from pip_services3_components.log import CompositeLogger
from pip_services3_messaging.connect.IMessageQueueConnection import IMessageQueueConnection

from pip_services3_kafka.connect.IKafkaMessageListener import IKafkaMessageListener
from pip_services3_kafka.connect.KafkaConnectionResolver import KafkaConnectionResolver
from pip_services3_kafka.connect.KafkaSubscription import KafkaSubscription


class KafkaConnection(IMessageQueueConnection, IReferenceable, IConfigurable, IOpenable):
    """
    Kafka connection using plain driver.

    By defining a connection and sharing it through multiple message queues
    you can reduce number of used database connections.

    ### Configuration parameters ###
        - client_id:               (optional) name of the client id
        - connection(s):
            - discovery_key:             (optional) a key to retrieve the connection from :class:`IDiscovery <pip_services3_components.connect.IDiscovery.IDiscovery>`
            - host:                      host name or IP address
            - port:                      port number (default: 27017)
            - uri:                       resource URI or connection string with all parameters in it
        - credential(s):
            - store_key:                 (optional) a key to retrieve the credentials from :class:`ICredentialStore <pip_services3_components.auth.ICredentialStore.ICredentialStore>`
            - username:                  user name
            - password:                  user password
        - options:
            - log_level:            (optional) log level 0 - None, 1 - Error, 2 - Warn, 3 - Info, 4 - Debug (default: 1)
            - connect_timeout:      (optional) number of milliseconds to connect to broker (default: 1000)
            - max_retries:          (optional) maximum retry attempts (default: 5)
            - retry_timeout:        (optional) number of milliseconds to wait on each reconnection attempt (default: 30000)
            - request_timeout:      (optional) number of milliseconds to wait on flushing messages (default: 30000)

    ### References ###
        - `*:logger:*:*:1.0`            (optional) :class:`ILogger <pip_services3_components.log.ILogger.ILogger>` components to pass log messages
        - `*:discovery:*:*:1.0`         (optional) :class:`IDiscovery <pip_services3_components.connect.IDiscovery.IDiscovery>` services to resolve connection
        - `*:credential-store:*:*:1.0`  (optional) Credential stores to resolve credentials
    """

    def __init__(self):
        """
        Creates a new instance of the connection component.
        """
        self.__default_config = ConfigParams.from_tuples(
            # connections. *
            # credential. *

            "client_id", None,
            "options.log_level", 1,
            "options.connect_timeout", 1000,
            "options.retry_timeout", 30000,
            "options.max_retries", 5,
            "options.request_timeout", 30000
        )

        # The logger.
        self._logger: CompositeLogger = CompositeLogger()

        # The connection resolver.
        self._connection_resolver: KafkaConnectionResolver = KafkaConnectionResolver()

        # The configuration options.
        self._options: ConfigParams = ConfigParams()

        # The Kafka connection pool object.
        self._connection: Producer = None

        # Kafka connection properties
        self._client_config: dict = {}

        # The Kafka message producer object;
        self._producer: Optional[Producer] = None

        # The Kafka admin client object;
        self._admin_client: Optional[AdminClient] = None

        # Topic subscriptions
        self._subscriptions: List[KafkaSubscription] = []

        self._client_id: str = socket.gethostname()
        self._log_level: int = 1
        self._connect_timeout: int = 1000
        self._max_retries: int = 5
        self._retry_timeout: int = 30000
        self._request_timeout: int = 30000

        self.__stop_events: List[threading.Event] = []

    def configure(self, config: ConfigParams):
        """
        Configures component by passing configuration parameters.

        :param config: configuration parameters to be set.
        """
        config = config.set_defaults(self.__default_config)
        self._connection_resolver.configure(config)
        self._options = self._options.override(config.get_section('options'))

        self._client_id = config.get_as_string_with_default('client_id', self._client_id)
        self._log_level = config.get_as_integer_with_default('options.log_level', self._connect_timeout)
        self._connect_timeout = config.get_as_integer_with_default('options.connect_timeout', self._connect_timeout)
        self._max_retries = config.get_as_integer_with_default('options.max_retries', self._max_retries)
        self._retry_timeout = config.get_as_integer_with_default('options.retry_timeout', self._retry_timeout)
        self._request_timeout = config.get_as_integer_with_default('options.request_timeout', self._request_timeout)

    def set_references(self, references: IReferences):
        """
        Sets references to dependent components.

        :param references: references to locate the component dependencies.
        """
        self._logger.set_references(references)
        self._connection_resolver.set_references(references)

    def is_open(self) -> bool:
        """
        Checks if the component is opened.

        :return: true if the component has been opened and false otherwise.
        """
        return self._connection is not None

    def __create_config(self, kind: str, options: dict = None) -> dict:
        """
        Create config for kafka objects

        :param kind: config for producer, consumer or admin
        :param options: additional config
        :return: dict with config
        """
        # TODO maybe need add another configs
        config = self._connection_resolver.resolve(None)
        brokers = config.get_as_string('brokers')
        options = options or {}

        options.update({'reconnect.backoff.max.ms': self._connect_timeout,
                        'bootstrap.servers': brokers,
                        # 'ssl_check_hostname': config.get_as_boolean('ssl')
                        })

        if kind in ['producer', 'admin']:
            options['retries'] = self._max_retries
            options['request.timeout.ms'] = self._request_timeout

        if kind == 'consumer':
            options['group.id'] = options.get('group.id', self._client_id)
            # options['queued.max.messages.kbytes'] = 2000000
            options['session.timeout.ms'] = int(options.get('session.timeout.ms', 10000))

            if 'from_beginning' in options.keys():
                options.pop('from_beginning')
                options['default.topic.config'] = {'auto.offset.reset': 'beginning'}
            else:
                options['default.topic.config'] = {'auto.offset.reset': 'smallest'}

            if options.get('heartbeat.interval.ms'):
                options['heartbeat.interval.ms'] = int(options['heartbeat.interval.ms'], 10000)

            options['enable.auto.commit'] = options.get('enable.auto.commit', True)
            options['auto.commit.interval.ms'] = options.get('auto.commit.interval.ms', 5000)

        username = config.get_as_string("username")
        password = config.get_as_string("password")
        mechanism = config.get_as_string_with_default("mechanism", "plain")

        options['security.protocol'] = 'PLAINTEXT'

        if username and password:
            options['sasl.mechanism'] = mechanism.upper()
            options['security.protocol'] = 'SASL_SSL' if config.get_as_boolean('ssl') else 'SASL_PLAINTEXT'
            options['sasl.username'] = username
            options['sasl.password'] = password

        return options

    def __set_log_level(self):
        """
        Sets log level for kafka
        """
        if self._log_level == 0:
            logging.getLogger('kafka').setLevel(logging.NOTSET)
        elif self._log_level == 1:
            logging.getLogger('kafka').setLevel(logging.ERROR)
        elif self._log_level == 2:
            logging.getLogger('kafka').setLevel(logging.WARN)
        elif self._log_level == 3:
            logging.getLogger('kafka').setLevel(logging.INFO)
        elif self._log_level == 4:
            logging.getLogger('kafka').setLevel(logging.DEBUG)

    def open(self, correlation_id: Optional[str]):
        """
        Opens the component.

        :param correlation_id: (optional) transaction id to trace execution through call chain.
        """
        if self._connection is not None:
            return

        try:

            # set log level for kafka
            self.__set_log_level()

            self._client_config = self.__create_config('producer')

            self._connection = Producer(self._client_config)
            self._producer = self._connection

            self._logger.debug(correlation_id,
                               f"Connected to Kafka broker at {self._client_config['bootstrap.servers']}")

        except Exception as err:
            self._logger.error(correlation_id, err, "Failed to connect to Kafka server")
            raise ConnectionException(
                correlation_id,
                "CONNECT_FAILED",
                "Connection to Kafka service failed"
            ).with_cause(err)

    def close(self, correlation_id: Optional[str]):
        """
        Closes component and frees used resources.

        :param correlation_id: (optional) transaction id to trace execution through call chain.
        """
        if self._connection is None:
            return

        # Disconnect producer
        if self._admin_client is not None:
            self._admin_client = None

        # Disconnect consumers
        for index in range(len(self._subscriptions)):
            self.__stop_events[index].clear()
            # if self._subscriptions[index].handler:
            #     self._subscriptions[index].handler.close()

        # Timeout for closing consumers by event
        time.sleep(1)

        self.__stop_events = []
        self._subscriptions = []

        self._connection = None
        self._logger.debug(correlation_id, "Disconnected from Kafka server")

    def get_connection(self) -> Any:
        """
        Gets the connection.
        """
        return self._connection

    def get_producer(self) -> Producer:
        """
        Gets the Kafka message producer object
        """
        return self._producer

    def _check_open(self):
        """
        Checks if connection is open

        :raises: an error is connection is closed or `None` otherwise.
        """
        if self.is_open():
            return

        raise InvalidStateException(
            None,
            "NOT_OPEN",
            "Connection was not opened"
        )

    def _connect_to_admin(self):
        """
        Connect admin client on demand.
        """
        self._check_open()

        if self._admin_client is not None:
            return

        options = self.__create_config('admin')

        self._admin_client = AdminClient(options)

    def read_queue_names(self) -> List[str]:
        """
        Reads a list of registered queue names.
        If connection doesn't support this function returnes an empty list.
        :return: queue names.
        """
        self._connect_to_admin()

        return list(self._admin_client.list_topics().topics.keys())

    def create_queue(self, name: str):
        """
        Creates a message queue.
        If connection doesn't support this function it exists without error.

        :param name: the name of the queue to be created.
        """
        self._check_open()
        self._connect_to_admin()

        self._admin_client.create_topics([NewTopic(topic=name, num_partitions=1, replication_factor=1)])

    def delete_queue(self, name: str):
        """
        Deletes a message queue.
        If connection doesn't support this function it exists without error.

        :param name: the name of the queue to be deleted.
        """
        self._check_open()
        self._connect_to_admin()

        self._admin_client.delete_topics([name])

    def publish(self, topic: str, messages: List[dict], options: dict):
        """
        Publish a message to a specified topic

        :param topic: a topic where the message will be placed
        :param messages: a list of messages to be published
        :param options: publishing options
        """
        # Check for open connection
        self._check_open()

        options = options or {}

        if options.get('compression'):
            options['compression.type'] = options.pop('compression')
        if options.get('timeout'):
            options['message.timeout.ms'] = options.pop('timeout')

        # Reconfigure Producer
        if options != {}:
            self._client_config.update(options)
            self._connection = Producer(self._client_config)
            self._producer = self._connection

        for message in messages:
            self._producer.produce(topic=topic, **message)
        self._producer.flush(5)

    def subscribe(self, topic: str, group_id: str, options: dict, listener: IKafkaMessageListener):
        """
        Subscribes to a topic

        :param topic: subject(topic) name
        :param group_id: (optional) consumer group id
        :param options: subscription options
        :param listener: message listener
        """
        # Check for open connection
        self._check_open()

        options = options or {}
        options['group.id'] = group_id or 'default'

        consumer_options = self.__create_config('consumer', options)

        try:
            # Subscribe to topic
            consumer = Consumer(consumer_options)
            consumer.subscribe([topic])

            # Consume incoming messages in background
            event = threading.Event()
            event.set()
            Thread(target=self.__handler, args=(consumer, listener, event), daemon=True).start()

            # Add the subscription
            subscription = KafkaSubscription(
                topic=topic,
                group_id=group_id,
                options=consumer_options,
                handler=consumer,
                listener=listener
            )

            self.__stop_events.append(event)
            self._subscriptions.append(subscription)
        except Exception as err:
            self._logger.error(None, err, "Failed to connect Kafka consumer.")
            raise err

    def __handler(self, consumer: Consumer, listener: IKafkaMessageListener, event: threading.Event):
        """Consume messages in thread"""
        try:
            while event.is_set():
                msg = consumer.poll(1)
                if msg is None:
                    continue
                if not msg.error():
                    listener.on_message(msg.topic(), msg.partition(), msg)
                elif msg.error().code() != KafkaError._PARTITION_EOF:
                    sys.stderr.write(f'Error consume message: {msg.error()}')
                    event.clear()
        except Exception as err:
            sys.stderr.write(f'Error processing message in the Consumer handler: {err}')
            self._logger.error(None, err, "Error processing message in the Consumer handler")
        finally:
            consumer.close()

    def unsubscribe(self, topic: str, group_id: str, listener: IKafkaMessageListener):
        """
        Unsubscribe from a previously subscribed topic

        :param topic: a topic name
        :param group_id: (optional) a consumer group id
        :param listener: a message listener
        """
        # Find the subscription index
        index = -1
        for i, v in enumerate(self._subscriptions):
            if v.topic == topic and v.group_id == group_id and v.listener == listener:
                index = i
                break
        if index < 0:
            return

        # Remove the subscription
        subscription = self._subscriptions[index]
        # Stop event for thread with consumer
        stop_event = self.__stop_events[index]

        del self.__stop_events[index]
        del self._subscriptions[index]

        if self.is_open() and subscription.handler is not None:
            # subscription.handler.close()
            stop_event.clear()

    def commit(self, topic: str, group_id: str, partition: int, offset: int, listener: IKafkaMessageListener):
        """
        Commit a message offset.

        :param topic: a topic name
        :param group_id: (optional) a consumer group id
        :param partition: a partition number
        :param offset: a message offset
        :param listener: a message listener
        """
        # Check for open connection
        self._check_open()

        # Find the subscription
        subscription = None
        for v in self._subscriptions:
            if v.topic == topic and v.group_id == group_id and v.listener == listener:
                subscription = v
                break

        if subscription is None or subscription.options.get('autoCommit'):
            return

        # Commit the offset
        subscription.handler.commit(offsets=[TopicPartition(topic=topic, partition=partition, offset=offset)],
                                    asynchronous=True)

    def seek(self, topic: str, group_id: str, partition: int, offset: int, listener: IKafkaMessageListener):
        """
        Seek a message offset.

        :param topic: a topic name
        :param group_id: (optional) a consumer group id
        :param partition: a partition number
        :param offset: a message offset
        :param listener: a message listener
        """
        # Check for open connection
        self._check_open()

        # Find the subscription
        subscription = None
        for v in self._subscriptions:
            if v.topic == topic and v.group_id == group_id and v.listener == listener:
                subscription = v
                break

        if subscription is None or subscription.options.get('autoCommit'):
            return

        # Seek the offset
        subscription.handler.seek(TopicPartition(topic=topic, partition=partition, offset=offset))
