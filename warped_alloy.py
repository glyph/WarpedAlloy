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

class ManagerServerNotReallyProtocol(Protocol, object):
    """
    
    """

    def connectionMade(self):
        """
        
        """
        transport = self.transport
        # goodbye, sweet reactor
        transport.stopReading()
        transport.stopWriting()

        socketObject = transport.getHandle()
        self.factory.mpmManager.sendOutFileDescriptor(socketObject.fileno())
        socketObject.close()



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
        print("manager-ing")


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
        print("CFM")


    def connectionLost(self, reason):
        """
        
        """
        super(ConnectionFromManager, self).connectionLost(reason)
        print("CL")


    @SendDescriptor.responder
    def receiveDescriptor(self, descriptor):
        """
        
        """
        print("receivering")
        self.reactor.adoptStreamConnection(descriptor, AF_INET, self.factory)
        print("receivated")
        return {}


    @Ping.responder
    def pung(self):
        """
        
        """
        print("received subprocess ping")
        return {}



class WorkerOptions(Options, object):
    """
    
    """

    def postOptions(self):
        """
        
        """
        print("worker-ing")


    def go(self, reactor):
        """
        
        """
        data = Data("Hello world", "text/plain")
        data.putChild("", data)
        factory = Site(data)

        # TODO: adoptStreamConnection should really support AF_UNIX
        protocol = ConnectionFromManager(reactor, factory)
        fileDescriptor = 7
        skt = fromfd(fileDescriptor, AF_UNIX, SOCK_STREAM)
        print("fromfd", skt)
        # os.close(fileDescriptor)
        serverTransport = UNIXServer(skt, protocol, None, None, 1234, reactor)
        print("transported")
        protocol.makeConnection(serverTransport)
        print("reading")
        serverTransport.startReading()
        print("waiting...")
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
        print("sub-out:", data)


    def errReceived(self, data):
        """
        
        """
        print("sub-err:", data)


    def processExited(self, reason):
        """
        
        """
        print("exit?", reason)


    def processEnded(self, reason):
        """
        
        """
        print("ended?", reason)



class OneWorkerProtocol(AMP, object):
    """
    
    """

    def connectionMade(self):
        """
        
        """
        print("OWP_CM")


    def connectionLost(self, reason):
        """
        
        """
        print("OWP_CL", reason)
        super(OneWorkerProtocol, self).connectionLost(reason)


    @inlineCallbacks
    def sendFD(self, fileDescriptor):
        """
        
        """
        print("SFD")
        result1 = yield self.callRemote(Ping)
        print("sending??????", result1, fileDescriptor)
        d = self.callRemote(SendDescriptor,
                            descriptor=fileDescriptor)
        print("send...ing?", d)
        result = yield d
        print("sended/!?@?!", result)



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
        print("argv?", argv)
        procTrans = self.reactor.spawnProcess(
            MyProcessProtocol(self), sys.executable,
            args=argv,
            env=os.environ.copy(),
            childFDs={
                0: 'w',
                1: 'r',
                2: 'r',
                7: there.fileno(),
            }
        )
        print(procTrans)
        # there.close()
        serverTransport.startReading()
        self.openSubprocessConnections.append(owp)


@react
def main(reactor):
    """
    
    """
    print("BOOTSTRAP")
    clo = CommandLineOptions()
    clo.parseOptions(sys.argv[1:])
    subCommandParser = clo.subOptions
    return subCommandParser.go(reactor)
