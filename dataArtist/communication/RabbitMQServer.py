# coding=utf-8

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
                         'runScriptFromName': self.gui.runScriptFromName
                         }

    def start(self):
        '''
        configure the server and check the
        message-inbox every self.opts['refeshrate']
        '''
        try:
            global pika
            import pika  # import here to save startup time
        except ImportError:
            raise ImportError(
                "couldn't import pika - you wont be able to use the RabbitMQ data server")

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
        # TEMP FIX: [body] is byte str -> b'...'
        # transform for python str:
        body = body.decode("utf-8")

        if self.opts['corfirmPosts']:
            print(" [R] %s -> {%s}" % (key, body))
        action = self.listenTo[key]
        action(body)

    def stop(self):
        if self.timer is not None and self.timer.isActive():
            self.timer.stop()
            self.channel.stop_consuming()
            self.connection.close()


if __name__ == '__main__':
    import sys
    from qtpy import QtWidgets

    ##############
    # Test all keys dataArtist listens to
    # in an interactive window
    # ensure, that dA.preferences.commmunication.RabbitMQ = True
    ##############

    # setup server:
    parameters = pika.URLParameters("amqp://localhost/")
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    # create window:
    a = QtWidgets.QApplication(sys.argv)
    w = QtWidgets.QWidget()
    l = QtWidgets.QGridLayout()

    I = [('addFile',             'path/to/file'),
         ('changeActiveDisplay', '1'),
         ('showDisplay',         '2, (0,0,100,200)'),
         ('runScriptFromName',   'SCRIPTNAME')]

    def fn(meth, txt):
        channel.basic_publish(exchange='',
                              routing_key=meth,
                              body=txt)

    for n, (meth, txt) in enumerate(I):
        btn = QtWidgets.QPushButton(meth)
        le = QtWidgets.QLineEdit()
        le.setText(txt)
        btn.clicked.connect(lambda _, meth=meth, le=le: fn(meth, le.text()))
        l.addWidget(le, n, 0)
        l.addWidget(btn, n, 1)

    w.setLayout(l)
    w.setWindowTitle("Test all RabbitMQ commands")
    w.show()
    sys.exit(a.exec_())
