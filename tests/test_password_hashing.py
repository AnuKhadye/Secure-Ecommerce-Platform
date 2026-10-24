import os
import tempfile
import unittest

from db.database import Database


class PasswordHashingTests(unittest.TestCase):
    def setUp(self):
        # Database leaves its connections open, so on Windows the file can't be
        # deleted straight away; ignore_cleanup_errors avoids a spurious error.
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.db = Database(db_path=os.path.join(self.tmp.name, 'test.db'))
        self.email = 'alice@example.com'
        self.password = 'correct horse battery staple'
        self.assertTrue(self.db.add_user('alice', self.password, self.email))

    def tearDown(self):
        self.tmp.cleanup()

    def test_new_user_hash_uses_pbkdf2_sha256(self):
        user = self.db.get_user_by_email(self.email)
        self.assertTrue(
            user['password'].startswith('pbkdf2:sha256:'),
            'stored hash does not use PBKDF2-SHA256',
        )

    def test_login_works_with_new_hash(self):
        self.assertIsNotNone(self.db.validate_user(self.email, self.password))
        self.assertIsNone(self.db.validate_user(self.email, 'wrong password'))


if __name__ == '__main__':
    unittest.main()
