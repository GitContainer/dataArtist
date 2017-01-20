# coding=utf-8
from __future__ import division
from __future__ import print_function
try:
    import pika
except ImportError:
    print("couldn't import pika - you wont be able to use the RabbitMQ data server")
from qtpy import QtCore


class RabbitMQServer(object):
    '''
    A server for communicating between different programs
    and remote control using RabbitMQ
    '''

    def __init__(self, gui):
        self.gui = gui
        self.timer = None

        self.opts = {'refreshrate': 1000,  # ms
                     'host': 'localhost',
                    # 'timeout': 1,  # ms
                     'corfirmPosts': False
                     }

        self.listenTo = {'addFile': self.gui.addFilePath,
                         'changeActiveDisplay': self.gui.changeActiveDisplay,
                         'showDisplay': self.gui.showDisplay,
                         'runScriptFromName': self.gui.runScriptFromName,
                         }


    def start(self):
        '''
        configure the server and check the
        message-inbox every self.opts['refeshrate']
        '''
        self.configure()
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.connection.process_data_events)
        self.timer.start(self.opts['refreshrate'])


    def configure(self):
        parameters = pika.URLParameters("amqp://%s/" % self.opts['host'])
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()
        for name in self.listenTo.keys():
            # INITITALIZE ALL QUEUES
            self.channel.queue_declare(queue=name)
            self.channel.basic_consume(
                queue=name, no_ack=True,
                consumer_callback=self.on_message)


    def on_message(self, channel, method_frame, header_frame, body):
        key = method_frame.routing_key
        if self.opts['corfirmPosts']:
            print(" [R] %s -> '%s'" % (key, body))
        action = self.listenTo[key]
        action(body)
#         channel.basic_ack(delivery_tag=method_frame.delivery_tag)


    def stop(self):
        if self.timer is not None and self.timer.isActive():
            self.timer.stop()
            self.channel.stop_consuming()
            self.connection.close()


if __name__ == '__main__':
    #send a message:
    import pika
    parameters = pika.URLParameters("amqp://localhost/")
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    channel.basic_publish(exchange='',
                          routing_key='addFile',
                          body='TEST/FILE/PATH.txt'
                          )
