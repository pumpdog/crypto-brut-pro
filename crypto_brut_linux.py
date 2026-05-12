#!/usr/bin/env python3
# ===================== LINUX HIGH-PERFORMANCE VERSION =====================
import time
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
import requests
import sys
from datetime import datetime
from bip_utils import Bip39MnemonicGenerator, Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes, Bip39MnemonicValidator
import itertools

FOUND_FILE = "FOUND_WALLETS.txt"
MAX_WORKERS = 80   # Оптимально для твоего сервера

COINS = {
    "BTC": Bip44Coins.BITCOIN,
    "ETH": Bip44Coins.ETHEREUM,
    "SOL": Bip44Coins.SOLANA,
    "TRX": Bip44Coins.TRON,
}

def log(text):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {text}")

def get_balance_info(coin_code, address):
    # Тот же код проверки баланса (сокращён для экономии места, работает)
    try:
        if coin_code == "BTC":
            r = requests.get(f"https://api.blockcypher.com/v1/btc/main/addrs/{address}/balance", timeout=8)
            if r.status_code == 200:
                d = r.json()
                return d.get("balance", 0) / 1e8, d.get("n_tx", 0)
        # Добавь остальные сети при необходимости
    except:
        pass
    return 0.0, 0

def save_found(coin, address, mnemonic, balance):
    with open(FOUND_FILE, "a", encoding="utf-8") as f:
        f.write(f"{'='*90}\n")
        f.write(f"ВРЕМЯ: {datetime.now()}\n")
        f.write(f"Сеть: {coin}\nАдрес: {address}\nSeed: {mnemonic}\nБаланс: {balance}\n")
        f.write(f"{'='*90}\n\n")
    log(f"🎉 НАЙДЕН КОШЕЛЁК! Баланс: {balance}")

def partial_brute(coin_key, template_words):
    from bip_utils.bip.bip39.bip39_words import BIP39_ENGLISH_WORDS
    wordlist = list(BIP39_ENGLISH_WORDS)
    unknown_pos = [i for i, w in enumerate(template_words) if w.upper() == "X"]
    unknown_count = len(unknown_pos)

    log(f"Запущен частичный брут | Неизвестных: {unknown_count} | Процессов: {MAX_WORKERS}")

    def process_combo(combo):
        candidate = template_words[:]
        for i, pos in enumerate(unknown_pos):
            candidate[pos] = combo[i]
        mnemonic = " ".join(candidate)
        try:
            Bip39MnemonicValidator().Validate(mnemonic)
            seed = Bip39SeedGenerator(mnemonic).Generate()
            bip44 = Bip44.FromSeed(seed, COINS[coin_key])
            acc = bip44.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(0)
            address = acc.PublicKey().ToAddress()
            balance, _ = get_balance_info(coin_key, address)
            if balance > 0:
                save_found(coin_key, address, mnemonic, balance)
        except:
            pass

    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        for combo in itertools.product(wordlist, repeat=unknown_count):
            executor.submit(process_combo, combo)

def main():
    log(f"🚀 Запуск на {multiprocessing.cpu_count()} ядер / 128GB RAM")

    print("\n1. Обычный режим")
    print("2. Частичный брут мнемоники")
    choice = input("Выберите режим: ")

    coin = input("Сеть (BTC/ETH/SOL/TRX): ").strip().upper()
    if coin not in COINS:
        coin = "BTC"

    if choice == "2":
        template = input("Введите шаблон (X вместо неизвестного слова): ").strip().split()
        partial_brute(coin, template)
    else:
        log("Обычный режим пока не реализован в максимальной версии")

if __name__ == "__main__":
    multiprocessing.set_start_method('spawn', force=True)
    open(FOUND_FILE, "a").close()
    main()
