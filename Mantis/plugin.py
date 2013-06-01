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
import supybot.schedule as schedule
import supybot.ircmsgs as ircmsgs
from supybot.utils.structures import TimeoutQueue

import sys

# depends from SOAPpy
from SOAPpy import SOAPProxy

namespace = 'http://futureware.biz/mantisconnect'

class Mantis(callbacks.PluginRegexp):
    """Utilities related to mantis
    This plugin is able to display newly reported bug, 
    and an expansion "bug #" to URI is provided.
    It can also detect "bug #" in chat.
    A template allow to change response message.
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
        
        self.urlbase = self.registryValue('urlbase') 
        self.privateurlbase = self.registryValue('privateurlbase')

        if self.privateurlbase != "":
            serviceUrl = self.privateurlbase + '/api/soap/mantisconnect.php'
        else:
            serviceUrl = self.urlbase + '/api/soap/mantisconnect.php'

        self.server = SOAPProxy(serviceUrl)._ns(namespace)
        self.username = self.registryValue('username')
        self.password = self.registryValue('password')
        self.oldperiodic = self.registryValue('bugPeriodicCheck')
        self.irc = irc
        self.lastBug = 0

        bugPeriodicCheck = self.oldperiodic
        if bugPeriodicCheck > 0:
            schedule.addPeriodicEvent(self._bugPeriodicCheck, bugPeriodicCheck, name=self.name())

        reload(sys)
        sys.setdefaultencoding('utf-8')


    def die(self):
        self.__parent.die()
        if self.oldperiodic > 0:
            schedule.removeEvent(self.name())


def _bugPeriodicCheck(self):
        irc = self.irc
        newBug = self.server.mc_issue_get_biggest_id( username=self.username,
            password=self.password, project_id = 0 ) + 1
        #self.log.debug('Timer hit')
        if self.lastBug == 0:
            self.lastBug = newBug
        if newBug > self.lastBug:
            #self.log.debug('Bug is greater: '+ str(newBug) + ' ' + str(self.lastBug))
            strings = self.getBugs( range(self.lastBug, newBug) )
            for s in strings:
                sendtos = self.registryValue('bugPeriodicCheckTo')
                sendtos = sendtos.split()
                for sendto in sendtos:
                    #self.log.debug('sendtochannel: '+ sendto + s)
                    irc.queueMsg(ircmsgs.privmsg(sendto, s))
                    #self.log.debug('Sent: ' + s)
            self.lastBug = newBug
            #self.log.debug('End for: '+ str(newBug) + ' ' + str(self.lastBug))


    def bug(self, irc, msg, args, bugNumber):
        """<bug number>
        Expand bug # to a full URI
        """
        strings = self.getBugs( [ bugNumber ] )

        if strings == []:
            irc.reply( "sorry, bug %s was not found" % bugNumber )
        else:
            for s in strings:
                irc.reply(s, prefixNick=False)

    bug = wrap(bug, ['int'])


    def version( self, irc, msg, args ):
        """ Returns the Mantis SOAP API version running on server
        """
        irc.reply( "Mantis SOAP API version: " + self.server.mc_version() )
    version = wrap(version)

    
    def snarfBug(self, irc, msg, match):
#r"""\b((?P<install>\w+)\b\s*)?(?P<type>bug|attachment)\b[\s#]*(?P<id>\d+)"""
        r"""\bbug\b[\s#]*(?P<id>\d+)"""
        self.log.info('Snarf here')
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
        strings = []
        for id in ids:
                    try:
                        bugdata = self.server.mc_issue_get( username=self.username,
                            password=self.password, issue_id = id )
                    except Exception:
                        continue
                    bugmsg = self.registryValue('bugMsgFormat')
                    bugmsg = bugmsg.replace('_ID_', "%s" % id)
                    bugmsg = bugmsg.replace('_PROJECT_', bugdata['project'].name)
                    bugmsg = bugmsg.replace('_SUMMARY_', bugdata['summary'])
                    bugmsg = bugmsg.replace('_REPORTER_', bugdata['reporter'].name)
                    try:
                         bugmsg = bugmsg.replace('_ASSIGNED_', bugdata['handler'].name)
                    except Exception:
                         bugmsg = bugmsg.replace('_ASSIGNED_', 'nobody')
                    bugmsg = bugmsg.replace('_STATUS_', bugdata['status'].name)
                    bugmsg = bugmsg.replace('_RESOLUTION_', bugdata['resolution'].name)
                    bugmsg = bugmsg.replace('_URL_', "%s/view.php?id=%s" % (self.urlbase, id))
                    bugmsg = bugmsg.split('_CRLF_')
                    for msg in bugmsg:
                        strings.append(msg)
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
