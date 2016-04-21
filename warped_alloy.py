#!/usr/bin/env python

import sys

from twisted.python.usage import Options
from twisted.internet.task import react
from twisted.internet.defer import Deferred


class ManagerOptions(Options, object):
    """
    
    """

    def postOptions(self):
        """
        
        """
        print("manager-ing")



class WorkerOptions(Options, object):
    """
    
    """


    def postOptions(self):
        """
        
        """
        print("worker-ing")


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



@react
def main(reactor):
    """
    
    """
    forever = Deferred()

    clo = CommandLineOptions()
    clo.parseOptions(sys.argv[1:])

    return forever
