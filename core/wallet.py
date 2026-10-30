import json
import base58
import nacl.signing
from typing import Tuple

class SolanaWallet:
    def __init__(self, key_str: str):
        self.raw_key = key_str.strip()
        self.signing_key, self.address = self._parse_key(self.raw_key)

    def _parse_key(self, key_str: str) -> Tuple[nacl.signing.SigningKey, str]:
        if key_str.startswith('[') and key_str.endswith(']'):
            raw = bytes(json.loads(key_str))
        else:
            raw = base58.b58decode(key_str)
        
        if len(raw) == 64:
            seed = raw[:32]
            signing_key = nacl.signing.SigningKey(seed)
        elif len(raw) == 32:
            signing_key = nacl.signing.SigningKey(raw)
        else:
            raise ValueError(f"Invalid private key byte length: {len(raw)} (expected 32 or 64)")
        
        pub_bytes = signing_key.verify_key.encode()
        address = base58.b58encode(pub_bytes).decode('utf-8')
        return signing_key, address

    def sign_message(self, message: str) -> str:
        """Signs a message with Ed25519 and returns base58 signature."""
        msg_bytes = message.encode('utf-8')
        signed = self.signing_key.sign(msg_bytes)
        signature = signed.signature
        return base58.b58encode(signature).decode('utf-8')

    @classmethod
    def generate_new(cls) -> Tuple["SolanaWallet", str]:
        """Generates a fresh new Solana keypair and returns (wallet, b58_private_key)."""
        gen = nacl.signing.SigningKey.generate()
        full_key = gen.encode() + gen.verify_key.encode()
        b58_priv = base58.b58encode(full_key).decode('utf-8')
        wallet = cls(b58_priv)
        return wallet, b58_priv
