#!/usr/bin/env python

from __future__ import absolute_import, print_function

print("FIRST")

import __main__

import sys
import os

from socket import socketpair, AF_INET, AF_UNIX, SOCK_STREAM, fromfd

import attr

from twisted.python.usage import Options
from twisted.internet.task import react
from twisted.internet.defer import Deferred, inlineCallbacks
from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet.protocol import Protocol, Factory, ProcessProtocol
from twisted.protocols.amp import AMP, Command, Descriptor
from twisted.internet.unix import Server as UNIXServer

from twisted.web.server import Site
from twisted.web.static import Data

STDIN = 0
STDOUT = 1
STDERR = 2
MAGIC_FILE_DESCRIPTOR = 7


def show(*args):
    """
    
    """
    print(*args)
    sys.stdout.flush()
    sys.stderr.flush()

class ManagerServerNotReallyProtocol(Protocol, object):
    """
    
    """

    def connectionMade(self):
        """
        
        """
        transport = self.transport
        # goodbye, sweet reactor

        socketObject = transport.getHandle()

        self.factory.mpmManager.sendOutFileDescriptor(socketObject.fileno())

        transport.stopReading()
        transport.stopWriting()



class ManagerServerFactory(Factory, object):
    """
    
    """

    def __init__(self, mpmManager):
        """
        
        """
        self.mpmManager = mpmManager

    protocol = ManagerServerNotReallyProtocol


class ManagerOptions(Options, object):
    """
    
    """

    def postOptions(self):
        """
        
        """
        show("manager-ing")


    @inlineCallbacks
    def go(self, reactor):
        """
        
        """
        mgr = MPMManager(reactor)
        endpoint = TCP4ServerEndpoint(reactor, 8123)
        msf = ManagerServerFactory(mgr)
        yield endpoint.listen(msf)
        mgr.newSubProcess()
        yield Deferred()


class Ping(Command, object):
    """
    
    """


class SendDescriptor(Command, object):
    """
    
    """
    arguments = [("descriptor", Descriptor())]
    response = []
    errors = []


class ConnectionFromManager(AMP, object):
    """
    
    """
    def __init__(self, reactor, factory):
        """
        
        """
        super(ConnectionFromManager, self).__init__()
        self.factory = factory
        self.reactor = reactor


    def connectionMade(self):
        """
        
        """
        show("CFM")


    def connectionLost(self, reason):
        """
        
        """
        super(ConnectionFromManager, self).connectionLost(reason)
        show("CL")


    @SendDescriptor.responder
    def receiveDescriptor(self, descriptor):
        """
        
        """
        show("receivering")
        self.reactor.adoptStreamConnection(descriptor, AF_INET, self.factory)
        show("receivated")
        return {}


    def fileDescriptorReceived(self, descriptor):
        """
        
        """
        show("FDR", descriptor)
        return super(ConnectionFromManager, self).fileDescriptorReceived(descriptor)


    @Ping.responder
    def pung(self):
        """
        
        """
        show("received subprocess ping")
        sys.stdout.flush()
        return {}



class WorkerOptions(Options, object):
    """
    
    """

    def postOptions(self):
        """
        
        """
        show("worker-ing")


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
        show("transported")
        protocol.makeConnection(serverTransport)
        show("reading")
        serverTransport.startReading()
        show("waiting...")
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


@attr.s
class MyProcessProtocol(ProcessProtocol, object):
    """
    
    """
    mpmManager = attr.ib()

    def outReceived(self, data):
        """
        
        """
        show("sub-out:", repr(data))


    def errReceived(self, data):
        """
        
        """
        show("sub-err:", repr(data))


    def processExited(self, reason):
        """
        
        """
        show("exit?", reason)


    def processEnded(self, reason):
        """
        
        """
        show("ended?", reason)



class OneWorkerProtocol(AMP, object):
    """
    
    """

    def connectionMade(self):
        """
        
        """
        show("OWP_CM")


    def connectionLost(self, reason):
        """
        
        """
        show("OWP_CL", reason)
        super(OneWorkerProtocol, self).connectionLost(reason)


    @inlineCallbacks
    def sendFD(self, fileDescriptor):
        """
        
        """
        show("pinging...")
        result1 = yield self.callRemote(Ping)
        show("pinged!", result1)
        show("sending??????", result1, fileDescriptor)
        d = self.callRemote(SendDescriptor,
                            descriptor=fileDescriptor)
        show("send...ing?")
        result = yield d
        show("sended/!?@?!", result)



@attr.s
class MPMManager(object):
    """
    
    """
    reactor = attr.ib()
    openSubprocessConnections = attr.ib(default=attr.Factory(list))

    def sendOutFileDescriptor(self, fileDescriptor):
        if not self.openSubprocessConnections:
            self.newSubProcess()
        self.openSubprocessConnections[0].sendFD(fileDescriptor)


    def newSubProcess(self):
        """
        
        """
        here, there = socketpair(AF_UNIX, SOCK_STREAM)
        owp = OneWorkerProtocol()
        serverTransport = UNIXServer(here, owp,
                                     None, None, 4321,
                                     self.reactor)
        owp.makeConnection(serverTransport)
        script = __main__.__file__
        argv = [sys.executable, script, b'w']
        show("argv?", argv)
        self.reactor.spawnProcess(
            MyProcessProtocol(self), sys.executable,
            args=argv,
            env=os.environ.copy(),
            childFDs={STDIN: 'w', STDOUT: 'r', STDERR: 'r',
                      MAGIC_FILE_DESCRIPTOR: there.fileno()}
        )
        there.close()
        serverTransport.startReading()
        self.openSubprocessConnections.append(owp)


@react
def main(reactor):
    """
    
    """
    show("BOOTSTRAP")
    clo = CommandLineOptions()
    clo.parseOptions(sys.argv[1:])
    subCommandParser = clo.subOptions
    return subCommandParser.go(reactor)
