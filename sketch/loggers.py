from google.appengine.api import xmpp
import logging
import logging.handlers

import os
DEFAULT_FROM_JID = 'logs@%s.appspotchat.com' % os.environ['APPLICATION_ID']

class XmppLogHandler(logging.Handler):

    def __init__(self, jid, from_jid):
        logging.Handler.__init__(self)
        self.jid = jid
        self.from_jid = from_jid
        self.is_logging = False

    def emit(self, record):
        # prevent recursive logging
        if self.is_logging:
            return
        self.is_logging = True
        # if user is online send a message
        if xmpp.get_presence(self.jid, from_jid=self.from_jid):
            status_code = xmpp.send_message(self.jid, self.format(record), from_jid=self.from_jid)
        self.is_logging = False


    @classmethod
    def add(self, jid, from_jid=DEFAULT_FROM_JID, level=logging.ERROR):
        if hasattr(logging.handlers,'XmppLogHandler'):
            return
        # ensure the user is subscribed
        xmpp.send_invite(jid, from_jid)
        # add handler to logging namespace
        logging.handlers.XmppLogHandler = self
        # create handler
        handler = logging.handlers.XmppLogHandler(jid, from_jid)
        handler.setLevel(level)
        # add the hadnler
        logger = logging.getLogger()
        logger.addHandler(handler)
