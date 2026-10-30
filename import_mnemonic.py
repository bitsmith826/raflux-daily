import os
import sys
import base58
from typing import List
from bip_utils import Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes
from core.logger import Logger

def derive_solana_accounts(mnemonic: str, count: int = 30, append_to_wallets: bool = True):
    Logger.banner()
    mnemonic = mnemonic.strip()
    words = mnemonic.split()
    if len(words) not in (12, 15, 18, 21, 24):
        Logger.error(f"Jumlah kata mnemonic tidak valid ({len(words)} kata). Biasanya 12 atau 24 kata.")
        return

    Logger.info(f"Menderivasi {count} akun Solana dari seed phrase...")
    try:
        seed_bytes = Bip39SeedGenerator(mnemonic).Generate()
        bip44_mst = Bip44.FromSeed(seed_bytes, Bip44Coins.SOLANA)
    except Exception as e:
        Logger.error(f"Gagal memproses mnemonic: {e}")
        return

    os.makedirs("data", exist_ok=True)
    derived = []

    for i in range(count):
        # Phantom standard derivation: m/44'/501'/{i}'/0'
        bip44_acc = bip44_mst.Purpose().Coin().Account(i).Change(Bip44Changes.CHAIN_EXT)
        priv_bytes = bip44_acc.PrivateKey().Raw().ToBytes()
        pub_addr = bip44_acc.PublicKey().ToAddress()
        
        # Combine 32-byte secret seed + 32-byte public key to get full 64-byte keypair
        pub_bytes = bip44_acc.PublicKey().RawCompressed().ToBytes()[1:] # or derive keypair
        # In bip-utils solana raw priv is 32 bytes seed
        # Base58 encode 32 bytes or 64 bytes is accepted by our loader
        priv_b58 = base58.b58encode(priv_bytes).decode('utf-8')
        
        derived.append((pub_addr, priv_b58))
        Logger.success(f"[Akun #{i+1:02d}] {pub_addr}")

    # Save to backup
    backup_file = "data/imported_mnemonic_backup.txt"
    with open(backup_file, "w", encoding="utf-8") as f:
        f.write("# Backup Derivasi Mnemonic Solana\n")
        for idx, (addr, priv) in enumerate(derived, 1):
            f.write(f"Akun #{idx:02d} | Address: {addr} | PrivateKey: {priv}\n")
    Logger.info(f"Daftar alamat & private key lengkap disimpan di '{backup_file}'.")

    if append_to_wallets:
        wallets_file = "data/wallets.txt"
        with open(wallets_file, "a", encoding="utf-8") as f:
            for _, priv in derived:
                f.write(f"{priv}\n")
        Logger.success(f"Berhasil menambahkan {count} akun ke '{wallets_file}'!")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        phrase = " ".join(sys.argv[1:-1]) if len(sys.argv) > 2 and sys.argv[-1].isdigit() else " ".join(sys.argv[1:])
        count = int(sys.argv[-1]) if sys.argv[-1].isdigit() else 30
    else:
        Logger.banner()
        print("Masukkan 12 atau 24 kata seed phrase (dipisahkan spasi):")
        phrase = input("> ").strip()
        print("Berapa banyak akun yang ingin diderivasi? (Default: 30):")
        cnt_in = input("> ").strip()
        count = int(cnt_in) if cnt_in.isdigit() else 30

    if phrase:
        derive_solana_accounts(phrase, count)
    else:
        Logger.warn("Seed phrase kosong. Operasi dibatalkan.")
