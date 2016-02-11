'''
General connection mechanism
'''

import labdb

class pxconnection(object):
    '''A connection to a device'''

    def __init__(self, hostname=None, info=None):

        self.info = info
        if self.info is None:
            self.info = labdb.get_info(hostname)

        # logging
        self.log = []
            
        # create the items required
        self.shell = self.info.shell()
        self.transport = self.info.transport()
        self.login = self.info.login()

    def open(self):
        '''Begin the connection'''
        pass

    def close(self):
        '''Tidy up the connection'''
        pass

    def command(self, task, timeout=-1):
        '''Run a command line on the foreign machine'''
        return self.shell.cmd(task, timeout=timeout)
