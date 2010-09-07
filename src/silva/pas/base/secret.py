import hmac
import os
import hashlib

from five import grok

from silva.core import conf as silvaconf
from silva.core.services.base import SilvaService
from zope.session.interfaces import IClientId
from silva.pas.base.interfaces import ISecretService
from zeam.form import silva as silvaforms


class SecretService(SilvaService):
    grok.implements(ISecretService)

    meta_type = 'Silva AIVD Secret Service'
    default_service_identifier = 'service_secret'
    manage_options = (
        {'label': 'Secret generation service',
         'action': 'manage_main'},) + SilvaService.manage_options
    silvaconf.icon('www/key.png')


    def __init__(self, id):
        super(SecretService, self).__init__(id)
        self.generate_new_key()

    def generate_new_key(self):
        self.__key = str(os.urandom(8*8))

    def create_secret(self, request, *args):
        challenge = hmac.new(
            self.__key,
            str(IClientId(request)),
            hashlib.sha1)
        for arg in args:
            challenge.update(str(args))
        return challenge.hexdigest()


class SecretServiceView(silvaforms.ZMIForm):
    label = u"Generate new key"
    description = u"Generate a new key. Carreful!! secret key is used " \
                  u"in session and authentication and this will logout "\
                  u"all currently logged in users."

    name = 'manage_main'

    grok.name(name)
    grok.context(ISecretService)
    ignoreContent = False
    ignoreRequest = True

    @silvaforms.action(u'Generate new key')
    def generate_new_key(self):
        self.context.generate_new_key()
        self.status = u'Key updated.'

