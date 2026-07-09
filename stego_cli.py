#!/usr/bin/env python3
"""
stego_cli.py -- command-line interface for stegocrypt

Examples
--------
Hide a message:
    python stego_cli.py encode -i cover.png -o secret.png -m "meet at dawn" -p mypassword

Reveal a message:
    python stego_cli.py decode -i secret.png -p mypassword

Check how much a cover image can hold:
    python stego_cli.py capacity -i cover.png
"""

import argparse
import getpass
import sys

from stegocrypt import encode_message, decode_message, capacity_bytes, StegoError


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="stego_cli.py",
        description="Hide or reveal secret text messages inside PNG/BMP images using LSB steganography.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    enc = sub.add_parser("encode", help="Hide a message inside an image")
    enc.add_argument("-i", "--input", required=True, help="Path to the cover image (input)")
    enc.add_argument("-o", "--output", required=True, help="Path to save the resulting image")
    enc.add_argument("-m", "--message", help="Message to hide. If omitted, you'll be prompted.")
    enc.add_argument("-p", "--password", help="Optional password to obfuscate the message.")

    dec = sub.add_parser("decode", help="Reveal a message hidden inside an image")
    dec.add_argument("-i", "--input", required=True, help="Path to the image containing a hidden message")
    dec.add_argument("-p", "--password", help="Password used when encoding, if any.")

    cap = sub.add_parser("capacity", help="Show how many bytes an image can hide")
    cap.add_argument("-i", "--input", required=True, help="Path to the image to check")

    args = parser.parse_args()

    try:
        if args.command == "encode":
            message = args.message
            if message is None:
                message = input("Message to hide: ")
            password = args.password
            if password is None:
                password = getpass.getpass("Password (leave blank for none): ")
            encode_message(args.input, message, args.output, password=password)
            print(f"[+] Message hidden successfully -> {args.output}")

        elif args.command == "decode":
            password = args.password
            if password is None:
                password = getpass.getpass("Password (leave blank if none was used): ")
            message = decode_message(args.input, password=password)
            print("[+] Hidden message:")
            print(message)

        elif args.command == "capacity":
            n = capacity_bytes(args.input)
            print(f"[i] This image can hide up to {n} bytes (~{n} characters) of text.")

    except StegoError as e:
        print(f"[!] Error: {e}", file=sys.stderr)
        return 1
    except FileNotFoundError as e:
        print(f"[!] File not found: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
