#
#  A Telnet specific interface
#

from pxshell import pxshell

class pxtelnet (pxshell):
    '''A telnet optimized interface class'''

    def __init__ (self, timeout=30, maxread=2000, searchwindowsize=None,
                    logfile=None, cwd=None, env=None, prompt=None):

        pxshell.__init__(self, None, timeout=timeout, maxread=maxread,
                         searchwindowsize=searchwindowsize, logfile=logfile,
                         cwd=cwd, env=env)

        self.name = '<pxtelnet>'
