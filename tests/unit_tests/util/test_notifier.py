from unittest import mock

from karp.util.notifier import Notifier, Observer


def test_notifier():
    notifier = Notifier()

    assert isinstance(notifier.observers, set)
    assert not notifier.observers


def test_observer():
    observer = Observer()

    observer.update()
    observer.update(**{"a": "b"})


def test_notifier_register_and_unregister_observer():
    notifier = Notifier()
    observer = Observer()

    notifier.register(observer)

    assert observer in notifier.observers

    notifier.unregister(observer)

    assert observer not in notifier.observers

    # Test unregister again doesn't do anything
    notifier.unregister(observer)


def test_notifier_notify():
    notifier = Notifier()
    observer_mock = mock.Mock(spec=Observer)

    notifier.register(observer_mock)
    notifier.notify()

    assert observer_mock.mock_calls == [mock.call.update()]


def test_notifier_notify_args():
    notifier = Notifier()
    observer_mock = mock.Mock(spec=Observer)

    notifier.register(observer_mock)
    kwargs = {"a": "one", "b": "two", "c": 1}
    notifier.notify(**kwargs)

    assert observer_mock.mock_calls == [mock.call.update(**kwargs)]
