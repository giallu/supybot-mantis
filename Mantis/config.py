###
# Copyright (c) 2007, Gianluca Sforna
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions, and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions, and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the name of the author of this software nor the name of
#     contributors to this software may be used to endorse or promote products
#     derived from this software without specific prior written consent.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

###

import supybot.conf as conf
import supybot.registry as registry

def configure(advanced):
    # This will be called by supybot to configure this module.  advanced is
    # a bool that specifies whether the user identified himself as an advanced
    # user or not.  You should effect your configuration by manipulating the
    # registry as appropriate.
    from supybot.questions import expect, anything, something, yn
    conf.registerPlugin('Mantis', True)
    if yn("""This plugin can show data about bug URLs and numbers mentioned
             in the channel. Do you want this bug snarfer enabled by 
             default?""", default=False):
        conf.supybot.plugins.Mantis.bugSnarfer.setValue(True)

Mantis = conf.registerPlugin('Mantis')
# This is where your configuration variables (if any) should go.  For example:
# conf.registerGlobalValue(Mantis, 'someConfigVariableName',
#     registry.Boolean(False, """Help for someConfigVariableName."""))

conf.registerChannelValue(Mantis,'bugPeriodicCheck',
    registry.Integer(0,
     """The plugin will check for new bug reports each <bugPeriodicCheck> seconds.
    If set to 0, this feature is disabled (default). The plugin
    must be reloaded for changes to take effect."""))

conf.registerGlobalValue(Mantis, 'bugPeriodicCheckTo',
    registry.String('', 
    """Determines who will be informed when new bugs are reported. 
    It is a whitespace separated list of nickname or channel"""))

conf.registerChannelValue(Mantis, 'bugSnarfer',
    registry.Boolean(False, """Determines whether the bug snarfer will be
    enabled, such that any bug ### seen in the channel
    will have its information reported into the channel."""))

conf.registerGlobalValue(Mantis, 'bugSnarferTimeout',
    registry.PositiveInteger(300, 
    """Users often say "bug XXX" several times in a row, in a channel.
    If "bug XXX" has been said in the last (this many) seconds, don't
    fetch its data again. If you change the value of this variable, you
    must reload this plugin for the change to take effect."""))

conf.registerChannelValue(Mantis, 'bugMsgFormat',
    registry.String('Bug _ID_ - _REPORTER_ - _RESOLUTION_ - _STATUS__CRLF__SUMMARY_ - _URL_',
    """Change the message format for bug details, following tokens will 
    be replaced before being printed: _ID_, _URL_, _REPORTER_, 
    _PROJECT_, _SUMMARY_, _STATUS_, _RESOLUTION_ .
    _CRLF_ will split the response in two (or more) lines."""))

conf.registerChannelValue(Mantis, 'urlbase',
    registry.String('http://www.mantisbt.org/bugs', 
    """The base URL for the Mantis instance this plugin will retrieve
    bug informations from."""))

conf.registerGlobalValue(Mantis, 'username',
    registry.String('', """Username for the Mantis account""",
                    private=True))

conf.registerGlobalValue(Mantis, 'password',
    registry.String('', """Password for the Mantis account""",
                    private=True))


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
