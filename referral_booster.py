import os
import sys
import time
import random
import csv
from datetime import datetime
from typing import List, Dict, Any

from core.wallet import SolanaWallet
from core.client import RafluxClient
from core.display import Display
from colorama import Fore, Style

REFERRAL_TARGETS_PATH = "data/referral_targets.txt"
REFERRALS_LOG_PATH = "data/referrals_generated.txt"
REPORTS_DIR = "reports"

def load_referral_targets() -> List[Dict[str, Any]]:
    targets = []
    if os.path.exists(REFERRAL_TARGETS_PATH):
        with open(REFERRAL_TARGETS_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                count = 20
                if ":" in line:
                    parts = line.rsplit(":", 1)
                    raw_ref = parts[0].strip()
                    try:
                        count = int(parts[1].strip())
                    except ValueError:
                        count = 20
                else:
                    raw_ref = line

                if "ref=" in raw_ref:
                    code = raw_ref.split("ref=")[1].split("&")[0].strip()
                else:
                    code = raw_ref.strip()

                if code:
                    targets.append({
                        "code": code,
                        "url": f"https://raflux.io/?ref={code}",
                        "target": count
                    })
    return targets

def append_to_ref_log(idx: int, code: str, addr: str, priv_key: str, username: str, pts: int):
    os.makedirs("data", exist_ok=True)
    with open(REFERRALS_LOG_PATH, "a", encoding="utf-8") as f:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"{idx} | {code} | {addr} | {priv_key} | {username} | {pts} FP | {ts}\n")

def save_csv_report(records: List[Dict[str, Any]]) -> str:
    os.makedirs(REPORTS_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(REPORTS_DIR, f"referrals_boost_{ts}.csv")
    headers = ["index", "ref_code", "address", "private_key", "username", "points", "status", "timestamp"]
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(records)
    return filepath

def print_booster_banner(total_codes: int, total_targets: int):
    w = 86
    top_eq = Fore.CYAN + "+" + "=" * (w - 2) + "+" + Style.RESET_ALL
    print("\n" + top_eq)

    art = [
        "  _____  ______ ______ ______ _____             _       _____   ____   ____  _____  ",
        " |  __ \\|  ____|  ____|  ____|  __ \\     /\\    | |     |  __ \\ / __ \\ / __ \\/ ____| ",
        " | |__) | |__  | |__  | |__  | |__) |   /  \\   | |     | |__) | |  | | |  | | (___   ",
        " |  _  /|  __| |  __| |  __| |  _  /   / /\\ \\  | |     |  _  /| |  | | |  | |\\___ \\  ",
        " | | \\ \\| |____| |    | |____| | \\ \\  / ____ \\ | |____ | |_) || |__| | |__| |____) | ",
        " |_|  \\_\\______|_|    |______|_|  \\_\\/_/    \\_\\|______||_  __/  \\____/ \\____/|_____/  ",
    ]
    inner = w - 2
    for line in art:
        pad_left = max(0, (inner - len(line)) // 2)
        print(Display.pad_box(f"{Fore.LIGHTCYAN_EX}{Style.BRIGHT}{' ' * pad_left}{line}", w))

    print(Display.pad_box(" ", w))
    tag = ">> RAFLUX AUTOMATED REFERRAL MULTIPLIER ENGINE <<"
    p_tag = (inner - len(tag)) // 2
    print(Display.pad_box(f"{' ' * p_tag}{Fore.YELLOW}{Style.BRIGHT}{tag}{Style.RESET_ALL}", w))

    sub = f"Target: {total_codes} Referral Links  *  Total: {total_targets} Akun Baru"
    p_sub = (inner - len(sub)) // 2
    print(Display.pad_box(f"{' ' * p_sub}{Fore.WHITE}{sub}{Style.RESET_ALL}", w))
    print(top_eq)

def print_target_box(targets: List[Dict[str, Any]]):
    w = 86
    title = " [ DAFTAR TARGET REFERRAL ] "
    dash_r = w - 2 - len(title) - 2
    top_dash = Fore.CYAN + "+" + "-" * (w - 2) + "+" + Style.RESET_ALL

    print(f"\n{Fore.CYAN}+--{Fore.WHITE}{Style.BRIGHT}{title}{Style.RESET_ALL}{Fore.CYAN}{'-' * dash_r}+{Style.RESET_ALL}")
    for i, t in enumerate(targets, 1):
        line = f"  {Fore.YELLOW}[{i:02d}]{Style.RESET_ALL} {Fore.WHITE}Link: {Fore.CYAN}{t['url']:<36}{Fore.WHITE} Target: {Fore.GREEN}{Style.BRIGHT}+{t['target']} Reff{Style.RESET_ALL}"
        print(Display.pad_box(line, w))
    print(top_dash + "\n")

def run_boost(targets: List[Dict[str, Any]] = None):
    if targets is None:
        targets = load_referral_targets()

    if not targets:
        print(f"\n{Fore.YELLOW}Info: File '{REFERRAL_TARGETS_PATH}' belum diisi atau tidak ditemukan.{Style.RESET_ALL}")
        print("Silakan masukkan kode referral atau link referral yang ingin diperbanyak:")
        in_code = input("> ").strip()
        if not in_code:
            print(f"{Fore.RED}Tidak ada kode referral yang dimasukkan. Batal.{Style.RESET_ALL}")
            return
        if "ref=" in in_code:
            c = in_code.split("ref=")[1].split("&")[0].strip()
        else:
            c = in_code.strip()
        print("Berapa banyak referral yang ingin dibuat? (Default: 20):")
        in_cnt = input("> ").strip()
        cnt = int(in_cnt) if in_cnt.isdigit() else 20
        targets = [{
            "code": c,
            "url": f"https://raflux.io/?ref={c}",
            "target": cnt
        }]

    total_targets = sum(t["target"] for t in targets)
    print_booster_banner(len(targets), total_targets)
    print_target_box(targets)

    global_records = []
    code_summary = []
    global_idx = 0

    for target_item in targets:
        ref_code = target_item["code"]
        target_count = target_item["target"]

        sep_title = f" [ MEMPROSES REFERRAL CODE: {ref_code} (TARGET: {target_count} AKUN) ] "
        dash_len = max(5, 86 - 2 - len(sep_title) - 2)
        print(f"{Fore.YELLOW}+=={Fore.WHITE}{Style.BRIGHT}{sep_title}{Style.RESET_ALL}{Fore.YELLOW}{'=' * dash_len}+{Style.RESET_ALL}")

        success_for_code = 0
        points_for_code = 0

        for local_idx in range(1, target_count + 1):
            global_idx += 1
            wallet, priv_key = SolanaWallet.generate_new()
            short_addr = f"{wallet.address[:5]}...{wallet.address[-5:]}"

            client = RafluxClient(wallet=wallet)

            # 1. SIWS Login
            auth_ok = client.authenticate(token_cache_file="data/tokens.json")
            if not auth_ok:
                print(f"{Fore.LIGHTBLACK_EX}[{global_idx:02d}/{total_targets:02d}]{Style.RESET_ALL} {Fore.RED}Auth SIWS Gagal untuk {short_addr}{Style.RESET_ALL}")
                continue

            # 2. Claim Referral
            ref_ok, ref_msg = client.claim_referral(ref_code)

            # 3. Welcome Points (+20 FP)
            welcome_ok, _ = client.collect_welcome_points()

            # 4. Daily Check-in (+1 FP)
            cin_ok, cin_msg, streak = client.daily_check_in()

            # 5. Fetch Points & Username
            pts_data = client.get_points()
            points = pts_data.get("balance", 21) if pts_data else 21
            profile = client.get_profile()
            username = profile.get("data", {}).get("username", "Unknown") if profile else "Unknown"

            success_for_code += 1
            points_for_code += points

            # Save referral log (isolated from main user wallets)
            append_to_ref_log(global_idx, ref_code, wallet.address, priv_key, username, points)

            rec = {
                "index": global_idx,
                "ref_code": ref_code,
                "address": wallet.address,
                "private_key": priv_key,
                "username": username,
                "points": points,
                "status": "Sukses" if ref_ok else "Gagal",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            global_records.append(rec)

            tag_ref = f"{Fore.GREEN}[REF OK]{Style.RESET_ALL}" if ref_ok else f"{Fore.RED}[REF FAIL]{Style.RESET_ALL}"
            tag_wel = f"{Fore.GREEN}+20 FP{Style.RESET_ALL}" if welcome_ok else f"{Fore.YELLOW}+0 FP{Style.RESET_ALL}"
            tag_cin = f"{Fore.GREEN}+1 FP (Streak 1){Style.RESET_ALL}" if cin_ok else f"{Fore.YELLOW}Check-in OK{Style.RESET_ALL}"

            line = (
                f"{Fore.CYAN}[{global_idx:02d}/{total_targets:02d}]{Style.RESET_ALL} "
                f"{Fore.WHITE}{short_addr}{Style.RESET_ALL} | "
                f"{Fore.YELLOW}{username[:14]:<14}{Style.RESET_ALL} | "
                f"{tag_ref} | {tag_wel} | {tag_cin} | "
                f"{Fore.YELLOW}{Style.BRIGHT}{points} FP{Style.RESET_ALL} "
                f"{Fore.GREEN}[OK]{Style.RESET_ALL}"
            )
            print(line)

            delay = round(random.uniform(2.0, 3.5), 1)
            time.sleep(delay)

        print(f"{Fore.YELLOW}+{'=' * 84}+{Style.RESET_ALL}\n")
        code_summary.append({
            "code": ref_code,
            "url": target_item["url"],
            "success": success_for_code,
            "target": target_count,
            "points": points_for_code
        })

    # Print Master Summary Table
    print_referral_summary_table(code_summary)

    # Save CSV Report
    report_file = save_csv_report(global_records)
    total_success = sum(c["success"] for c in code_summary)
    total_fp = sum(c["points"] for c in code_summary)
    Display.finish_box(total_success, total_targets, total_fp, report_file)

def print_referral_summary_table(summary: List[Dict[str, Any]]):
    cols = [
        {"name": "No",       "key": "no",     "width": 3,  "align": "^"},
        {"name": "Kode Reff", "key": "code",   "width": 10, "align": "^"},
        {"name": "Referral Link Target", "key": "url", "width": 29, "align": "<"},
        {"name": "Berhasil", "key": "succ",   "width": 9,  "align": "^"},
        {"name": "Target",   "key": "targ",   "width": 8,  "align": "^"},
        {"name": "Total FP", "key": "fp",     "width": 9,  "align": ">"},
    ]

    def get_sep(char="-"):
        parts = ["+" + char * (c["width"] + 2) for c in cols]
        return Fore.CYAN + "".join(parts) + "+" + Style.RESET_ALL

    print("\n" + get_sep("-"))
    hdr_cells = [Display.pad_cell(f"{Fore.WHITE}{Style.BRIGHT}{c['name']}{Style.RESET_ALL}", c["width"], "^") for c in cols]
    print(Fore.CYAN + "| " + (" " + Fore.CYAN + "| " + Style.RESET_ALL).join(hdr_cells) + " " + Fore.CYAN + "|")
    print(get_sep("="))

    total_succ = 0
    total_targ = 0
    total_pts = 0

    for i, s in enumerate(summary, 1):
        total_succ += s["success"]
        total_targ += s["target"]
        total_pts += s["points"]

        row = {
            "no": f"{i:02d}",
            "code": f"{Fore.YELLOW}{Style.BRIGHT}{s['code']}{Style.RESET_ALL}",
            "url": f"{Fore.LIGHTBLUE_EX}raflux.io/?ref={s['code']}{Style.RESET_ALL}",
            "succ": f"{Fore.GREEN}{s['success']} Reff{Style.RESET_ALL}",
            "targ": f"{Fore.WHITE}{s['target']} Reff{Style.RESET_ALL}",
            "fp": f"{Fore.GREEN}{Style.BRIGHT}{s['points']} FP{Style.RESET_ALL}"
        }
        cells = [Display.pad_cell(str(row[c["key"]]), c["width"], c["align"]) for c in cols]
        print(Fore.CYAN + "| " + (" " + Fore.CYAN + "| " + Style.RESET_ALL).join(cells) + " " + Fore.CYAN + "|")

    left_w = cols[0]["width"] + cols[1]["width"] + cols[2]["width"] + 2 * 3
    footer_sep = Fore.CYAN + "+" + "-" * (left_w + 2) + "+" + "-" * (cols[3]["width"] + 2) + "+" + "-" * (cols[4]["width"] + 2) + "+" + "-" * (cols[5]["width"] + 2) + "+"
    print(footer_sep)

    cell_left = Display.pad_cell(f" {Fore.WHITE}{Style.BRIGHT}TOTAL: SEMUA KODE REFERRAL SELESAI", left_w, "<")
    cell_succ = Display.pad_cell(f"{Fore.GREEN}{Style.BRIGHT}{total_succ} Reff{Style.RESET_ALL}", cols[3]["width"], "^")
    cell_targ = Display.pad_cell(f"{Fore.WHITE}{total_targ} Reff", cols[4]["width"], "^")
    cell_fp = Display.pad_cell(f"{Fore.GREEN}{Style.BRIGHT}{total_pts} FP{Style.RESET_ALL}", cols[5]["width"], ">")

    print(Fore.CYAN + "| " + cell_left + " " + Fore.CYAN + "| " + cell_succ + " " + Fore.CYAN + "| " + cell_targ + " " + Fore.CYAN + "| " + cell_fp + " " + Fore.CYAN + "|")
    print(footer_sep)

if __name__ == "__main__":
    run_boost()
