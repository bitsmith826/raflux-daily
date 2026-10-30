import os
import sys
import time
import json
import csv
import random
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional

from core.wallet import SolanaWallet
from core.client import RafluxClient
from core.logger import Logger
from core.display import Display

CONFIG_PATH = "config/config.json"
WALLETS_PATH = "data/wallets.txt"
PROXIES_PATH = "data/proxies.txt"
REPORTS_DIR = "reports"

def load_config() -> Dict[str, Any]:
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError(f"Config file not found: {CONFIG_PATH}")
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def load_wallets() -> List[str]:
    if not os.path.exists(WALLETS_PATH):
        return []
    wallets = []
    with open(WALLETS_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                wallets.append(line)
    return wallets

def load_proxies() -> List[str]:
    if not os.path.exists(PROXIES_PATH):
        return []
    proxies = []
    with open(PROXIES_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                proxies.append(line)
    return proxies

def process_wallet(wallet_str: str, idx: int, total: int, config: Dict[str, Any], proxy: Optional[str] = None) -> Dict[str, Any]:
    record = {
        "index": idx,
        "address": "Unknown",
        "username": "-",
        "ref_status": "-",
        "checkin_status": "Gagal",
        "streak": 0,
        "points": 0,
        "status": "Error"
    }

    try:
        wallet = SolanaWallet(wallet_str)
        record["address"] = wallet.address
    except Exception as e:
        Logger.error(f"Private key tidak valid di baris ke-{idx}: {e}")
        record["status"] = f"Key Error: {e}"
        return record

    client = RafluxClient(
        wallet=wallet,
        base_url=config.get("api_base_url", "https://api.raflux.io/solana/v1"),
        proxy=proxy
    )

    # 1. Authenticate with retry
    authenticated = False
    is_new = False
    for attempt in range(1, 3):
        if client.authenticate():
            authenticated = True
            break
        if attempt < 2:
            time.sleep(2)

    if not authenticated:
        Logger.error(f"Akun #{idx:02d} ({wallet.address[:8]}...): Autentikasi SIWS gagal.")
        record["status"] = "Auth Failed"
        return record

    # 2. Claim Referral Code
    ref_desc = "Dilewati"
    if config.get("auto_claim_referral", True):
        primary_code = config.get("referral_code", "").strip()
        fallback_code = config.get("fallback_referral_code", "").strip()
        
        if primary_code and not primary_code.startswith("YOUR_"):
            ok, msg = client.claim_referral(primary_code)
            if ok:
                record["ref_status"] = primary_code
                ref_desc = f"Sukses (+20 FP) [{primary_code}]"
            else:
                if "already" in msg.lower():
                    record["ref_status"] = primary_code
                    ref_desc = f"Sudah Terklaim [{primary_code}]"
                elif fallback_code and fallback_code != primary_code and not fallback_code.startswith("YOUR_"):
                    ok_fb, msg_fb = client.claim_referral(fallback_code)
                    if ok_fb:
                        record["ref_status"] = fallback_code
                        ref_desc = f"Sukses (+20 FP) [{fallback_code}]"
                    else:
                        record["ref_status"] = "Skipped"
                        ref_desc = "Dilewati / Sudah Ada"
                else:
                    record["ref_status"] = "Skipped"
        else:
            record["ref_status"] = "Tidak Diatur"
            ref_desc = "Dilewati (Tanpa Ref)"

    # 3. Collect Welcome Points Bonus (+20 FP)
    if config.get("auto_collect_welcome_points", True):
        client.collect_welcome_points()

    # 4. Daily Check-in
    checkin_desc = "Gagal"
    if config.get("auto_daily_checkin", True):
        ok_c, msg_c, streak = client.daily_check_in()
        record["streak"] = streak
        if ok_c:
            record["checkin_status"] = "Sukses"
            checkin_desc = f"SUKSES (Streak {streak} Hari)"
        else:
            record["checkin_status"] = msg_c
            checkin_desc = f"Sudah Check-In ({streak} Hari)" if streak > 0 else "Gagal"

    # 5. Check & Claim Quests
    if config.get("auto_claim_quests", True):
        client.process_all_quests()

    # 6. Fetch Final Points & Profile
    pts_data = client.get_points()
    profile = client.get_profile()
    username = profile.get("data", {}).get("username", "Unknown") if profile else "Unknown"
    balance = pts_data.get("balance", 0) if pts_data else 0

    record["username"] = username
    record["points"] = balance
    record["status"] = "Sukses"

    # Print Clean Card
    Display.wallet_card(
        idx=idx,
        total=total,
        address=wallet.address,
        username=username,
        ref_msg=ref_desc,
        checkin_msg=checkin_desc,
        streak=record["streak"],
        points=balance,
        is_new=is_new
    )
    return record

def save_report(results: List[Dict[str, Any]]) -> str:
    os.makedirs(REPORTS_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = os.path.join(REPORTS_DIR, f"raflux_report_{timestamp}.csv")
    
    headers = ["index", "address", "username", "ref_status", "checkin_status", "streak", "points", "status"]
    with open(report_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(results)

    return report_file

def run_all(config: Dict[str, Any]):
    wallets = load_wallets()
    total = len(wallets)
    if total == 0:
        Logger.warn(f"Belum ada wallet yang terdaftar di '{WALLETS_PATH}'!")
        Logger.info("Silakan isi file 'data/wallets.txt' atau jalankan 'python import_mnemonic.py' untuk import 30+ akun.")
        return

    proxies = load_proxies() if config.get("enable_proxy", False) else []
    delay_range = config.get("delay_between_wallets_sec", [4, 8])
    ref_code = config.get("referral_code", "") or "Tidak Diatur"
    loop_mode = config.get("loop_mode", False) or ("--loop" in sys.argv)

    # Display Config Card
    Display.config_box(
        total_wallets=total,
        ref_code=ref_code,
        delay_range=delay_range,
        proxies_count=len(proxies),
        loop_mode=loop_mode
    )

    results = []
    
    # Check if multithreading is requested
    threads = 1
    for arg in sys.argv:
        if arg.startswith("--threads="):
            try:
                threads = int(arg.split("=")[1])
            except ValueError:
                pass

    if threads > 1 and proxies:
        Logger.info(f"Menjalankan dengan mode Multi-threading ({threads} threads paralel)...")
        with ThreadPoolExecutor(max_workers=threads) as executor:
            futures = {
                executor.submit(
                    process_wallet,
                    w,
                    i,
                    total,
                    config,
                    proxies[(i - 1) % len(proxies)] if proxies else None
                ): i for i, w in enumerate(wallets, 1)
            }
            for future in as_completed(futures):
                try:
                    res = future.result()
                    results.append(res)
                except Exception as e:
                    Logger.error(f"Thread error: {e}")
        results.sort(key=lambda x: x["index"])
    else:
        for i, w in enumerate(wallets, 1):
            proxy = proxies[(i - 1) % len(proxies)] if proxies else None
            res = process_wallet(w, i, total, config, proxy)
            results.append(res)
            
            if i < total:
                delay = random.uniform(delay_range[0], delay_range[1])
                time.sleep(delay)

    # Print Precision Table & Finish Card
    Display.summary_table(results)
    report_file = save_report(results)
    
    success_count = sum(1 for r in results if r["status"] == "Sukses")
    total_fp = sum(r["points"] for r in results)
    Display.finish_box(success_count, total, total_fp, report_file)

def main():
    if "--boost-ref" in sys.argv or "--ref" in sys.argv:
        from referral_booster import run_boost
        run_boost()
        return

    Display.banner()
    config = load_config()

    loop_mode = config.get("loop_mode", False) or ("--loop" in sys.argv)
    interval_hours = config.get("loop_interval_hours", 24)

    if loop_mode:
        Logger.info(f"Mode Loop aktif! Bot akan berjalan otomatis setiap {interval_hours} jam.")
        while True:
            try:
                run_all(config)
            except Exception as e:
                Logger.error(f"Error saat iterasi loop: {e}")
            
            sleep_sec = interval_hours * 3600
            Logger.info(f"Menunggu siklus harian berikutnya dalam {interval_hours} jam...")
            time.sleep(sleep_sec)
    else:
        run_all(config)

if __name__ == "__main__":
    main()
