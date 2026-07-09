# StegoCrypt — LSB Image Steganography Tool

A command-line tool that hides secret text messages inside ordinary PNG/BMP images, and reveals them again — with optional password protection.

Steganography is the practice of hiding data *inside* other data so its existence isn't obvious. Unlike encryption (which scrambles a message so it's unreadable but visibly "a secret"), steganography hides the fact that a secret exists at all. Security teams study this because it's a real technique used for data exfiltration — sneaking sensitive data out of a network inside what looks like a harmless image attachment.

## How it works

Every pixel in an image is made of Red, Green, and Blue values, each an 8-bit number from 0–255. Changing only the *last bit* of one of these numbers shifts its value by at most 1 (e.g. 200 → 201) — a difference no human eye can detect. StegoCrypt rewrites the last bit of each color channel to spell out the hidden message in binary, and reads those bits back out to recover it.

```
Original pixel:  (200, 133, 47)
Binary:           11001000  10000101  00101111
Hide bit "1":     1100100[1] 10000101  00101111   <- only last bit changes
```

## Features

- Hide any text message inside a PNG or BMP cover image
- Optional password-based obfuscation (XOR keystream derived from SHA-256 of the password)
- Capacity checking — tells you the maximum message size a given image can hold before you try
- Clear error handling for oversized messages, wrong passwords, and non-stego images
- Fully tested with an automated test suite (`test_stegocrypt.py`)

## Installation

```bash
git clone https://github.com/MauriceThomas03/stegocrypt.git
cd stegocrypt
pip install -r requirements.txt
```

## Usage

Generate a sample image to experiment with (or use your own PNG):

```bash
python examples/generate_sample_image.py
```

**Hide a message:**
```bash
python stego_cli.py encode -i examples/cover.png -o examples/secret.png -m "meet at dawn" -p mypassword
```

**Reveal a message:**
```bash
python stego_cli.py decode -i examples/secret.png -p mypassword
```

**Check how much a cover image can hold:**
```bash
python stego_cli.py capacity -i examples/cover.png
```

Passwords and messages can also be entered interactively (prompted, input hidden) if you omit the `-m` / `-p` flags.

## Running the tests

```bash
python test_stegocrypt.py
```

## Security notes & limitations

This is an educational / portfolio project, not a production security tool. A few honest caveats that matter if you're evaluating it:

- **The password protection is XOR obfuscation, not real encryption.** It stops casual inspection but is not resistant to a determined attacker who suspects a keystream cipher. A production version would use AES-GCM via the `cryptography` library instead.
- **LSB steganography is detectable.** Statistical steganalysis tools (e.g. chi-square attacks) can flag images whose LSBs don't look like natural image noise, especially when a message fills most of the image's capacity. This tool demonstrates the *technique*, not a way to defeat forensic analysis.
- **Lossy formats will destroy the hidden data.** Saving the output as JPEG (or re-uploading to a service that re-compresses images, like most social media platforms) will corrupt or erase the hidden message, since JPEG discards exactly the "invisible" detail this tool relies on. Always save as PNG or BMP.

## Why I built this

I wanted a portfolio project that goes beyond the typical "port scanner" or "password checker" beginner projects and actually demonstrates a concept used in real digital forensics and data-exfiltration analysis — how attackers can hide data in plain sight, and what defenders look for.

## License

MIT
