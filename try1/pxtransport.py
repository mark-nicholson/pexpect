#
# Connection Transport
#

# Exception classes used by this module.
class ExceptionPxTransport(ExceptionPexpect):
    '''Raised for pxtransport exceptions.
    '''

class pxtransport(object):
    '''The carrier of the info.'''

    def __init__(self, hostname=None, info=None):
        if hostname is None and info is None:
            raise ExceptionPxTransport("insufficient connection info")

        self.info = info
        if self.info is None:
            self.info = find_info(hostname)

    def executable(self):
        '''Provide the program name to run'''
        return ''

    def exec_options(self):
        '''Setup the executable's needed command line options'''
        return []

    def options(self):
        '''Supply additional configuration parameters for pexpect'''
        return []
