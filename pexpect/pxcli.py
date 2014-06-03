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

    def __init__(self):
        self.tag = UNIQUE_TAG
        self.prompt_fmt = '%s>'

    def terminal_type(self):
        raise NotImplementedError()

    def default_prompt(self):
        raise NotImplementedError()

    def unique_prompt(self):
        raise NotImplementedError()

    def set_prompt_cmd(self):
        raise NotImplementedError()

class pxsh(pxcli):
    '''Support class for /bin/sh compatible shells'''

    def terminal_type(self):
        return 'ansi'

    def default_prompt(self):
        return r"[#$]"

    def unique_prompt(self):
        return "\[PEXPECT\][\$\#] "

    def set_prompt_cmd(self):
        return  "PS1='[PEXPECT]\$ '"

class pxcsh(pxsh):
    '''Support class for /bin/csh compatible shells'''

    def set_prompt_cmd(self):
        return "set prompt='[PEXPECT]\$ '"

