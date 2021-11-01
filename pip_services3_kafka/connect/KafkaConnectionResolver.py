# -*- coding: utf-8 -*-

from typing import Optional, List, Any

from pip_services3_commons.config import IConfigurable, ConfigParams
from pip_services3_commons.errors import ConfigException
from pip_services3_commons.refer import IReferenceable, IReferences
from pip_services3_components.auth import CredentialResolver, CredentialParams
from pip_services3_components.connect import ConnectionResolver, ConnectionParams


class KafkaConnectionResolver(IReferenceable, IConfigurable):
    """
    Helper class that resolves Kafka connection and credential parameters,
    validates them and generates connection options.

    ### Configuration parameters ###
         - connection(s):
           - discovery_key:               (optional) a key to retrieve the connection from :class:`IDiscovery <pip_services3_components.connect.IDiscovery.IDiscovery>`
           - host:                        host name or IP address
           - port:                        port number
           - uri:                         resource URI or connection string with all parameters in it
         - credential(s):
           - store_key:                   (optional) a key to retrieve the credentials from :class:`ICredentialStore <pip_services3_components.auth.ICredentialStore.ICredentialStore>`
           - username:                    user name
           - password:                    user password

    ### References ###
        - `*:discovery:*:*:1.0`      (optional) :class:`IDiscovery <pip_services3_components.connect.IDiscovery.IDiscovery>` services to resolve connection
        - `*:credential-store:*:*:1.0`         (optional) Credential stores to resolve credentials

    """

    def __init__(self):
        # The connections resolver.
        self.__connection_resolver = ConnectionResolver()
        # The credentials resolver.
        self.__credential_resolver = CredentialResolver()

    def configure(self, config: ConfigParams):
        """
        Configures component by passing configuration parameters.

        :param config: configuration parameters to be set.
        """
        self.__connection_resolver.configure(config)
        self.__credential_resolver.configure(config)

    def set_references(self, references: IReferences):
        """
        Sets references to dependent components.

        :param references: references to locate the component dependencies.
        """
        self.__connection_resolver.set_references(references)
        self.__credential_resolver.set_references(references)

    def __validate_connection(self, correlation_id: Optional[str], connection: ConnectionParams):
        if connection is None:
            raise ConfigException(
                correlation_id,
                "NO_CONNECTION",
                "Kafka connection is not set"
            )

        uri = connection.get_uri()

        if uri is not None:
            return

        protocol = connection.get_as_string_with_default('protocol', 'tcp')

        if protocol is None:
            raise ConfigException(
                correlation_id,
                "NO_PROTOCOL",
                "Connection protocol is not set"
            )

        if protocol != 'tcp':
            raise ConfigException(
                correlation_id,
                "UNSUPPORTED_PROTOCOL",
                "The protocol " + protocol + " is not supported"
            )

        host = connection.get_host()
        if host is None:
            raise ConfigException(
                correlation_id,
                "NO_HOST",
                "Connection host is not set"
            )

        port = connection.get_as_integer_with_default('port', 9092)
        if port == 0:
            raise ConfigException(
                correlation_id,
                "NO_PORT",
                "Connection port is not set"
            )

    def __parse_uri(self, value: str, options: ConfigParams):
        if value is None:
            return

        brokers = ''
        uris = value.split(',')
        for uri in uris:
            uri = uri.strip()

            pos = uri.find('?')
            uri = uri[0:pos] if pos >= 0 else uri

            pos = uri.find('://')
            uri = uri[pos + 3:] if pos >= 0 else uri

            pos = uri.find('@')

            server = uri[pos + 1:] if pos > 0 else uri
            if brokers != '':
                brokers += ','

            brokers += server

            if pos > 0:
                name_pass = uri[0:pos]
                pos = name_pass.find(':')
                name = name_pass[0:pos] if pos > 0 else name_pass
                password = name_pass[pos + 1:] if pos > 0 else ''
                options.set_as_object('username', name)
                options.set_as_object('password', password)

        options.set_as_object('brokers', brokers)

    def __compose_options(self, connections: List[ConnectionParams], credential: CredentialParams) -> ConfigParams:
        # Define additional parameters parameters
        if credential is None:
            credential = CredentialParams()

        # Construct options and copy over credentials
        options = ConfigParams()
        options = options.set_defaults(credential)

        global_uri = ""
        brokers = ""

        # Process connections, find or constract uri
        for connection in connections:
            if global_uri != '':
                continue

            uri = connection.get_uri()
            if uri:
                global_uri = uri
                continue

            if brokers != '':
                brokers += ','

            host = connection.get_host()
            brokers += host

            port = connection.get_as_integer_with_default('port', 9092)
            brokers += f':{port}'

        # Set connection uri
        if global_uri != '':
            self.__parse_uri(global_uri, options)
        else:
            options.set_as_object('brokers', brokers)

        return options

    def resolve(self, correlation_id: Optional[str]) -> ConfigParams:
        """
        Resolves Kafka connection options from connection and credential parameters.

        :param correlation_id: (optional) transaction id to trace execution through call chain.
        :return: resolved Kafka connection options.
        """
        connections = self.__connection_resolver.resolve_all(correlation_id)
        # Validate connections
        for connection in connections:
            self.__validate_connection(correlation_id, connection)

        credential = self.__credential_resolver.lookup(correlation_id)
        # Credentials are not validated right now

        options = self.__compose_options(connections, credential)
        return options

    def compose(self, correlation_id: Optional[str], connections: List[ConnectionParams],
                credential: CredentialParams) -> Any:
        """
        Composes Kafka connection options from connection and credential parameters.

        :param correlation_id: (optional) transaction id to trace execution through call chain.
        :param connections: connection parameters
        :param credential: credential parameters
        :return: resolved Kafka connection options.
        """
        # Validate connections
        for connection in connections:
            self.__validate_connection(correlation_id, connection)

        options = self.__compose_options(connections, credential)
        return options
