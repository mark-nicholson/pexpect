'''This module provides common shell definition classes.

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

# global prompt uniqueness
UNIQUE_TAG = '[PEXPECT]'

class pxcli(object):

    def __init__(self,
                 terminal_type='ansi',
                 default_prompt=r"[#$]",
                 unique_prompt="\[PEXPECT\][\$\#] ",
                 set_prompt_cmd="PS1='[PEXPECT]\$ '"):
        '''Basically defaults to /bin/sh.'''
        
        self._tag = UNIQUE_TAG
        self._terminal_type = terminal_type
        self._default_prompt = default_prompt
        self._unique_prompt = unique_prompt
        self._set_prompt_cmd = set_prompt_cmd

    def terminal_type(self):
        return self._terminal_type

    def default_prompt(self):
        return self._default_prompt

    def unique_prompt(self):
        return self._unique_prompt

    def set_prompt_cmd(self):
        return self._set_prompt_cmd


class pxsh(pxcli):
    '''Support class for /bin/sh compatible shells'''
    pass

class pxcsh(pxsh):
    '''Support class for /bin/csh compatible shells'''
    def __init__(self):
        pxsh.__init__(self,
                      set_prompt_cmd = "set prompt='[PEXPECT]\$ '")
