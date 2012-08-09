
import unittest

from Products.Silva.ftesting import public_settings
from silva.pas.base.testing import FunctionalLayer


class LoginTestCase(unittest.TestCase):
    layer = FunctionalLayer

    def setUp(self):
        self.root = self.layer.get_application()

    def test_login_form(self):
        with self.layer.get_browser(public_settings) as browser:
            browser.options.cookie_support = True
            browser.options.follow_redirect = True
            self.assertEqual(
                browser.open('/root/edit'),
                401)
            self.assertIn('Content-Length', browser.headers)
            self.assertEqual(
                browser.headers['Content-Type'],
                'text/html;charset=utf-8')
            self.assertEqual(
                browser.headers['Cache-Control'],
                'no-cache, must-revalidate, post-check=0, pre-check=0')
            self.assertEqual(
                browser.headers['Pragma'],
                'no-cache')
            self.assertEqual(
                browser.inspect.title,
                ['Protected area'])
            form = browser.get_form('login_form')
            form.controls['__ac.field.name'].value = 'manager'
            form.controls['__ac.field.password'].value = 'invalid'
            self.assertEqual(
                form.controls['login'].submit(),
                401)
            form = browser.get_form('login_form')
            form.controls['__ac.field.name'].value = 'editor'
            form.controls['__ac.field.password'].value = 'editor'
            self.assertEqual(
                form.controls['login'].submit(),
                200)
            self.assertEqual(
                browser.location,
                '/root/edit')


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(LoginTestCase))
    return suite

