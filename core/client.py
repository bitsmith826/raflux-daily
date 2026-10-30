import json
import os
import requests
from typing import Optional, Dict, Any, Tuple
from core.wallet import SolanaWallet
from core.logger import Logger

class RafluxClient:
    def __init__(self, wallet: SolanaWallet, base_url: str = "https://api.raflux.io/solana/v1", proxy: Optional[str] = None):
        self.wallet = wallet
        self.base_url = base_url.rstrip("/")
        self.token: Optional[str] = None
        self.proxy = proxy
        self.session = requests.Session()
        
        if self.proxy:
            self.session.proxies = {
                "http": self.proxy,
                "https": self.proxy
            }
        
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Origin": "https://raflux.io",
            "Referer": "https://raflux.io/",
            "Content-Type": "application/json"
        })

    def _get_auth_headers(self) -> Dict[str, str]:
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def authenticate(self, token_cache_file: str = "data/tokens.json") -> bool:
        """Checks if a cached token exists and is valid, or executes SIWS login."""
        # Try loading from cache
        if os.path.exists(token_cache_file):
            try:
                with open(token_cache_file, "r", encoding="utf-8") as f:
                    cache = json.load(f)
                    if self.wallet.address in cache:
                        self.token = cache[self.wallet.address]
                        # Verify token with /me
                        res = self.get_profile()
                        if res and res.get("status") == 200:
                            return True
            except Exception:
                pass

        # Execute fresh SIWS login
        import time
        for attempt in range(1, 4):
            try:
                # 1. Request Challenge Message
                siws_url = f"{self.base_url}/siws"
                resp = self.session.post(siws_url, json={"address": self.wallet.address}, timeout=30)
                if resp.status_code == 429:
                    time.sleep(7.5)
                    continue
                if resp.status_code not in (200, 201):
                    Logger.error(f"Gagal meminta SIWS challenge: HTTP {resp.status_code} - {resp.text}")
                    return False
                
                data = resp.json()
                challenge = data.get("data", {}).get("message") or data.get("message")
                if not challenge:
                    Logger.error("Pesan challenge tidak ditemukan dalam respons server.")
                    return False

                # 2. Sign Challenge Message
                signature = self.wallet.sign_message(challenge)

                # 3. Submit Login
                login_url = f"{self.base_url}/login"
                login_payload = {
                    "address": self.wallet.address,
                    "message": challenge,
                    "signature": signature
                }
                resp_login = self.session.post(login_url, json=login_payload, timeout=30)
                if resp_login.status_code == 429:
                    time.sleep(7.5)
                    continue
                if resp_login.status_code not in (200, 201):
                    Logger.error(f"Gagal login ke Raflux: HTTP {resp_login.status_code} - {resp_login.text}")
                    return False

                login_data = resp_login.json()
                token = login_data.get("data", {}).get("token") or login_data.get("token")
                if not token:
                    Logger.error("Token JWT tidak ditemukan dalam respons login.")
                    return False

                self.token = token
                is_new = login_data.get("data", {}).get("isNewUser", False)

                # Save token to cache
                try:
                    cache = {}
                    if os.path.exists(token_cache_file):
                        with open(token_cache_file, "r", encoding="utf-8") as f:
                            cache = json.load(f)
                    cache[self.wallet.address] = self.token
                    with open(token_cache_file, "w", encoding="utf-8") as f:
                        json.dump(cache, f, indent=2)
                except Exception as e:
                    pass

                return True
            except Exception as e:
                if attempt < 3:
                    time.sleep(3)
                    continue
                Logger.error(f"Terjadi kesalahan saat autentikasi: {e}")
                return False
        return False

    def get_profile(self) -> Optional[Dict[str, Any]]:
        """Retrieves user profile info."""
        try:
            url = f"{self.base_url}/me"
            resp = self.session.get(url, headers=self._get_auth_headers(), timeout=20)
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass
        return None

    def get_points(self) -> Optional[Dict[str, Any]]:
        """Retrieves points balance."""
        try:
            url = f"{self.base_url}/me/points"
            resp = self.session.get(url, headers=self._get_auth_headers(), timeout=20)
            if resp.status_code == 200:
                return resp.json().get("data", {})
        except Exception as e:
            Logger.error(f"Gagal mengambil poin: {e}")
        return None

    def get_referral_info(self) -> Optional[Dict[str, Any]]:
        """Retrieves referral details (own referral code, active referrals, bonus status)."""
        try:
            url = f"{self.base_url}/me/referral-code"
            resp = self.session.get(url, headers=self._get_auth_headers(), timeout=20)
            if resp.status_code == 200:
                return resp.json().get("data", {})
        except Exception:
            pass
        return None

    def claim_referral(self, code: str) -> Tuple[bool, str]:
        """Submits a referral code (+20 points)."""
        import time
        prof = self.get_profile()
        if prof and prof.get("data", {}).get("canClaimReferral") is False:
            return False, "Sudah klaim referral sebelumnya"

        for attempt in range(1, 4):
            try:
                url = f"{self.base_url}/referrals/claim"
                resp = self.session.post(url, json={"code": code}, headers=self._get_auth_headers(), timeout=20)
                if resp.status_code == 429:
                    time.sleep(7.5)
                    continue
                if resp.status_code in (200, 201):
                    return True, f"Kode referral '{code}' berhasil diklaim!"
                
                res_json = resp.json()
                msg = res_json.get("message") or res_json.get("code") or resp.text
                return False, f"HTTP {resp.status_code}: {msg}"
            except Exception as e:
                if attempt < 3:
                    time.sleep(3)
                    continue
                return False, str(e)
        return False, "Rate limit exceeded"

    def collect_welcome_points(self) -> Tuple[bool, str]:
        """Collects 20 welcome bonus points."""
        import time
        ref_info = self.get_referral_info()
        if ref_info and not ref_info.get("welcomeBonusPending", False):
            return True, "Welcome bonus sudah diklaim sebelumnya."

        for attempt in range(1, 4):
            try:
                url = f"{self.base_url}/me/referrals/collect-welcome-points"
                resp = self.session.post(url, headers=self._get_auth_headers(), timeout=20)
                if resp.status_code == 429:
                    time.sleep(7.5)
                    continue
                if resp.status_code == 200:
                    data = resp.json().get("data", {})
                    pts = data.get("points", 0) if isinstance(data, dict) else 0
                    if pts > 0:
                        return True, f"Berhasil klaim welcome bonus: +{pts} Flux Points!"
                    else:
                        return True, "Welcome bonus sudah diklaim sebelumnya."
                
                res_json = resp.json()
                msg = res_json.get("message") or res_json.get("code") or resp.text
                return False, f"HTTP {resp.status_code}: {msg}"
            except Exception as e:
                if attempt < 3:
                    time.sleep(3)
                    continue
                return False, str(e)
        return False, "Rate limit exceeded"

    def daily_check_in(self) -> Tuple[bool, str, int]:
        """Executes daily check-in. Returns (success, message, streak_days)."""
        try:
            # First check quests status to avoid redundant requests if already checked in today
            qdata = self.get_quests()
            if qdata and "streak" in qdata:
                streak_info = qdata.get("streak", {})
                current_streak = streak_info.get("current", 1)
                if streak_info.get("checkedInToday"):
                    return True, f"Sudah check-in hari ini (Streak {current_streak} Hari).", current_streak

            # Perform check-in with rate-limit retry
            url = f"{self.base_url}/quests/check-in"
            for attempt in range(1, 3):
                resp = self.session.post(url, headers=self._get_auth_headers(), timeout=20)
                if resp.status_code == 200:
                    data = resp.json().get("data", {})
                    fp = data.get("fpAwarded", 1)
                    streak = data.get("streak", {}).get("current", 1)
                    return True, f"Check-in harian sukses! +{fp} FP (Streak {streak} Hari)", streak
                elif resp.status_code == 429:
                    if attempt < 2:
                        import time
                        time.sleep(7.5)
                        continue
                
                res_json = resp.json() if resp.status_code in (400, 429, 409) else {}
                code = res_json.get("code", "")
                if code in ("QUEST_ALREADY_CHECKED_IN", "QUEST_ALREADY_CLAIMED"):
                    streak = 1
                    if qdata and "streak" in qdata:
                        streak = qdata.get("streak", {}).get("current", 1)
                    return True, f"Sudah check-in hari ini (Streak {streak} Hari).", streak
                
                msg = res_json.get("message") or code or resp.text
                return False, f"Check-in gagal: {msg}", 0
        except Exception as e:
            return False, str(e), 0

    def get_quests(self) -> Optional[Dict[str, Any]]:
        """Retrieves list of quests."""
        try:
            url = f"{self.base_url}/quests"
            resp = self.session.get(url, headers=self._get_auth_headers(), timeout=20)
            if resp.status_code == 200:
                return resp.json().get("data", {})
        except Exception as e:
            Logger.error(f"Gagal mengambil daftar quest: {e}")
        return None

    def claim_quest(self, quest_id: str) -> Tuple[bool, str]:
        """Claims a claimable quest or milestone."""
        try:
            url = f"{self.base_url}/quests/{quest_id}/claim"
            resp = self.session.post(url, headers=self._get_auth_headers(), timeout=20)
            if resp.status_code == 200:
                data = resp.json().get("data", {})
                fp = data.get("fpAwarded", 0) if isinstance(data, dict) else 0
                return True, f"Quest berhasil diklaim (+{fp} FP)!"
            return False, f"Gagal klaim: {resp.text}"
        except Exception as e:
            return False, str(e)

    def process_all_quests(self):
        """Scans quest list and claims any that are in CLAIMABLE status."""
        data = self.get_quests()
        if not data or not data.get("quests"):
            return

        quests = data["quests"]
        claimed_any = False
        for q in quests:
            qid = q.get("id")
            title = q.get("title", "Unknown Quest")
            status = q.get("status")
            
            # Check milestones if present
            milestones = q.get("milestones") or []
            has_claimable_milestone = any(m.get("status") == "CLAIMABLE" for m in milestones)
            
            if status == "CLAIMABLE" or has_claimable_milestone:
                Logger.info(f"Mengklaim quest: {title}...")
                ok, msg = self.claim_quest(qid)
                if ok:
                    Logger.success(f"Quest [{title}] -> {msg}")
                    claimed_any = True
                else:
                    Logger.warn(f"Quest [{title}] -> {msg}")

        pass
