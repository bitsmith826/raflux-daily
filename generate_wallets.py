import os
import sys
from core.wallet import SolanaWallet
from core.logger import Logger

def generate_wallets(count: int = 5, append_to_wallets: bool = True):
    Logger.banner()
    Logger.info(f"Menghasilkan {count} Solana Wallet baru...")

    os.makedirs("data", exist_ok=True)
    generated = []

    for i in range(1, count + 1):
        wallet, priv_b58 = SolanaWallet.generate_new()
        generated.append((wallet.address, priv_b58))
        Logger.success(f"[{i}/{count}] Public Key: {wallet.address}")

    # Save details to generated_wallets.txt
    backup_path = "data/generated_wallets_backup.txt"
    with open(backup_path, "a", encoding="utf-8") as f:
        for addr, priv in generated:
            f.write(f"Address: {addr}\nPrivate: {priv}\n{'-'*50}\n")
    Logger.info(f"Cadangan lengkap (Address & Private Key) disimpan di '{backup_path}'.")

    # Optionally append private keys to data/wallets.txt
    if append_to_wallets:
        wallets_path = "data/wallets.txt"
        with open(wallets_path, "a", encoding="utf-8") as f:
            for _, priv in generated:
                f.write(f"{priv}\n")
        Logger.success(f"{count} private key berhasil ditambahkan ke '{wallets_path}'!")

if __name__ == "__main__":
    count = 5
    if len(sys.argv) > 1:
        try:
            count = int(sys.argv[1])
        except ValueError:
            pass
    generate_wallets(count)
