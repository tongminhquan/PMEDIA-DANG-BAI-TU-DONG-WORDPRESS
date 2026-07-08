from __future__ import annotations

import unittest

from wp_auto_poster_gui.core.credential_store import protect_secret, unprotect_secret


class CredentialStoreTest(unittest.TestCase):
    def test_protect_secret_round_trips_without_plain_text(self) -> None:
        secret = "abc 123 APPLICATION PASSWORD"

        protected = protect_secret(secret)

        self.assertNotEqual(protected, secret)
        self.assertNotIn(secret, protected)
        self.assertEqual(unprotect_secret(protected), secret)


if __name__ == "__main__":
    unittest.main()
