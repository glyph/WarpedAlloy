#!/usr/bin/env python

import __main__

import sys
import os

from socket import socketpair

import attr

from twisted.python.usage import Options
from twisted.internet.task import react
from twisted.internet.address import UNIXAddress
from twisted.internet.defer import Deferred, inlineCallbacks
from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet.protocol import Protocol, Factory, ProcessProtocol

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
        self.factory.mpmManager.sendOutFileDescriptor(socketObject)
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
        endpoint = TCP4ServerEndpoint(reactor)
        msf = ManagerServerFactory(mgr)
        yield endpoint.listen(msf)
        yield Deferred()



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


@attr.s
class MPMManager(object):
    """
    
    """
    reactor = attr.ib()
    openSubprocessConnections = attr.ib(default=attr.Factory(list))

    def sendOutFileDescriptor(self, fileDescriptor):
        pass


    def newSubProcess(self):
        """
        
        """
        here, there = socketpair(AF_UNIX, STOCK_STREAM)
        from twisted.internet.unix import Server as UNIXServer
        UNIXServer(here, OneWorkerProtocol(), UNIXAddress(None), None, )
        self.reactor.spawnProcess(
            MyProcessProtocol(self), sys.executable,
            args=[sys.executable, __main__.__file__], env=os.environ.copy(),
            childFDs={
                0: 'w',
                1: 'r',
                2: 'r',
                7: there.fileno(),
            }
        )



@react
def main(reactor):
    """
    
    """
    clo = CommandLineOptions()
    clo.parseOptions(sys.argv[1:])
    subCommandParser = clo.subCommand
    return subCommandParser.go(reactor)
