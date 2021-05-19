"""Ubuntu Kylin hackathon chat server.

Multithreading and asynchronous server for Chat.

"""
import os

from argparse import ArgumentParser
from socket import (
    socket,
    AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
)
from threading import Thread
from typing import Any, List, Tuple


class Server(Thread):
    """Server for chat.

    It supports manage connections that connected to itself, supported
    operations include connect and close.

    It instantiated by HOST, PORT, and CONNECTIONS.  The HOST is a
    standard IP address or domain, the PORT is a number in range of
    Unix port, and the CONNECTIONS is a list of Connection objects
    representing the active connections.

    """

    def __init__(self, host: str, port: int):
        """Server constructor.

        Instantiates by specified HOST, PORT, and a empty list of
        HackServerSocket.

        """
        super().__init__()
        self.connections: List[Connection] = []
        self.host = host
        self.port = port

    def run(self) -> None:
        """Service start.

        It creates a listening socket with HOST and PORT that provided
        by instance.  The listening socket is use reliable TCP
        flow-controlled data streams.

        It supports reuse the same port when client connection was
        closed only for a few minutes.

        """
        service_socket = socket(AF_INET, SOCK_STREAM)
        service_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        service_socket.bind((self.host, self.port))

        service_socket.listen(1)
        print(
            "HackChat server listening at",
            service_socket.getsockname()
        )

        while True:
            client_socket, descriptor = service_socket.accept()
            print("Accepted a new connection from {} to {}".format(
                client_socket.getpeername(),
                client_socket.getsockname(),
            ))

            server_socket = Connection(
                client_socket, descriptor, self
            )
            server_socket.start()
            print(
                "Ready to receive messages from",
                client_socket.getpeername()
            )

            self.connections.append(server_socket)

    def broadcast(self,
                  message: str,
                  origin: Tuple[socket, Any]
                  ) -> None:
        """Broadcast message for connected clients.

        This method is used to send MESSAGE to all connected clients,
        except the origin client.

        """
        for connection in self.connections:
            if connection.descriptor != origin:
                connection.send(message)

    def close_connection(self,
                         connection: Any
                         ) -> None:
        """Cancel a connection instance from connections list.
        
        Remove a client HackChatServerSocket instance from connections
        after the client is closed.

        """
        self.connections.remove(connection)


class Connection(Thread):
    """Socket for chat connection.

    It supports make communications between a connected client and
    server.

    It instantiated by CLIENT_SOCKET, DESCRIPTOR, and SERVER.  The
    CLIENT_SOCKET is a connected socket, the DESCRIPTOR is description
    of connection, SERVER is the parent thread of current instance.

    """

    def __init__(self,
                 client_socket: socket,
                 descriptor: Tuple[socket, Any],
                 connected_server: Server
                 ):
        super().__init__()
        self.client_socket = client_socket
        self.descriptor = descriptor
        self.server = connected_server

    def run(self) -> None:
        """Interactive Data Processing.
        
        This method broadcasts the message that is received from the
        connected client to all other clients.  If the client has left
        the connection, closes the connected socket and removes itself
        from the connection threads list of the parent HackChatServer
        instance.

        """
        while True:
            message = self.client_socket.recv(1024).decode("utf-8")

            if message is not None:
                print("{} says {!r}".format(self.descriptor, message))
                self.server.broadcast(message, self.descriptor)

            else:
                print("{} has closed the connection".format(
                    self.descriptor
                ))
                self.client_socket.close()
                self.server.close_connection(self)

                return

    def send(self, message: str) -> None:
        """Send MESSAGE to server.

        This method sends a MESSAGE to connected server.

        """
        self.client_socket.sendall(message.encode("utf-8"))


def stop(activated_server: Server):
    """Stop HackChat service.

    Allows the server administrator to shut down the server.  Typing q
    in the command line will close all active connections and exit the
    application.

    """
    while True:
        key_sequence = input('')
        if key_sequence == 'q':
            print('Closing all connections...')
            for connection in activated_server.connections:
                connection.client_socket.close()
            print('Stop the server...')
            os._exit(0)


if __name__ == '__main__':
    parser = ArgumentParser(description='Chatroom Server')
    parser.add_argument('host', help='Interface the server listens at')
    parser.add_argument('-p', metavar='PORT', type=int, default=10080,
                        help='TCP port (default 10080)')
    args = parser.parse_args()

    server = Server(args.host, args.p)
    server.start()

    _exit = Thread(target=exit, args=(server,))
    _exit.start()
