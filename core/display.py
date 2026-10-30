import re
import sys
from datetime import datetime
from colorama import init, Fore, Style
from typing import List, Dict, Any

# Ensure stdout handles UTF-8 on Windows
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

init(autoreset=True)

ANSI_REGEX = re.compile(r'\x1b\[[0-9;]*m')

class Display:
    BOX_WIDTH = 86

    @staticmethod
    def strip_ansi(text: str) -> str:
        return ANSI_REGEX.sub('', text)

    @classmethod
    def vlen(cls, text: str) -> int:
        return len(cls.strip_ansi(text))

    @classmethod
    def pad_box(cls, content: str, width: int = None, border_col: str = Fore.CYAN) -> str:
        w = width or cls.BOX_WIDTH
        pad = (w - 2) - cls.vlen(content)
        return f"{border_col}|{Style.RESET_ALL}{content}{' ' * max(0, pad)}{border_col}|{Style.RESET_ALL}"

    @classmethod
    def pad_cell(cls, text: str, width: int, align: str = "<") -> str:
        raw_len = cls.vlen(text)
        pad = width - raw_len
        if pad <= 0:
            return text
        if align == "<":
            return text + (" " * pad)
        elif align == ">":
            return (" " * pad) + text
        else:
            left_pad = pad // 2
            right_pad = pad - left_pad
            return (" " * left_pad) + text + (" " * right_pad)

    @classmethod
    def banner(cls):
        w = cls.BOX_WIDTH
        top_eq = Fore.CYAN + "+" + "=" * (w - 2) + "+" + Style.RESET_ALL
        
        art_lines = [
            "  _____             ______ _       _   _ __   __  ",
            " |  __ \\     /\\    |  ____| |     | | | |\\ \\ / /  ",
            " | |__) |   /  \\   | |__  | |     | | | | \\ V /   ",
            " |  _  /   / /\\ \\  |  __| | |     | | | |  > <    ",
            " | | \\ \\  / ____ \\ | |    | |____ | |_| | / . \\   ",
            " |_|  \\_\\/_/    \\_\\|_|    |______| \\___/ /_/ \\_\\  ",
        ]
        
        print("\n" + top_eq)
        inner = w - 2
        for line in art_lines:
            pad_left = (inner - len(line)) // 2
            centered = " " * pad_left + line
            print(cls.pad_box(f"{Fore.LIGHTCYAN_EX}{Style.BRIGHT}{centered}", w))
            
        print(cls.pad_box(" ", w))
        tagline = ">> AUTOMATED MULTI-ACCOUNT AIRDROP SYSTEM (SOLANA NETWORK) <<"
        p_tag = (inner - len(tagline)) // 2
        print(cls.pad_box(f"{' ' * p_tag}{Fore.YELLOW}{Style.BRIGHT}{tagline}{Style.RESET_ALL}", w))
        
        feats = "* Daily Check-In  * Referral Bonus  * Quests Tracker  * CSV Reports"
        p_feat = (inner - len(feats)) // 2
        print(cls.pad_box(f"{' ' * p_feat}{Fore.LIGHTBLACK_EX}{feats}{Style.RESET_ALL}", w))
        print(top_eq)

    @classmethod
    def config_box(cls, total_wallets: int, ref_code: str, delay_range: list, proxies_count: int, loop_mode: bool):
        w = cls.BOX_WIDTH
        proxy_text = f"{proxies_count} Aktif" if proxies_count > 0 else "Direct (Tanpa Proxy)"
        loop_text = "Aktif (Loop 24 Jam)" if loop_mode else "Single Run (Sekali Jalan)"
        
        title = " [ KONFIGURASI BOT ] "
        dash_r = w - 2 - len(title) - 2
        top_dash = Fore.CYAN + "+" + "-" * (w - 2) + "+" + Style.RESET_ALL
        
        print(f"\n{Fore.CYAN}+--{Fore.WHITE}{Style.BRIGHT}{title}{Style.RESET_ALL}{Fore.CYAN}{'-' * dash_r}+{Style.RESET_ALL}")
        print(cls.pad_box(f"  {Fore.WHITE}Total Akun Terdaftar  : {Fore.YELLOW}{Style.BRIGHT}{total_wallets} Wallets{Style.RESET_ALL}{' '*8}{Fore.WHITE}Referral Code : {Fore.GREEN}{ref_code}", w))
        print(cls.pad_box(f"  {Fore.WHITE}Jeda Antar Akun       : {Fore.YELLOW}{delay_range[0]} - {delay_range[1]} Detik{Style.RESET_ALL}{' '*7}{Fore.WHITE}Status Proxy  : {Fore.CYAN}{proxy_text}", w))
        print(cls.pad_box(f"  {Fore.WHITE}Mode Eksekusi         : {Fore.MAGENTA}{loop_text}", w))
        print(top_dash)

    @classmethod
    def wallet_card(cls, idx: int, total: int, address: str, username: str, ref_msg: str, checkin_msg: str, streak: int, points: int, is_new: bool = False):
        w = cls.BOX_WIDTH
        short_addr = f"{address[:5]}...{address[-5:]}" if len(address) > 12 else address
        tag = "[BARU]" if is_new else "[OK]"
        hdr = f" [AKUN {idx:02d}/{total:02d}] {short_addr} {tag} "
        dash_r = w - 2 - len(hdr) - 2
        top_dash = Fore.CYAN + "+" + "-" * (w - 2) + "+" + Style.RESET_ALL
        
        color_check = Fore.GREEN if "sukses" in checkin_msg.lower() else (Fore.CYAN if "sudah" in checkin_msg.lower() else Fore.YELLOW)
        
        print(f"\n{Fore.CYAN}+--{Fore.WHITE}{Style.BRIGHT}{hdr}{Style.RESET_ALL}{Fore.CYAN}{'-' * dash_r}+{Style.RESET_ALL}")
        print(cls.pad_box(f"  {Fore.LIGHTBLACK_EX}[+] {Fore.WHITE}Solana Address : {Fore.LIGHTWHITE_EX}{address}", w))
        print(cls.pad_box(f"  {Fore.LIGHTBLACK_EX}[+] {Fore.WHITE}Username       : {Fore.YELLOW}{username}", w))
        print(cls.pad_box(f"  {Fore.LIGHTBLACK_EX}[+] {Fore.WHITE}Referral Code  : {Fore.GREEN}{ref_msg}", w))
        print(cls.pad_box(f"  {Fore.LIGHTBLACK_EX}[+] {Fore.WHITE}Daily Check-In : {color_check}{checkin_msg}", w))
        print(cls.pad_box(f"  {Fore.LIGHTBLACK_EX}[+] {Fore.WHITE}Streak Harian  : {Fore.CYAN}{streak} Hari", w))
        print(cls.pad_box(f"  {Fore.LIGHTBLACK_EX}[=] {Fore.WHITE}Total Saldo    : {Fore.YELLOW}{Style.BRIGHT}{points} Flux Points", w))
        print(top_dash)

    @classmethod
    def summary_table(cls, rows: List[Dict[str, Any]]):
        cols = [
            {"name": "No",       "key": "no",       "width": 3,  "align": "^"},
            {"name": "Address",  "key": "addr",     "width": 13, "align": "<"},
            {"name": "Username", "key": "user",     "width": 15, "align": "<"},
            {"name": "Check-In", "key": "check",    "width": 10, "align": "<"},
            {"name": "Streak",   "key": "streak",   "width": 8,  "align": "^"},
            {"name": "Saldo",    "key": "points",   "width": 9,  "align": ">"},
            {"name": "Status",   "key": "status",   "width": 6,  "align": "^"},
        ]
        
        def get_sep(char="-"):
            parts = ["+" + char * (c["width"] + 2) for c in cols]
            return Fore.CYAN + "".join(parts) + "+" + Style.RESET_ALL

        print("\n" + get_sep("-"))
        hdr_cells = [cls.pad_cell(f"{Fore.WHITE}{Style.BRIGHT}{c['name']}{Style.RESET_ALL}", c["width"], "^") for c in cols]
        print(Fore.CYAN + "| " + (" " + Fore.CYAN + "| " + Style.RESET_ALL).join(hdr_cells) + " " + Fore.CYAN + "|")
        print(get_sep("="))

        total_fp = 0
        success_cnt = 0
        total_streak = 0

        for r in rows:
            no = f"{r.get('index', 0):02d}"
            raw_addr = r.get('address', '')
            addr = f"{raw_addr[:4]}...{raw_addr[-5:]}" if len(raw_addr) > 12 else raw_addr
            user = str(r.get('username', '-'))[:15]
            
            c_raw = str(r.get('checkin_status', ''))
            if "sukses" in c_raw.lower():
                check_disp = f"{Fore.GREEN}Sukses{Style.RESET_ALL}"
            elif "sudah" in c_raw.lower():
                check_disp = f"{Fore.CYAN}Sudah{Style.RESET_ALL}"
            else:
                check_disp = f"{Fore.RED}Gagal{Style.RESET_ALL}"

            streak_val = r.get('streak', 0)
            total_streak += streak_val
            streak_disp = f"{Fore.CYAN}{streak_val} Hari{Style.RESET_ALL}"

            pts_val = r.get('points', 0)
            total_fp += pts_val
            pts_disp = f"{Fore.YELLOW}{Style.BRIGHT}{pts_val} FP{Style.RESET_ALL}"

            is_ok = (r.get('status') == 'Sukses')
            if is_ok:
                success_cnt += 1
                stat_disp = f"{Fore.GREEN}AKTIF{Style.RESET_ALL}"
            else:
                stat_disp = f"{Fore.RED}ERROR{Style.RESET_ALL}"

            row_data = {
                "no": no,
                "addr": addr,
                "user": user,
                "check": check_disp,
                "streak": streak_disp,
                "points": pts_disp,
                "status": stat_disp
            }

            cells = [cls.pad_cell(str(row_data[c["key"]]), c["width"], c["align"]) for c in cols]
            print(Fore.CYAN + "| " + (" " + Fore.CYAN + "| " + Style.RESET_ALL).join(cells) + " " + Fore.CYAN + "|")

        left_w = cols[0]["width"] + cols[1]["width"] + cols[2]["width"] + cols[3]["width"] + 3 * 3
        footer_sep = Fore.CYAN + "+" + "-" * (left_w + 2) + "+" + "-" * (cols[4]["width"] + 2) + "+" + "-" * (cols[5]["width"] + 2) + "+" + "-" * (cols[6]["width"] + 2) + "+"
        
        print(footer_sep)
        
        pct = int((success_cnt / len(rows) * 100)) if rows else 0
        avg_streak = round(total_streak / len(rows)) if rows else 0
        
        cell_left = cls.pad_cell(f" {Fore.WHITE}{Style.BRIGHT}TOTAL: {success_cnt}/{len(rows)} AKUN BERHASIL", left_w, "<")
        cell_streak = cls.pad_cell(f"{Fore.CYAN}{avg_streak} Hari", cols[4]["width"], "^")
        cell_pts = cls.pad_cell(f"{Fore.GREEN}{Style.BRIGHT}{total_fp} FP{Style.RESET_ALL}", cols[5]["width"], ">")
        cell_stat = cls.pad_cell(f"{Fore.GREEN}{pct}%", cols[6]["width"], "^")
        
        print(Fore.CYAN + "| " + cell_left + " " + Fore.CYAN + "| " + cell_streak + " " + Fore.CYAN + "| " + cell_pts + " " + Fore.CYAN + "| " + cell_stat + " " + Fore.CYAN + "|")
        print(footer_sep)

    @classmethod
    def finish_box(cls, success_count: int, total: int, total_fp: int, report_file: str):
        w = cls.BOX_WIDTH
        pct = int((success_count / total * 100)) if total else 0
        
        title = " [ LAPORAN EKSEKUSI SELESAI ] "
        dash_r = w - 2 - len(title) - 2
        top_eq = Fore.GREEN + "+" + "=" * (w - 2) + "+" + Style.RESET_ALL
        
        print(f"\n{Fore.GREEN}+=={Fore.WHITE}{Style.BRIGHT}{title}{Style.RESET_ALL}{Fore.GREEN}{'=' * dash_r}+{Style.RESET_ALL}")
        print(cls.pad_box(f"  {Fore.WHITE}Status Eksekusi      : {Fore.GREEN}{Style.BRIGHT}{success_count}/{total} Akun Sukses ({pct}% Berhasil)", w, Fore.GREEN))
        print(cls.pad_box(f"  {Fore.WHITE}Total Akumulasi Poin : {Fore.YELLOW}{Style.BRIGHT}{total_fp} Flux Points", w, Fore.GREEN))
        print(cls.pad_box(f"  {Fore.WHITE}File Rekapitulasi    : {Fore.CYAN}{report_file}", w, Fore.GREEN))
        print(top_eq + "\n")
