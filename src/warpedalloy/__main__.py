# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

if __name__ == '__main__':
    from warpedalloy import main
    from twisted.internet.task import react

    react(main)
