import glob
import gzip
import os
import time
import argparse
import logtail
import pika

class logtailrmq(logtail.logtail):
    """
    This class will tail a log and push the data to rabbitmq.
    """
    def __init__(self,globstr,directory,debug,singlefile,rabbitmq_host,exchange_name,exchange_type,routing_key,auto_delete,readsize=10000,recovery_file=None):
        super( logtailrmq, self ).__init__(globstr=globstr,directory=directory,debug=debug,singlefile=singlefile,readsize=readsize,recovery_file=recovery_file)
        self._rabbitmq_host = rabbitmq_host
        self._exchange_name = exchange_name
        self._exchange_type = exchange_type
        self._auto_delete = auto_delete
        self._routing_key = routing_key
        self._conn = None
        self._conn_channel = None
        self.connect()

    @property
    def conn(self):
        """
        Contains the connection to rabbitmq.
        """
        return self._conn

    @conn.setter
    def conn(self,value):
        self._conn = value

    @property
    def conn_channel(self):
        """
        The connection channel for publishing messages.
        """
        return self._conn_channel

    @conn_channel.setter
    def conn_channel(self,value):
        self._conn_channel = value

    @property
    def rabbitmq_host(self):
        """
        The rabbitmq host that we are connected to.
        """
        return self._rabbitmq_host

    @rabbitmq_host.setter
    def rabbitmq_host(self,value):
        self._rabbitmq_host = value

    @property
    def auto_delete(self):
        """
        Whether or not the exchange should auto delete when it is done.
        """
        return self._auto_delete

    @auto_delete.setter
    def auto_delete(self,value):
        self._auto_delete = value

    @property
    def exchange_name(self):
        """
        The name of the rabbitmq exchange.
        """
        return self._exchange_name

    @exchange_name.setter
    def exchange_name(self,value):
        self._exchange_name = value

    @property
    def exchange_type(self):
        """
        The exchange type of the rabbitmq exchange.
        """
        return self._exchange_type

    @exchange_type.setter
    def exchange_type(self,value):
        self._exchange_type = value

    @property
    def routing_key(self):
        """
        The routing key for messages into the rabbitmq exchange.
        """
        return self._routing_key

    @routing_key.setter
    def routing_key(self,value):
        self._routing_key = value

    def connect(self):
        if ( self.conn == None ):
            self.conn = pika.BlockingConnection(
                pika.ConnectionParameters(self.rabbitmq_host))
            self.conn_channel = self.conn.channel()
            self.conn_channel.exchange_declare(
                exchange=self.exchange_name,
                type=self.exchange_type,
                auto_delete=self.auto_delete)

    def process(self,line):
        if ( self.debug ):
            print line
        self.conn_channel.basic_publish(
            exchange=self.exchange_name,
            routing_key=self.routing_key,
            body=line)

def default_arg_parser():
    """
    Creates an argparse ArgumentParser for parsing the command line when this utility is run as the
    main script.
    """
    arg_parser = logtail.default_arg_parser();
    arg_parser.add_argument(
        '--rabbitmq-host','-b',
        required=True,
        dest="rabbitmq_host",
        help="The rabbitmq host.")
    arg_parser.add_argument(
        '--exchange-name','-e',
        required=True,
        dest="exchange_name",
        help="The rabbitmq exchange that will receive data.")
    arg_parser.add_argument(
        '--exchange-type','-t',
        dest="exchange_type",
        default="fanout",
        help="The type of exchange to declare.")
    arg_parser.add_argument(
        '--routing-key','-k',
        dest="routing_key",
        default="",
        help="The routing key for the messages in rabbitmq.")
    arg_parser.add_argument(
        '--auto-delete','-a',
        dest="auto_delete",
        default=False,
        help="set for auto deletion of exchanges (off by default)")
    return arg_parser

if __name__ == '__main__':
    import logtailrmq
    import os

    arg_parser = logtailrmq.default_arg_parser()
    options = arg_parser.parse_args()

    if options.debug == True :
        print options

    if os.path.isdir(options.directory) == True :
        lt = logtailrmq.logtailrmq(**(options.__dict__))
        lt.run()
