'''This class extends pexpect.spawn to specialize setting up SSH connections.
This adds methods for login, logout, and expecting the shell prompt.

PEXPECT LICENSE

    This license is approved by the OSI and FSF as GPL-compatible.
        http://opensource.org/licenses/isc-license.txt

    Copyright (c) 2012, Noah Spurrier <noah@noah.org>
    PERMISSION TO USE, COPY, MODIFY, AND/OR DISTRIBUTE THIS SOFTWARE FOR ANY
    PURPOSE WITH OR WITHOUT FEE IS HEREBY GRANTED, PROVIDED THAT THE ABOVE
    COPYRIGHT NOTICE AND THIS PERMISSION NOTICE APPEAR IN ALL COPIES.
    THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
    WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
    MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
    ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
    WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
    ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
    OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

'''

from pexpect import ExceptionPexpect, TIMEOUT, EOF
from pexpect.pxshell import pxshell, ExceptionPxShell
import time
import os

__all__ = ['ExceptionPxssh', 'pxssh']

# Exception classes used by this module.
class ExceptionPxssh(ExceptionPxShell):
    '''Raised for pxssh exceptions.
    '''


class pxssh (pxshell):
    '''This class extends pexpect.spawn to specialize setting up SSH
    connections. This adds methods for login, logout, and expecting the shell
    prompt. It does various tricky things to handle many situations in the SSH
    login process. For example, if the session is your first login, then pxssh
    automatically accepts the remote certificate; or if you have public key
    authentication setup then pxssh won't wait for the password prompt.

    pxssh uses the shell prompt to synchronize output from the remote host. In
    order to make this more robust it sets the shell prompt to something more
    unique than just $ or #. This should work on most Borne/Bash or Csh style
    shells.

    Example that runs a few commands on a remote server and prints the result::

        import pxssh
        import getpass
        try:
            s = pxssh.pxssh()
            hostname = raw_input('hostname: ')
            username = raw_input('username: ')
            password = getpass.getpass('password: ')
            s.login(hostname, username, password)
            s.sendline('uptime')   # run a command
            s.prompt()             # match the prompt
            print(s.before)        # print everything before the prompt.
            s.sendline('ls -l')
            s.prompt()
            print(s.before)
            s.sendline('df')
            s.prompt()
            print(s.before)
            s.logout()
        except pxssh.ExceptionPxssh as e:
            print("pxssh failed on login.")
            print(e)

    Note that if you have ssh-agent running while doing development with pxssh
    then this can lead to a lot of confusion. Many X display managers (xdm,
    gdm, kdm, etc.) will automatically start a GUI agent. You may see a GUI
    dialog box popup asking for a password during development. You should turn
    off any key agents during testing. The 'force_password' attribute will turn
    off public key authentication. This will only work if the remote SSH server
    is configured to allow password logins. Example of using 'force_password'
    attribute::

            s = pxssh.pxssh()
            s.force_password = True
            hostname = raw_input('hostname: ')
            username = raw_input('username: ')
            password = getpass.getpass('password: ')
            s.login (hostname, username, password)
    '''

    def __init__ (self, timeout=30, maxread=2000, searchwindowsize=None,
                    logfile=None, cwd=None, env=None, interpreter=None):

        pxshell.__init__(self, timeout=timeout, maxread=maxread, searchwindowsize=searchwindowsize, logfile=logfile, cwd=cwd, env=env, interpreter=interpreter)
        
        self.name = '<pxssh>'
        self.SSH_OPTS =  [
            "-o 'RSAAuthentication=no'",
            "-o 'PubkeyAuthentication=no'"
        ]
# Disabling host key checking, makes you vulnerable to MITM attacks.
#                + " -o 'StrictHostKeyChecking=no'"
#                + " -o 'UserKnownHostsFile /dev/null' ")
        # Disabling X11 forwarding gets rid of the annoying SSH_ASKPASS from
        # displaying a GUI password dialog. I have not figured out how to
        # disable only SSH_ASKPASS without also disabling X11 forwarding.
        # Unsetting SSH_ASKPASS on the remote side doesn't disable it! Annoying!
        #self.SSH_OPTS = "-x -o'RSAAuthentication=no' -o 'PubkeyAuthentication=no'"
        self.force_password = False


    def login (self, server, username, password='', terminal_type='ansi',
                original_prompt=r"[#$]", login_timeout=10, port=None,
                auto_prompt_reset=True, ssh_key=None, quiet=True,
                sync_multiplier=1, check_local_ip=True):
        '''This logs the user into the given server.'''
        print("pxssh::login()")
        # select the options 
        ssh_options = []
        if quiet:
            ssh_options += [ '-q' ]
        if not check_local_ip:
            ssh_options += [ "-o 'NoHostAuthenticationForLocalhost=yes'" ]
        if self.force_password:
            ssh_options += self.SSH_OPTS
        if port is not None:
            ssh_options += [ '-p %s'%(str(port)) ]
        if ssh_key is not None:
            try:
                os.path.isfile(ssh_key)
            except:
                raise ExceptionPxssh('private ssh key does not exist')
            ssh_options += [ '-i %s' % (ssh_key) ]

        # format the command adequately
        ssh_options += [ '-l', username, server ]
        
        # run the common login routine
        pxshell.login(self,
                      'ssh', ' '.join(ssh_options),
                      username, password,
                      login_timeout,
                      auto_prompt_reset,
                      sync_multiplier)

    def _login_state_machine(self, username, password):
        '''SSH specific login state machine...'''
        print("pxssh::_login_state_machine()")
        # ssh responses...
        print("default_prompt:  " + self.interpreter.default_prompt())
        print("timeout:  %d" % self.login_timeout)
        responses = [
            "(?i)are you sure you want to continue connecting",
            self.interpreter.default_prompt(),
            "(?i)(?:password)|(?:passphrase for key)",
            "(?i)permission denied",
            "(?i)terminal type",
            #TIMEOUT
        ]
        extras = [
            "(?i)connection closed by remote host"
        ]

        
        # the instance is spawned, now interact
        i = self.expect(responses + extras, timeout=self.login_timeout)
        print("A: %d" % i)

        # First phase
        if i==0:
            # New certificate -- always accept it.
            # This is what you get if SSH does not have the remote host's
            # public key stored in the 'known_hosts' cache.
            self.sendline("yes")
            i = self.expect(responses)
        print("B: %d" % i)
        if i==2: # password or passphrase
            self.sendline(password)
            i = self.expect(responses)
        print("C: %d" % i)
        if i==4:
            self.sendline(terminal_type)
            i = self.expect(responses)

        # Second phase
        print("D: %d" % i)
        if i==0:
            # This is weird. This should not happen twice in a row.
            self.close()
            raise ExceptionPxssh('Weird error. Got "are you sure" prompt twice.')
        elif i==1: # can occur if you have a public key pair set to authenticate.
            ### TODO: May NOT be OK if expect() got tricked and matched a false prompt.
            pass
        elif i==2: # password prompt again
            # For incorrect passwords, some ssh servers will
            # ask for the password again, others return 'denied' right away.
            # If we get the password prompt again then this means
            # we didn't get the password right the first time.
            self.close()
            raise ExceptionPxssh('password refused')
        elif i==3: # permission denied -- password was bad.
            self.close()
            raise ExceptionPxssh('permission denied')
        elif i==4: # terminal type again? WTF?
            self.close()
            raise ExceptionPxssh('Weird error. Got "terminal type" prompt twice.')
        elif i==5: # Timeout
            #This is tricky... I presume that we are at the command-line prompt.
            #It may be that the shell prompt was so weird that we couldn't match
            #it. Or it may be that we couldn't log in for some other reason. I
            #can't be sure, but it's safe to guess that we did login because if
            #I presume wrong and we are not logged in then this should be caught
            #later when I try to set the shell prompt.
            pass
        elif i==6: # Connection closed by remote host
            self.close()
            raise ExceptionPxssh('connection closed')
        else: # Unexpected
            self.close()
            raise ExceptionPxssh('unexpected login response')
