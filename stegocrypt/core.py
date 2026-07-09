"""
stegocrypt.core
----------------
LSB (Least Significant Bit) image steganography with optional
password-based obfuscation of the hidden payload.

How it works
------------
Every pixel in an image is made of color channels (e.g. Red, Green, Blue),
each stored as an 8-bit number (0-255). Changing the *last* bit of an 8-bit
number changes its value by at most 1 (e.g. 200 -> 201), which is not
visible to the human eye. This tool hides data by rewriting the last bit
of each color channel to match the bits of a secret message, then reads
the last bits back out to recover it.

This is a classic data-hiding / anti-forensics technique. Security teams
study it to understand how attackers can exfiltrate data inside ordinary-
looking image files (e.g. attached to an email or posted on a public
forum) without triggering content filters that only inspect visible
image content.

This project is for education and portfolio purposes. The XOR cipher used
for password protection is NOT cryptographically strong -- see README.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Union

from PIL import Image

# A unique marker written before the message length so we can tell a
# "no hidden message" image apart from one that happens to have random
# noise in its LSBs.
MAGIC_HEADER = b"STGC"
LENGTH_BYTES = 4  # supports messages up to ~4GB (bounded by image capacity anyway)


class StegoError(Exception):
    """Raised for any steganography-specific failure (capacity, format, etc.)."""


def _derive_keystream(password: str, length: int) -> bytes:
    """
    Derive a repeating keystream from a password using SHA-256.
    This is simple XOR obfuscation, not real encryption -- it stops casual
    inspection of the extracted bytes but is trivially breakable by anyone
    who suspects a password-derived XOR stream. See README for why.
    """
    if not password:
        return b""
    digest = hashlib.sha256(password.encode("utf-8")).digest()
    return (digest * (length // len(digest) + 1))[:length]


def _xor_bytes(data: bytes, key: bytes) -> bytes:
    if not key:
        return data
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))


def _bytes_to_bits(data: bytes):
    for byte in data:
        for i in range(7, -1, -1):
            yield (byte >> i) & 1


def _bits_to_bytes(bits) -> bytes:
    out = bytearray()
    cur = 0
    count = 0
    for bit in bits:
        cur = (cur << 1) | bit
        count += 1
        if count == 8:
            out.append(cur)
            cur = 0
            count = 0
    return bytes(out)


def capacity_bytes(image_path: Union[str, Path]) -> int:
    """Return the maximum number of payload bytes that can be hidden in an image."""
    with Image.open(image_path) as img:
        img = img.convert("RGB")
        width, height = img.size
    total_bits = width * height * 3  # 1 bit per color channel
    header_bits = (len(MAGIC_HEADER) + LENGTH_BYTES) * 8
    usable_bits = max(0, total_bits - header_bits)
    return usable_bits // 8


def encode_message(
    image_path: Union[str, Path],
    message: str,
    output_path: Union[str, Path],
    password: str = "",
) -> None:
    """Hide `message` inside `image_path` and save the result to `output_path`."""
    with Image.open(image_path) as img:
        img = img.convert("RGB")
        width, height = img.size
        pixels = list(img.getdata())

    payload = message.encode("utf-8")
    payload = _xor_bytes(payload, _derive_keystream(password, len(payload)))

    header = MAGIC_HEADER + len(payload).to_bytes(LENGTH_BYTES, "big")
    full_data = header + payload

    max_bytes = capacity_bytes(image_path)
    if len(payload) > max_bytes:
        raise StegoError(
            f"Message too large for this image: {len(payload)} bytes needed, "
            f"{max_bytes} bytes available. Use a larger image or shorter message."
        )

    bits = list(_bytes_to_bits(full_data))
    bit_index = 0
    new_pixels = []

    for pixel in pixels:
        if bit_index >= len(bits):
            new_pixels.append(pixel)
            continue
        r, g, b = pixel
        channels = [r, g, b]
        for c in range(3):
            if bit_index < len(bits):
                channels[c] = (channels[c] & ~1) | bits[bit_index]
                bit_index += 1
        new_pixels.append(tuple(channels))

    out_img = Image.new("RGB", (width, height))
    out_img.putdata(new_pixels)
    out_img.save(output_path)


def decode_message(image_path: Union[str, Path], password: str = "") -> str:
    """Extract and return the hidden message from `image_path`."""
    with Image.open(image_path) as img:
        img = img.convert("RGB")
        pixels = list(img.getdata())

    all_bits = []
    for pixel in pixels:
        for channel in pixel:
            all_bits.append(channel & 1)

    header_bit_len = (len(MAGIC_HEADER) + LENGTH_BYTES) * 8
    if len(all_bits) < header_bit_len:
        raise StegoError("Image too small to contain a valid header.")

    header_bytes = _bits_to_bytes(all_bits[:header_bit_len])
    magic = header_bytes[: len(MAGIC_HEADER)]
    if magic != MAGIC_HEADER:
        raise StegoError(
            "No hidden message found (magic header missing). "
            "This image was probably not encoded with stegocrypt."
        )

    msg_len = int.from_bytes(header_bytes[len(MAGIC_HEADER):], "big")
    payload_bit_len = msg_len * 8
    start = header_bit_len
    end = start + payload_bit_len

    if end > len(all_bits):
        raise StegoError("Declared message length exceeds image capacity — file may be corrupted.")

    payload_bytes = _bits_to_bytes(all_bits[start:end])
    payload_bytes = _xor_bytes(payload_bytes, _derive_keystream(password, len(payload_bytes)))

    try:
        return payload_bytes.decode("utf-8")
    except UnicodeDecodeError as e:
        raise StegoError(
            "Decoded bytes are not valid text — wrong password, or image wasn't encoded with stegocrypt."
        ) from e
