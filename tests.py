from nose.tools import raises
from alfred import parseArgs
from tools import Bus

requiredArgs = ['--db_host', 'host', '--broker_host', 'host']


@raises(SystemExit)
def test_no_arguments():
    parseArgs()


def test_with_hosts():
    parseArgs(requiredArgs)


def test_arg_types():
    requiredArgs.extend(['--db_port', '1900'])
    args = parseArgs(requiredArgs)
    assert isinstance(args.db_port, int)
    assert args.db_port == 1900


def test_conf_file():
    from ConfigParser import ConfigParser
    c = ConfigParser()
    c.read('test.ini')
    args = parseArgs(['-c', 'test.ini'])
    assert args.db_host == c.get('db', 'host')


class TestBusConnection(object):

    def setup(self):
        # Using the config file, easier to adapt tests to environrment tests
        from ConfigParser import ConfigParser
        self.config = ConfigParser()
        self.config.read('test.ini')

    def test_bus_connection(self):
        Bus(self.config.get('broker', 'host'), 1883)

    def test_publish(self):
        self.passed = False

        def on_message(msg):
            assert msg.topic == '/'.join([b.base_topic, 'test'])
            assert msg.payload == 'test message'
            self.passed = True

        b = Bus(self.config.get('broker', 'host'), 1883)
        b.subscribe('#')
        b.on_message = on_message
        b.publish("test", "test message")

        while not self.passed:
            b.client.loop_start()
