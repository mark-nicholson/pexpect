#
#  Login behavioural class
#

# Exception classes used by this module.
class ExceptionPxLogin(ExceptionPexpect):
    '''Raised for pxlogin exceptions.
    '''

class pxlogin (object):
    '''
    Login management
    '''
    def __init__(self, transport, interpreter, timeout=30):
        '''Setup the basic login parameters.'''
        self.timeout = timeout
        self.transport = transport
        self.interpreter = interpreter
    
    def login (self,
               username='', password='',
               timeout=None):
        '''This logs the user into the given server.

        It uses
        'original_prompt' to try to find the prompt right after login. When it
        finds the prompt it immediately tries to reset the prompt to something
        more easily matched. The default 'original_prompt' is very optimistic
        and is easily fooled. It's more reliable to try to match the original
        prompt as exactly as possible to prevent false matches by server
        strings such as the "Message Of The Day". On many systems you can
        disable the MOTD on the remote server by creating a zero-length file
        called :file:`~/.hushlogin` on the remote server. If a prompt cannot be found
        then this will not necessarily cause the login to fail. In the case of
        a timeout when looking for the prompt we assume that the original
        prompt was so weird that we could not match it, so we use a few tricks
        to guess when we have reached the prompt. Then we hope for the best and
        blindly try to reset the prompt to something more unique. If that fails
        then login() raises an :class:`ExceptionPxssh` exception.

        In some situations it is not possible or desirable to reset the
        original prompt. In this case, pass ``auto_prompt_reset=False`` to
        inhibit setting the prompt to the UNIQUE_PROMPT. Remember that pxssh
        uses a unique prompt in the :meth:`prompt` method. If the original prompt is
        not reset then this will disable the :meth:`prompt` method unless you
        manually set the :attr:`PROMPT` attribute.
        '''
        print("pxlogin::login()")
        # archive the options
        if timeout is not None:
            self.timeout = timeout
        #self.sync_multiplier = sync_multiplier        

        # double check
        if self.transport is None:
            raise ExceptionPxLogin('No transport provided')
        if self.interpreter is None:
            raise ExceptionPxLogin('No interpreter provided')

        # fire it up.
        self.transport.ignition()

        # run the login sequence...
        self._login_state_machine(username, password)

        #
        # Login system should be done
        #
        
        # try to resolve the interface
        if not self.interpreter.sync_prompt(self.sync_multiplier, login=True):
            self.close()
            raise ExceptionPxShell('could not synchronize with original prompt')

        # We appear to be in.
        # set shell prompt to something unique.
        if auto_prompt_reset:
            if not self.set_unique_prompt():
                self.close()
                raise ExceptionPxShell('could not set shell prompt '
                                        '(recieved: %r, expected: %r).' % (
                                            self.before,
                                            self.interpreter.unique_prompt(),))

        # update to the prompt
        newinfo = self.prompt(timeout=0.1)


    def _login_state_machine(self, username, password):
        '''Sequence of steps to "login"'''
        print("pxshell::_login_state_machine()")
        # work on assumption of "basic" login steps
        self.expect( [ "(?i)(?:login)", "(?i)(?:user\s*name)", TIMEOUT ], timeout=self.login_timeout )
        self.sendline(username)
        self.expect( [ "(?i)(?:password)", TIMEOUT ], timeout=self.login_timeout )
        self.sendline(password)


    def logout (self):
        '''Sends exit to the remote shell.

        If there are stopped jobs then this automatically sends exit twice.
        '''

        # disconnect the interpreter
        self.interpreter.close()
        
        self.sendline("exit")
        index = self.expect([EOF, "(?i)there are stopped jobs"])
        if index==1:
            self.sendline("exit")
            self.expect(EOF)
        self.close()

