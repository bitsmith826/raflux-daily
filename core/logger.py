import sys
from datetime import datetime
from colorama import init, Fore, Style

# Ensure stdout handles UTF-8 on Windows
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

init(autoreset=True)

class Logger:
    @staticmethod
    def _time():
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @classmethod
    def info(cls, msg: str):
        print(f"{Fore.LIGHTBLACK_EX}[{cls._time()}]{Style.RESET_ALL} {Fore.CYAN}[INFO]{Style.RESET_ALL} {msg}")

    @classmethod
    def success(cls, msg: str):
        print(f"{Fore.LIGHTBLACK_EX}[{cls._time()}]{Style.RESET_ALL} {Fore.GREEN}[SUCCESS]{Style.RESET_ALL} {msg}")

    @classmethod
    def warn(cls, msg: str):
        print(f"{Fore.LIGHTBLACK_EX}[{cls._time()}]{Style.RESET_ALL} {Fore.YELLOW}[WARN]{Style.RESET_ALL} {msg}")

    @classmethod
    def error(cls, msg: str):
        print(f"{Fore.LIGHTBLACK_EX}[{cls._time()}]{Style.RESET_ALL} {Fore.RED}[ERROR]{Style.RESET_ALL} {msg}")

    @classmethod
    def wallet(cls, idx: int, total: int, address: str):
        short = f"{address[:6]}...{address[-6:]}"
        print(f"\n{Fore.LIGHTBLACK_EX}[{cls._time()}]{Style.RESET_ALL} {Fore.MAGENTA}[WALLET {idx}/{total}]{Style.RESET_ALL} {Fore.LIGHTWHITE_EX}{short}{Style.RESET_ALL} ({address})")

    @classmethod
    def banner(cls):
        art = f"""{Fore.CYAN}
  ____         __ _                 ____        _ _       
 |  _ \\ __ _  / _| |_   ___  __    |  _ \\  __ _(_) |_   _ 
 | |_) / _` || |_| | | | \\ \\/ /____| | | |/ _` | | | | | |
 |  _ < (_| ||  _| | |_| |>  <_____| |_| | (_| | | | |_| |
 |_| \\_\\__,_||_| |_|\\__,_/_/\\_\\    |____/ \\__,_|_|_|\\__, |
                                                    |___/ 
        {Fore.YELLOW}>> Automated Solana Daily Bot for Raflux.io <<{Fore.CYAN}
        {Fore.LIGHTBLACK_EX}* Daily Check-in * Referral Bonus * Quest Claims * Points Tracker
{Style.RESET_ALL}"""
        print(art)
