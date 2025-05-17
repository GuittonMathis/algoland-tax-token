#!/usr/bin/env python3
"""
create_account.py

Generates a new Algorand account and prints its public address and
the corresponding 25-word mnemonic phrase.

Dependencies:
  pip install py-algorand-sdk

Usage:
  python create_account.py
"""

from algosdk import account, mnemonic

# Generate a new Algorand keypair: returns (private_key_bytes, address_str)
secret_key, address = account.generate_account()

# Print the results
print("Adresse TestNet :", address)
print("Mnemonic (gardez-le précieusement) :", mnemonic.from_private_key(secret_key))
