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

from pexpect import ExceptionPexpect, TIMEOUT, EOF, spawn
import time
import os

__all__ = [
    'ExceptionPxShell',
    'pxshell', 'pxinterpreter', 'pxsh', 'pxcsh',
    'UNIQUE_TAG'
]

# global prompt uniqueness
UNIQUE_TAG = '[PEXPECT]'

class pxinterpreter(object):

    def __init__(self):
        self.tag = UNIQUE_TAG
        self.prompt_fmt = '%s\$ '

    def terminal_type(self):
        raise NotImplementedError()

    def default_prompt(self):
        raise NotImplementedError()

    def unique_prompt(self):
        raise NotImplementedError()

    def set_prompt_cmd(self):
        raise NotImplementedError()

class pxsh(pxinterpreter):

    def terminal_type(self):
        return 'ansi'

    def default_prompt(self):
        return r"[#$]"

    def unique_prompt(self):
        return self.prompt_fmt % self.tag

    def set_prompt_cmd(self):
        if tag is not None:
            self.tag = tag
        return "PS1='%s'" % self.unique_prompt()

class pxcsh(pxsh):

    def set_prompt_cmd(self):
        return "set prompt='%s'" % self.unique_prompt()

    
    
# Exception classes used by this module.
class ExceptionPxShell(ExceptionPexpect):
    '''Raised for pxshell exceptions.
    '''

class pxshell (spawn):
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

        spawn.__init__(self, None, timeout=timeout, maxread=maxread, searchwindowsize=searchwindowsize, logfile=logfile, cwd=cwd, env=env)

        self.name = '<pxshell>'

        #SUBTLE HACK ALERT! Note that the command that SETS the prompt uses a
        #slightly different string than the regular expression to match it. This
        #is because when you set the prompt the command will echo back, but we
        #don't want to match the echoed command. So if we make the set command
        #slightly different than the regex we eliminate the problem. To make the
        #set command different we add a backslash in front of $. The $ doesn't
        #need to be escaped, but it doesn't hurt and serves to make the set
        #prompt command different than the regex.

        # prepare a basic interpreter
        self.interpreter = interpreter
        print("interpreter: " + str(self.interpreter))

    def levenshtein_distance(self, a, b):
        '''This calculates the Levenshtein distance between a and b.
        '''

        n, m = len(a), len(b)
        if n > m:
            a,b = b,a
            n,m = m,n
        current = range(n+1)
        for i in range(1,m+1):
            previous, current = current, [i]+[0]*n
            for j in range(1,n+1):
                add, delete = previous[j]+1, current[j-1]+1
                change = previous[j-1]
                if a[j-1] != b[i-1]:
                    change = change + 1
                current[j] = min(add, delete, change)
        return current[n]

    def try_read_prompt(self, timeout_multiplier):
        '''This facilitates using communication timeouts to perform
        synchronization as quickly as possible, while supporting high latency
        connections with a tunable worst case performance. Fast connections
        should be read almost immediately. Worst case performance for this
        method is timeout_multiplier * 3 seconds.
        '''

        # maximum time allowed to read the first response
        first_char_timeout = timeout_multiplier * 0.5

        # maximum time allowed between subsequent characters
        inter_char_timeout = timeout_multiplier * 0.1

        # maximum time for reading the entire prompt
        total_timeout = timeout_multiplier * 3.0

        prompt = b''
        begin = time.time()
        expired = 0.0
        timeout = first_char_timeout

        while expired < total_timeout:
            try:
                prompt += self.read_nonblocking(size=1, timeout=timeout)
                expired = time.time() - begin # updated total time expired
                timeout = inter_char_timeout 
            except TIMEOUT:
                break

        return prompt

    def sync_original_prompt (self, sync_multiplier=1.0):
        '''This attempts to find the prompt. Basically, press enter and record
        the response; press enter again and record the response; if the two
        responses are similar then assume we are at the original prompt.
        This can be a slow function. Worst case with the default sync_multiplier
        can take 12 seconds. Low latency connections are more likely to fail
        with a low sync_multiplier. Best case sync time gets worse with a
        high sync multiplier (500 ms with default). '''
        print("pxshell::sync_original_prompt()")

        # mop up the cruft so far
        #spew = 'crap'
        #while len(spew) > 0:
        #    try:
        #        spew = self.read_nonblocking(64, timeout=0)
        #        print("spew: '%s'" % spew)
        #    except TIMEOUT:
        #        break
        
        # All of these timing pace values are magic.
        # I came up with these based on what seemed reliable for
        # connecting to a heavily loaded machine I have.
        self.sendline()
        time.sleep(0.1)

        try:
            # Clear the buffer before getting the prompt.
            self.try_read_prompt(sync_multiplier)
        except TIMEOUT:
            pass

        self.sendline()
        x = self.try_read_prompt(sync_multiplier)

        self.sendline()
        a = self.try_read_prompt(sync_multiplier)

        self.sendline()
        b = self.try_read_prompt(sync_multiplier)

        ld = self.levenshtein_distance(a,b)
        len_a = len(a)
        if len_a == 0:
            return False
        if float(ld)/len_a < 0.4:
            return True
        return False

    def login (self,
               executable, options='',
               username='', password='',
               login_timeout=1,
               auto_prompt_reset=True,
               sync_multiplier=1):
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
        print("pxshell::login()")
        # archive the options
        self.login_timeout = login_timeout
        self.sync_multiplier = sync_multiplier        

        # double check
        if executable == '':
            raise ExceptionPxShell('Unconfigured child application: %s' % executable)

        # keep this simple in here
        cmd = executable + ' ' + options

        # fire it up.
        spawn._spawn(self, cmd)

        # run the login sequence...
        self._login_state_machine(username, password)

        # try to resolve the interface
        if not self.sync_original_prompt(self.sync_multiplier):
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
        self.sendline("exit")
        index = self.expect([EOF, "(?i)there are stopped jobs"])
        if index==1:
            self.sendline("exit")
            self.expect(EOF)
        self.close()

    def prompt(self, timeout=-1):
        '''Match the next shell prompt.

        This is little more than a short-cut to the :meth:`~pexpect.spawn.expect`
        method. Note that if you called :meth:`login` with
        ``auto_prompt_reset=False``, then before calling :meth:`prompt` you must
        set the :attr:`PROMPT` attribute to a regex that it will use for
        matching the prompt.

        Calling :meth:`prompt` will erase the contents of the :attr:`before`
        attribute even if no prompt is ever matched. If timeout is not given or
        it is set to -1 then self.timeout is used.

        :return: True if the shell prompt was matched, False if the timeout was
                 reached.
        '''

        if timeout == -1:
            timeout = self.timeout
        i = self.expect([self.interpreter.unique_prompt(), TIMEOUT], timeout=timeout)
        if i==1:
            return False
        return True

    def set_unique_prompt(self):
        '''This sets the remote prompt to something more unique than ``#`` or ``$``.
        This makes it easier for the :meth:`prompt` method to match the shell prompt
        unambiguously. This method is called automatically by the :meth:`login`
        method, but you may want to call it manually if you somehow reset the
        shell prompt. For example, if you 'su' to a different user then you
        will need to manually reset the prompt. This sends shell commands to
        the remote host to set the prompt, so this assumes the remote host is
        ready to receive commands.

        Alternatively, you may use your own prompt pattern. In this case you
        should call :meth:`login` with ``auto_prompt_reset=False``; then set the
        :attr:`PROMPT` attribute to a regular expression. After that, the
        :meth:`prompt` method will try to match your prompt pattern.
        '''
        print("pxshell::set_unique_prompt()")
        # shells to try
        if self.interpreter is None:
            stt = [ pxsh(), pxcsh() ]
        else:
            stt = [ self.interpreter ]

        # try to (preemptively) mop up
        #self.sendline("unset PROMPT_COMMAND")

        # cook up a usable prompt
        for sh in stt:
            self.sendline(sh.set_prompt_cmd())
            i = self.expect ([TIMEOUT, sh.unique_prompt()], timeout=10)
            if i > 0:
                self.interpreter = sh
                return True

        # hmm, that didn't go well
        return False

    def cmd(self, command, timeout=-1):
        '''Provide a end-to-end command operation.'''

        # issue the command
        self.sendline(command)

        # get a prompt back
        ok = self.prompt(timeout=timeout)
        if not ok:
            raise ExceptionPxShell('could not synchronize with original prompt')

        # tidy up the response
        lines = self.before.splitlines()

        # omit the "command" part
        return lines[1:]
        
# vi:ts=4:sw=4:expandtab:ft=python:
