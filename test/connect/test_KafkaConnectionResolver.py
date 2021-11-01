# -*- coding: utf-8 -*-

from pip_services3_commons.config import ConfigParams

from pip_services3_kafka.connect.KafkaConnectionResolver import KafkaConnectionResolver


class TestKafkaConnectionResolver:

    def test_single_connection(self):
        resolver = KafkaConnectionResolver()
        resolver.configure(ConfigParams.from_tuples(
            "connection.protocol", "tcp",
            "connection.host", "localhost",
            "connection.port", 9092
        ))

        connection = resolver.resolve(None)
        assert 'localhost:9092' == connection.get_as_string('brokers')
        assert connection.get_as_string("username") == ''
        assert connection.get_as_string("password") == ''
        assert connection.get_as_string("token") == ''

    def test_cluster_connection(self):
        resolver = KafkaConnectionResolver()
        resolver.configure(ConfigParams.from_tuples(
            "connections.0.protocol", "tcp",
            "connections.0.host", "server1",
            "connections.0.port", 9092,
            "connections.1.protocol", "tcp",
            "connections.1.host", "server2",
            "connections.1.port", 9092,
            "connections.2.protocol", "tcp",
            "connections.2.host", "server3",
            "connections.2.port", 9092,
        ))

        connection = resolver.resolve(None)
        assert connection.get_as_string("brokers") != ''
        assert connection.get_as_string("username") == ''
        assert connection.get_as_string("password") == ''
        assert connection.get_as_string("token") == ''

    def test_cluster_connection_with_auth(self):
        resolver = KafkaConnectionResolver()
        resolver.configure(ConfigParams.from_tuples(
            "connections.0.protocol", "tcp",
            "connections.0.host", "server1",
            "connections.0.port", 9092,
            "connections.1.protocol", "tcp",
            "connections.1.host", "server2",
            "connections.1.port", 9092,
            "connections.2.protocol", "tcp",
            "connections.2.host", "server3",
            "connections.2.port", 9092,
            "credential.mechanism", "plain",
            "credential.username", "test",
            "credential.password", "pass123",
        ))

        connection = resolver.resolve(None)
        assert connection.get_as_string("brokers") != ''
        assert connection.get_as_string("username") == 'test'
        assert connection.get_as_string("password") == 'pass123'
        assert connection.get_as_string("mechanism") == 'plain'

    def test_cluster_uri(self):
        resolver = KafkaConnectionResolver()
        resolver.configure(ConfigParams.from_tuples(
            "connection.uri", "tcp://test:pass123@server1:9092,server2:9092,server3:9092?param=234",
        ))
        connection = resolver.resolve(None)
        assert connection.get_as_string("brokers") != ''
        assert connection.get_as_string("username") == 'test'
        assert connection.get_as_string("password") == 'pass123'
        assert connection.get_as_string("mechanism") == ''
