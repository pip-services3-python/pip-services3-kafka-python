# -*- coding: utf-8 -*-
import time

from pip_services3_messaging.queues import MessageEnvelope, IMessageQueue
from pip_services3_messaging.test.TestMessageReceiver import TestMessageReceiver


class MessageQueueFixture:
    _queue: IMessageQueue

    def __init__(self, queue: IMessageQueue):
        self._queue = queue

    def test_send_and_receive_message(self):
        envelope1 = MessageEnvelope("123", "Test", "Test message")

        self._queue.send(None, envelope1)

        envelope2 = self._queue.receive(None, 10000)

        assert envelope2 is not None
        assert envelope1.message_type == envelope2.message_type
        assert envelope1.message.decode('utf-8') == envelope2.message.decode('utf-8')
        assert envelope1.correlation_id == envelope2.correlation_id

    def test_receive_and_send_message(self):
        envelope1 = MessageEnvelope("123", "Test", "Test message")

        time.sleep(0.5)
        self._queue.send(None, envelope1)

        envelope2 = self._queue.receive(None, 10000)
        assert envelope2 is not None
        assert envelope1.message_type == envelope2.message_type
        assert envelope1.message.decode('utf-8') == envelope2.message.decode('utf-8')
        assert envelope1.correlation_id == envelope2.correlation_id

    def test_receive_complete_message(self):
        envelope1 = MessageEnvelope("123", "Test", "Test message")

        self._queue.send(None, envelope1)

        count = self._queue.read_message_count()
        assert count > 0

        envelope2 = self._queue.receive(None, 10000)
        assert envelope2 is not None
        assert envelope1.message_type == envelope2.message_type
        assert envelope1.message.decode('utf-8') == envelope2.message.decode('utf-8')
        assert envelope1.correlation_id == envelope2.correlation_id

        self._queue.complete(envelope2)
        assert envelope1.get_reference() is None

    def test_receive_abandon_message(self):
        envelope1 = MessageEnvelope("123", "Test", "Test message")
        self._queue.send(None, envelope1)

        envelope2 = self._queue.receive(None, 10000)
        assert envelope2 is not None
        assert envelope1.message_type == envelope2.message_type
        assert envelope1.message.decode('utf-8') == envelope2.message.decode('utf-8')
        assert envelope1.correlation_id == envelope2.correlation_id

        self._queue.abandon(envelope2)

        envelope2 = self._queue.receive(None, 10000)
        assert envelope2 is not None
        assert envelope1.message_type == envelope2.message_type
        assert envelope1.message.decode('utf-8') == envelope2.message.decode('utf-8')
        assert envelope1.correlation_id == envelope2.correlation_id

    def test_send_peek_message(self):
        envelope1 = MessageEnvelope("123", "Test", "Test message")
        self._queue.send(None, envelope1)

        # Delay until the message is received
        time.sleep(4)

        envelope2 = self._queue.peek(None)
        assert envelope2 is not None
        assert envelope1.message_type == envelope2.message_type
        assert envelope1.message.decode('utf-8') == envelope2.message.decode('utf-8')
        assert envelope1.correlation_id == envelope2.correlation_id

    def test_peek_no_message(self):
        envelope = self._queue.peek(None)
        assert envelope is None

    def test_move_to_dead_message(self):
        envelope1 = MessageEnvelope("123", "Test", "Test message")
        self._queue.send(None, envelope1)

        envelope2 = self._queue.receive(None, 10000)
        assert envelope2 is not None
        assert envelope1.message_type == envelope2.message_type
        assert envelope1.message.decode('utf-8') == envelope2.message.decode('utf-8')
        assert envelope1.correlation_id == envelope2.correlation_id

        self._queue.move_to_dead_letter(envelope2)

    def test_on_message(self):
        message_receiver = TestMessageReceiver()
        self._queue.begin_listen(None, message_receiver)

        envelope1 = MessageEnvelope("123", "Test", "Test message")
        self._queue.send(None, envelope1)

        # await message
        for i in range(30):
            if len(message_receiver.messages) > 0:
                break
            time.sleep(1)

        envelope2 = message_receiver.messages[0]
        assert envelope2 is not None
        assert envelope1.message_type == envelope2.message_type
        assert envelope1.message.decode('utf-8') == envelope2.message.decode('utf-8')
        assert envelope1.correlation_id == envelope2.correlation_id

        self._queue.end_listen(None)
