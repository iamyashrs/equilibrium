import logging
import webapp2
from google.appengine.ext.webapp.mail_handlers import InboundMailHandler

class LogSenderHandler(InboundMailHandler):
    def receive(self, mail_message):
        logging.info("Received a message from: " + mail_message.sender)