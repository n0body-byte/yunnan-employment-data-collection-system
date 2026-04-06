from __future__ import annotations

import unittest

from app.security import create_access_token, decode_access_token, hash_password, verify_password


class SecurityTests(unittest.TestCase):
    def test_password_hash_and_verify(self) -> None:
        password_hash = hash_password('Admin12345')
        self.assertTrue(verify_password('Admin12345', password_hash))
        self.assertFalse(verify_password('WrongPassword', password_hash))

    def test_access_token_encode_and_decode(self) -> None:
        token = create_access_token(subject='1', role='PROVINCE', region='Yunnan')
        payload = decode_access_token(token)
        self.assertEqual(payload['sub'], '1')
        self.assertEqual(payload['role'], 'PROVINCE')
        self.assertEqual(payload['region'], 'Yunnan')


if __name__ == '__main__':
    unittest.main()
