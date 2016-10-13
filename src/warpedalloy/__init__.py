#!/usr/bin/env python

from __future__ import absolute_import, print_function

import sys
import os

from socket import socketpair, AF_INET, AF_UNIX, SOCK_STREAM, fromfd

import attr

from twisted.python.usage import Options
from twisted.internet.task import react
from twisted.internet.defer import Deferred, inlineCallbacks
from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet.protocol import Protocol, Factory, ProcessProtocol
from twisted.protocols.amp import AMP, Command, Descriptor, Unicode
from twisted.internet.unix import Server as UNIXServer
from twisted.logger import (
    eventAsJSON, globalLogBeginner, Logger, formatEventAsClassicLogText,
    eventFromJSON,
)

from twisted.web.server import Site
from twisted.web.static import Data

from ._version import __version__

STDIN = 0
STDOUT = 1
STDERR = 2
MAGIC_FILE_DESCRIPTOR = 7


@attr.s
class SendToSubprocess(Protocol, object):
    """

    """
    mpm = attr.ib()
    def connectionMade(self):
        """

        """
        transport = self.transport
        transport.stopReading()
        transport.stopWriting()
        skt = transport.getHandle()

        sent = self.mpm.sendOutFileDescriptor(skt.fileno())

        @sent.addBoth
        def inevitably(result):
            skt.close()
            return result



class ManagerOptions(Options, object):
    """

    """

    @inlineCallbacks
    def go(self, reactor):
        """

        """
        mgr = MPMManager(reactor)
        endpoint = TCP4ServerEndpoint(reactor, 8123)
        yield endpoint.listen(Factory.forProtocol(
            lambda: SendToSubprocess(mgr)))
        yield Deferred()



class SendDescriptor(Command, object):
    """

    """
    arguments = [("descriptor", Descriptor())]



class LogReceived(Command, object):
    """

    """
    arguments = [("message", Unicode())]
    requiresAnswer = False



class ConnectionFromManager(AMP, object):
    """

    """

    _log = Logger()

    def __init__(self, reactor, factory):
        """

        """
        super(ConnectionFromManager, self).__init__()
        self.factory = factory
        self.reactor = reactor


    @SendDescriptor.responder
    def receiveDescriptor(self, descriptor):
        """

        """
        self._log.info(format="adopting new stream connection {descriptor}",
                       descriptor=descriptor)
        self.reactor.adoptStreamConnection(descriptor, AF_INET, self.factory)
        return {}


    def sendLog(self, eventDictionary):
        """

        """
        eventText = eventAsJSON(eventDictionary)
        self.callRemote(LogReceived, message=eventText)


    def connectionLost(self, reason):
        """

        """
        self.reactor.stop()



class WorkerOptions(Options, object):
    """

    """

    def go(self, reactor):
        """

        """
        data = Data("Hello world\n", "text/plain")
        data.putChild("", data)
        factory = Site(data)

        # TODO: adoptStreamConnection should really support AF_UNIX
        protocol = ConnectionFromManager(reactor, factory)
        skt = fromfd(MAGIC_FILE_DESCRIPTOR, AF_UNIX, SOCK_STREAM)
        os.close(MAGIC_FILE_DESCRIPTOR)
        serverTransport = UNIXServer(skt, protocol, None, None, 1234, reactor)
        protocol.makeConnection(serverTransport)
        serverTransport.startReading()

        globalLogBeginner.beginLoggingTo([protocol.sendLog])
        factory.doStart()

        return Deferred()



class CommandLineOptions(Options, object):
    """

    """
    synopsis = "Usage: warped_alloy [options]"

    subCommands = [
        # ['command-name', 'command-shortcut', ParserClass, documentation]
        ['manager', 'm', ManagerOptions, 'For managing'],
        ['worker', 'w', WorkerOptions, 'For workering'],
    ]

    defaultSubCommand = 'manager'



class OneWorkerProtocol(AMP, object):
    """

    """

    def sendFD(self, fileDescriptor):
        """

        """
        return self.callRemote(SendDescriptor, descriptor=fileDescriptor)


    @LogReceived.responder
    def oneLogMessage(self, message):
        """

        """
        evt = eventFromJSON(message)
        text = formatEventAsClassicLogText(evt)
        messageBytes = (text).encode("utf-8")
        os.write(STDERR, messageBytes)
        return {}



@attr.s
class MPMManager(object):
    """

    """
    reactor = attr.ib()
    openSubprocessConnections = attr.ib(default=attr.Factory(list))

    def sendOutFileDescriptor(self, fileDescriptor):
        if not self.openSubprocessConnections:
            self.newSubProcess()
        return self.openSubprocessConnections[0].sendFD(fileDescriptor)


    def newSubProcess(self):
        """

        """
        here, there = socketpair(AF_UNIX, SOCK_STREAM)
        owp = OneWorkerProtocol()
        serverTransport = UNIXServer(here, owp, None, None, 4321, self.reactor)
        owp.makeConnection(serverTransport)
        argv = [sys.executable, __file__, b'w']
        self.reactor.spawnProcess(
            ProcessProtocol(), argv[0], args=argv, env=os.environ.copy(),
            childFDs={STDIN: 'w', STDOUT: 'r', STDERR: 'r',
                      MAGIC_FILE_DESCRIPTOR: there.fileno()}
        )
        there.close()
        serverTransport.startReading()
        self.openSubprocessConnections.append(owp)


def main(reactor):
    """

    """
    clo = CommandLineOptions()
    clo.parseOptions(sys.argv[1:])
    subCommandParser = clo.subOptions
    return subCommandParser.go(reactor)


__all__ = ["__version__"]
