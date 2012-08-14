
import unittest

from Products.Silva.ftesting import public_settings
from silva.pas.base.testing import FunctionalLayer


class LoginTestCase(unittest.TestCase):
    layer = FunctionalLayer

    def setUp(self):
        self.root = self.layer.get_application()

    def test_login_form_default(self):
        """Test login with the login form by default.
        """
        with self.layer.get_browser(public_settings) as browser:
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
                form.controls['__ac.field.origin'].value,
                'http://localhost/root/edit')
            self.assertEqual(
                form.controls['login'].submit(),
                401)
            form = browser.get_form('login_form')
            form.controls['__ac.field.name'].value = 'editor'
            form.controls['__ac.field.password'].value = 'editor'
            self.assertEqual(
                form.controls['__ac.field.origin'].value,
                'http://localhost/root/edit')
            self.assertEqual(
                form.controls['login'].submit(),
                200)
            self.assertEqual(
                browser.location,
                '/root/edit')

    def test_login_form_redirect_to_path(self):
        """Test login with the login form and the option redirect to
        path.
        """
        self.root.acl_users.cookie_auth.redirect_to_path = True
        with self.layer.get_browser(public_settings) as browser:
            self.assertEqual(
                browser.options.server,
                'localhost')
            self.assertEqual(
                browser.options.port,
                '80')
            self.assertEqual(
                browser.open('/root/edit'),
                401)
            self.assertEqual(
                browser.options.server,
                'localhost')
            self.assertEqual(
                browser.options.port,
                '80')
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
                form.controls['__ac.field.origin'].value,
                '/root/edit')
            self.assertEqual(
                form.controls['login'].submit(),
                401)
            form = browser.get_form('login_form')
            form.controls['__ac.field.name'].value = 'editor'
            form.controls['__ac.field.password'].value = 'editor'
            self.assertEqual(
                form.controls['__ac.field.origin'].value,
                '/root/edit')
            self.assertEqual(
                form.controls['login'].submit(),
                200)
            self.assertEqual(
                browser.location,
                '/root/edit')
            self.assertEqual(
                browser.options.server,
                'localhost')
            self.assertEqual(
                browser.options.port,
                '80')

    def test_login_form_redirect_to_url(self):
        """Test login with the login form and the option redirect to
        path.
        """
        self.root.acl_users.cookie_auth.redirect_to_url = 'https://backend'
        with self.layer.get_browser(public_settings) as browser:
            self.assertEqual(
                browser.options.server,
                'localhost')
            self.assertEqual(
                browser.options.port,
                '80')
            self.assertEqual(
                browser.open('http://localhost/root/edit'),
                401)
            # And I got redirected to the backend:
            self.assertEqual(
                browser.options.server,
                'backend')
            self.assertEqual(
                browser.options.port,
                '443')
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
                form.controls['__ac.field.origin'].value,
                'https://backend/root/edit')
            self.assertEqual(
                form.controls['login'].submit(),
                401)
            form = browser.get_form('login_form')
            form.controls['__ac.field.name'].value = 'editor'
            form.controls['__ac.field.password'].value = 'editor'
            self.assertEqual(
                form.controls['__ac.field.origin'].value,
                'https://backend/root/edit')
            self.assertEqual(
                form.controls['login'].submit(),
                200)
            self.assertEqual(
                browser.location,
                '/root/edit')
            self.assertEqual(
                browser.options.server,
                'backend')
            self.assertEqual(
                browser.options.port,
                '443')


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(LoginTestCase))
    return suite

