import logging
import os

from tornado.ioloop import IOLoop

from handlers import WatcherServer, MessageServer


logging.basicConfig(level=logging.DEBUG)
log = logging.Logger(__name__)

def main():

    watchers = set()
    sources_statistics = dict()

    message_server = MessageServer(watchers, sources_statistics)
    message_port = int(os.environ.get("MESSAGE_PORT", 8888))
    message_server.listen(message_port)

    watcher_server = WatcherServer(watchers, sources_statistics)
    watcher_port = int(os.environ.get("WATCHER_PORT", 8889))
    watcher_server.listen(watcher_port)

    IOLoop.current().start()


if __name__ == "__main__":
    main()
