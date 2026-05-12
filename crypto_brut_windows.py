# ===================== WINDOWS GUI VERSION =====================
import time
import threading
import requests
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, simpledialog
from bip_utils import Bip39MnemonicGenerator, Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes, Bip39MnemonicValidator
import itertools
from datetime import datetime

FOUND_FILE = "FOUND_WALLETS.txt"

COINS = {
    "Bitcoin (BTC)": Bip44Coins.BITCOIN,
    "Ethereum (ETH)": Bip44Coins.ETHEREUM,
    "Solana (SOL)": Bip44Coins.SOLANA,
    "Tron (TRX)": Bip44Coins.TRON,
}

def get_balance_info(coin_code, address):
    try:
        if coin_code == "BTC":
            r = requests.get(f"https://api.blockcypher.com/v1/btc/main/addrs/{address}/balance", timeout=8)
            if r.status_code == 200:
                d = r.json()
                return d.get("balance", 0) / 1e8, d.get("n_tx", 0)
        elif coin_code == "ETH":
            r = requests.get(f"https://api.etherscan.io/api?module=account&action=balance&address={address}", timeout=8)
            data = r.json()
            if data.get("status") == "1":
                bal = int(data["result"]) / 1e18
                return bal, 1 if bal > 0 else 0
        elif coin_code == "SOL":
            r = requests.post("https://api.mainnet-beta.solana.com", json={"jsonrpc":"2.0","id":1,"method":"getBalance","params":[address]}, timeout=8)
            if r.status_code == 200:
                bal = r.json()["result"]["value"] / 1e9
                return bal, 1 if bal > 0 else 0
        elif coin_code == "TRX":
            r = requests.get(f"https://api.trongrid.io/v1/accounts/{address}", timeout=8)
            if r.status_code == 200:
                bal = int(r.json().get("balance", 0)) / 1e6
                return bal, 1 if bal > 0 else 0
    except:
        pass
    return 0.0, 0

def generate_from_mnemonic(mnemonic, coin_name):
    try:
        seed = Bip39SeedGenerator(mnemonic).Generate()
        bip44 = Bip44.FromSeed(seed, COINS[coin_name])
        account = bip44.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(0)
        address = account.PublicKey().ToAddress()
        return address
    except:
        return None

def save_found(coin_name, address, mnemonic, balance):
    with open(FOUND_FILE, "a", encoding="utf-8") as f:
        f.write(f"{'='*80}\n")
        f.write(f"ВРЕМЯ: {datetime.now()}\n")
        f.write(f"Сеть: {coin_name}\n")
        f.write(f"Адрес: {address}\n")
        f.write(f"Seed: {mnemonic}\n")
        f.write(f"Баланс: {balance}\n")
        f.write(f"{'='*80}\n\n")

class CryptoBrutPro:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Крипто Брутфорс Про v4.0 — Windows")
        self.root.geometry("1100x800")

        tk.Label(self.root, text="🔥 КРИПТО БРУТФОРС ПРО v4.0", font=("Arial", 18, "bold")).pack(pady=10)

        tk.Label(self.root, text="Сеть:").pack(anchor="w", padx=20)
        self.coin_var = tk.StringVar(value="Bitcoin (BTC)")
        ttk.Combobox(self.root, textvariable=self.coin_var, values=list(COINS.keys()), state="readonly").pack(fill="x", padx=20, pady=5)

        tk.Label(self.root, text="Режим:").pack(anchor="w", padx=20)
        self.mode_var = tk.StringVar(value="normal")
        tk.Radiobutton(self.root, text="1. Обычный режим", variable=self.mode_var, value="normal").pack(anchor="w", padx=30)
        tk.Radiobutton(self.root, text="2. Брут конкретного адреса", variable=self.mode_var, value="target").pack(anchor="w", padx=30)
        tk.Radiobutton(self.root, text="3. Частичный брут мнемоники (самый сильный)", variable=self.mode_var, value="partial").pack(anchor="w", padx=30)

        tk.Label(self.root, text="Потоков:").pack(anchor="w", padx=20)
        self.workers_var = tk.IntVar(value=30)
        tk.Scale(self.root, from_=1, to=60, orient="horizontal", variable=self.workers_var).pack(fill="x", padx=20)

        tk.Button(self.root, text="▶ ЗАПУСТИТЬ", bg="#2196F3", fg="white", font=("Arial", 14, "bold"), height=2, command=self.start).pack(pady=20)

        self.log = scrolledtext.ScrolledText(self.root, height=25, font=("Consolas", 10))
        self.log.pack(fill="both", expand=True, padx=20, pady=10)

    def log_print(self, text):
        self.log.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] {text}\n")
        self.log.see(tk.END)

    def start(self):
        mode = self.mode_var.get()
        coin_name = self.coin_var.get()
        workers = self.workers_var.get()

        if mode == "partial":
            threading.Thread(target=self.partial_brute, args=(coin_name, workers), daemon=True).start()
        elif mode == "target":
            target = simpledialog.askstring("Целевой адрес", "Введите адрес для брута:")
            if target:
                threading.Thread(target=self.target_brute, args=(coin_name, target, workers), daemon=True).start()
        else:
            count = simpledialog.askinteger("Количество", "Сколько кошельков сгенерировать?", initialvalue=2000)
            threading.Thread(target=self.normal_mode, args=(coin_name, count or 2000, workers), daemon=True).start()

    def normal_mode(self, coin_name, count, workers):
        self.log_print(f"Запуск обычного режима: {coin_name} | {count} кошельков")
        # ... (реализация при необходимости)

    def target_brute(self, coin_name, target, workers):
        self.log_print(f"Целевой брут запущен → {target}")

    def partial_brute(self, coin_name, workers):
        self.log_print("🧠 Частичный брут мнемоники")
        example = "word1 word2 X X X X X X X X X X"
        partial = simpledialog.askstring("Введите шаблон", f"Пример:\n{example}\nИспользуйте X для неизвестных слов")
        if not partial:
            return
        words = partial.strip().split()
        unknown_pos = [i for i, w in enumerate(words) if w.upper() == "X"]
        unknown_count = len(unknown_pos)

        self.log_print(f"Неизвестных слов: {unknown_count} | Комбинаций ≈ {2048**unknown_count:,}")

        from bip_utils.bip.bip39.bip39_words import BIP39_ENGLISH_WORDS
        wordlist = list(BIP39_ENGLISH_WORDS)

        def worker():
            for combo in itertools.product(wordlist, repeat=unknown_count):
                candidate = words[:]
                for idx, pos in enumerate(unknown_pos):
                    candidate[pos] = combo[idx]
                mnemonic = " ".join(candidate)
                try:
                    Bip39MnemonicValidator().Validate(mnemonic)
                    address = generate_from_mnemonic(mnemonic, coin_name)
                    if address:
                        balance, tx = get_balance_info(coin_name.split()[0], address)
                        if balance > 0 or tx > 0:
                            self.log_print(f"🎉 НАЙДЕНО! Баланс: {balance} | {address}")
                            save_found(coin_name, address, mnemonic, balance)
                except:
                    continue

        for _ in range(workers):
            t = threading.Thread(target=worker, daemon=True)
            t.start()

if __name__ == "__main__":
    open(FOUND_FILE, "a", encoding="utf-8").close()
    app = CryptoBrutPro()
    app.root.mainloop()
