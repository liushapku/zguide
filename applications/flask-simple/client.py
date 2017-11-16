from socketIO_client import SocketIO, SocketIONamespace, BaseNamespace

class Namespace(SocketIONamespace):
    def on_connect(self):
        print('[Connected]')

    def on_reconnect(self):
        print('[Reconnected]')

    def on_disconnect(self):
        print('[Disconnected]')

    def on_message(self, msg):
        print(type(msg), msg)

socketIO = SocketIO('192.168.1.185', 5000, Namespace,
                    wait_for_connection=True)
# print('I am here')
# Listen
# socketIO.on('aaa_response', on_aaa_response)
# socketIO.send(dict(to='Alice', message='hello Alice'))
socketIO.wait()
#
# # Stop listening
# socketIO.off('aaa_response')
# socketIO.emit('aaa')
# socketIO.wait(seconds=1)
#
# # Listen only once
# socketIO.once('aaa_response', on_aaa_response)
# socketIO.emit('aaa')  # Activate aaa_response
# socketIO.emit('aaa')  # Ignore
# socketIO.wait(seconds=1)
