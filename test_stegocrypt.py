"""
Simple test suite for stegocrypt. Run with:  python test_stegocrypt.py
Uses only the standard library's unittest module (no pytest dependency needed).
"""

import os
import tempfile
import unittest

from PIL import Image

from stegocrypt import encode_message, decode_message, capacity_bytes, StegoError


class TestStegoCrypt(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.cover_path = os.path.join(self.tmpdir, "cover.png")
        self.encoded_path = os.path.join(self.tmpdir, "encoded.png")

        img = Image.new("RGB", (100, 100))
        pixels = img.load()
        for x in range(100):
            for y in range(100):
                pixels[x, y] = ((x * 3) % 256, (y * 5) % 256, (x + y) % 256)
        img.save(self.cover_path)

    def test_round_trip_no_password(self):
        secret = "The eagle lands at midnight."
        encode_message(self.cover_path, secret, self.encoded_path)
        recovered = decode_message(self.encoded_path)
        self.assertEqual(secret, recovered)

    def test_round_trip_with_password(self):
        secret = "Only readable with the right password."
        encode_message(self.cover_path, secret, self.encoded_path, password="hunter2")
        recovered = decode_message(self.encoded_path, password="hunter2")
        self.assertEqual(secret, recovered)

    def test_wrong_password_fails(self):
        secret = "Top secret payload"
        encode_message(self.cover_path, secret, self.encoded_path, password="correct-horse")
        with self.assertRaises(StegoError):
            decode_message(self.encoded_path, password="wrong-password")

    def test_decode_unmodified_image_raises(self):
        with self.assertRaises(StegoError):
            decode_message(self.cover_path)

    def test_capacity_reported_and_enforced(self):
        cap = capacity_bytes(self.cover_path)
        self.assertGreater(cap, 0)
        too_long = "A" * (cap + 100)
        with self.assertRaises(StegoError):
            encode_message(self.cover_path, too_long, self.encoded_path)

    def test_encoded_image_dimensions_unchanged(self):
        encode_message(self.cover_path, "size check", self.encoded_path)
        with Image.open(self.cover_path) as orig, Image.open(self.encoded_path) as enc:
            self.assertEqual(orig.size, enc.size)


if __name__ == "__main__":
    unittest.main(verbosity=2)
