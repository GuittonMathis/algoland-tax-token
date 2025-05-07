from algosdk import account, mnemonic

# Génère bien : secret_key (bytes), address (string)
secret_key, address = account.generate_account()

print("Adresse TestNet :", address)
print("Mnemonic (gardez-le précieusement) :", mnemonic.from_private_key(secret_key))
