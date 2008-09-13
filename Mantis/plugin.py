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

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
from supybot.utils.structures import TimeoutQueue

import sys

# depends from SOAPpy
from SOAPpy import SOAPProxy

namespace = 'http://futureware.biz/mantisconnect'

class Mantis(callbacks.PluginRegexp):
    """Utilities related to mantis
    For now, just a expansion "bug #" to URI is provided.
    """

    threaded = True
    unaddressedRegexps = ['snarfBug']

    def __init__(self, irc):
        self.__parent = super(Mantis, self)
        self.__parent.__init__(irc)

        self.saidBugs = ircutils.IrcDict()
        sayTimeout = self.registryValue('bugSnarferTimeout')
        for k in irc.state.channels.keys():
            self.saidBugs[k] = TimeoutQueue(sayTimeout)
        
        self.url = self.registryValue('urlbase') + '/api/soap/mantisconnect.php'
        self.server = SOAPProxy(urlbase)._ns(namespace)
        self.username = self.registryValue('username')
        self.password = self.registryValue('password')

        reload(sys)
        sys.setdefaultencoding('utf-8')


    def bug(self, irc, msg, args, bugNumber):
        """<bug number>
        Expand bug # to a full URI
        """
        if server.mc_issue_exists( username=mantisuser, password=mantispassword, issue_id = bugNumber ):
        #TODO: we could use directly this call to see if bug exists; learn how
        #      to use exceptions
            bugdata = server.mc_issue_get( username=mantisuser, password=mantispassword, issue_id = bugNumber )
            summary = bugdata['summary']
            status = bugdata['status'].name
            reporter = bugdata['reporter'].name
            resolution = bugdata['resolution'].name
            irc.reply("Bug %s - %s - %s - %s" % (bugNumber, reporter, status, resolution) )
            irc.reply("%s - %s/view.php?id=%s" % (summary, self.urlbase, bugNumber) )
        else:
            irc.reply( "sorry, bug %s was not found" % bugNumber )

    bug = wrap(bug, ['int'])


    def version( self, irc, msg, args ):
        """ Returns the Mantis SOAP API version running on server
        """
        irc.reply( "Mantis SOAP API version: " + server.mc_version() )
    version = wrap(version)

    
    def snarfBug(self, irc, msg, match):
#r"""\b((?P<install>\w+)\b\s*)?(?P<type>bug|attachment)\b[\s#]*(?P<id>\d+)"""
        r"""\bbug\b[\s#]*(?P<id>\d+)"""
        channel = msg.args[0]
        if not self.registryValue('bugSnarfer', channel): return

        id_matches = match.group('id').split()
        ids = []
        self.log.debug('Snarfed ID(s): ' + ' '.join(id_matches))

        # Check if the bug has been already snarfed in the last X seconds
        for id in id_matches:
            should_say = self._shouldSayBug(id, channel)
            if should_say:
                ids.append(id)
        if not ids: return

        strings = self.getBugs(ids)

        for s in strings:
            irc.reply(s, prefixNick=False)

    def _shouldSayBug(self, bug_id, channel):
        if channel not in self.saidBugs:
            sayTimeout = self.registryValue('bugSnarferTimeout')
            self.saidBugs[channel] = TimeoutQueue(sayTimeout)
        if bug_id in self.saidBugs[channel]:
            return False

        self.saidBugs[channel].enqueue(bug_id)
        self.log.info('After checking bug %s queue is %r' \
                        % (bug_id, self.saidBugs[channel]))
        return True

    def getBugs(self, ids):
        for id in ids:
            bugdata = server.mc_issue_get( username=mantisuser, password=mantispassword, issue_id = id )
            summary = bugdata['summary']
            status = bugdata['status'].name
            reporter = bugdata['reporter'].name
            resolution = bugdata['resolution'].name
            strings = [ "Bug %s - %s - %s - %s" % (id, reporter, status, resolution) ]
            strings.append( "%s - %s/view.php?id=%s" % (summary, self.urlbase, id) )
        return strings


Class = Mantis

def unwrap(object ):
    "Unwrap SOAPpy objects to get 'raw' python objects"
    if isinstance( object, SOAPpy.SOAP.structType ):
        return object._asdict
    elif isinstance( object, SOAPpy.SOAP.arrayType ):
        return object.data
    else:
        return object

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
