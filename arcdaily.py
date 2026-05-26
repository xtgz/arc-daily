#!/usr/bin/env python3
"""
ARC Testnet Daily Interactions Bot
- GM message, self-transfers, contract deploy, ERC20, etc.
- Multi-wallet with unique proxy per wallet
- Progress tracking to avoid duplicate actions
- 24h cooldown loop mode

Usage:
    python3 arcdaily.py              # Run once
    python3 arcdaily.py --loop       # Run with 24h cooldown loop
    python3 arcdaily.py --reset      # Reset progress

Files:
    privkey.txt    - 1 private key per line
    proxy.txt      - 1 proxy per line (http://user:pass@host:port)
"""

import os
import sys
import json
import time
import random
import argparse
from web3 import Web3
from eth_account import Account
from datetime import datetime

# ============ CONFIG ============
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PRIVKEY_FILE = os.path.join(SCRIPT_DIR, "privkey.txt")
PROXY_FILE = os.path.join(SCRIPT_DIR, "proxy.txt")
PROGRESS_FILE = os.path.join(SCRIPT_DIR, "progress.json")
LOG_FILE = os.path.join(SCRIPT_DIR, "daily.log")

# ARC Network
ARC_RPC = "https://rpc.testnet.arc.network"
CHAIN_ID = 5042002
EXPLORER = "https://testnet.arcscan.app"

# User agents for fingerprint diversity
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 OPR/111.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Vivaldi/6.7",
]

# Simple contract bytecode (minimal)
SIMPLE_CONTRACT_BYTECODE = "0x6080604052348015600e575f5ffd5b50603e80601a5f395ff3fe60806040525f5ffdfea264697066735822122000000000000000000000000000000000000000000000000000000000000000006473"

# ============ HELPERS ============

def log(msg):
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def load_wallets():
    """Load private keys from privkey.txt (1 per line)"""
    if not os.path.exists(PRIVKEY_FILE):
        log(f"❌ {PRIVKEY_FILE} not found!")
        log("Create privkey.txt with 1 private key per line")
        sys.exit(1)
    
    with open(PRIVKEY_FILE) as f:
        keys = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    
    wallets = []
    for pk in keys:
        try:
            account = Account.from_key(pk)
            wallets.append({"address": account.address, "private_key": pk})
        except Exception as e:
            log(f"⚠️ Invalid key: {pk[:10]}... - {e}")
    
    return wallets

def load_proxies():
    """Load proxies from proxy.txt (1 per line)"""
    if not os.path.exists(PROXY_FILE):
        return []
    
    with open(PROXY_FILE) as f:
        proxies = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    
    return proxies

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {}

def save_progress(progress):
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f, indent=2)

def get_w3(proxy_url=None):
    """Get Web3 instance with optional proxy"""
    if proxy_url:
        from web3.providers.rpc import HTTPProvider
        return Web3(HTTPProvider(ARC_RPC, request_kwargs={"proxies": {"http": proxy_url, "https": proxy_url}}))
    return Web3(Web3.HTTPProvider(ARC_RPC))

def wait_tx(w3, tx_hash, timeout=60):
    """Wait for transaction receipt"""
    start = time.time()
    while time.time() - start < timeout:
        try:
            receipt = w3.eth.get_transaction_receipt(tx_hash)
            if receipt:
                return receipt
        except:
            pass
        time.sleep(2)
    return None

def countdown(seconds, label="Next run"):
    """Live countdown timer"""
    while seconds > 0:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        print(f"\r  ⏱️ {label} in: {hours:02d}:{minutes:02d}:{secs:02d}", end="", flush=True)
        time.sleep(1)
        seconds -= 1
    print()

# ============ ACTIONS ============

def send_gm(w3, account):
    """Send GM message on-chain"""
    log("  [GM] Sending GM...")
    nonce = w3.eth.get_transaction_count(account.address, 'pending')
    
    gm_data = "0x" + "gm from arc testnet farmer".encode().hex()
    
    tx = {
        'nonce': nonce,
        'to': account.address,
        'value': 0,
        'gas': 30000,
        'gasPrice': w3.eth.gas_price,
        'chainId': CHAIN_ID,
        'data': gm_data
    }
    
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    log(f"  [GM] TX: {EXPLORER}/tx/0x{tx_hash.hex()}")
    
    receipt = wait_tx(w3, tx_hash)
    if receipt and receipt['status'] == 1:
        log(f"  [GM] ✅ Confirmed in block {receipt['blockNumber']}")
        return True
    log(f"  [GM] ❌ Failed")
    return False

def self_transfer(w3, account, amount=None):
    """Self-transfer to create on-chain activity"""
    if amount is None:
        amount = random.randint(1, 100)
    
    log(f"  [TRANSFER] Self-transfer {amount} wei...")
    nonce = w3.eth.get_transaction_count(account.address, 'pending')
    
    tx = {
        'nonce': nonce,
        'to': account.address,
        'value': amount,
        'gas': 21000,
        'gasPrice': w3.eth.gas_price,
        'chainId': CHAIN_ID
    }
    
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    log(f"  [TRANSFER] TX: {EXPLORER}/tx/0x{tx_hash.hex()}")
    
    receipt = wait_tx(w3, tx_hash)
    if receipt and receipt['status'] == 1:
        log(f"  [TRANSFER] ✅ Confirmed")
        return True
    log(f"  [TRANSFER] ❌ Failed")
    return False

def deploy_contract(w3, account):
    """Deploy a minimal contract"""
    log("  [DEPLOY] Deploying contract...")
    nonce = w3.eth.get_transaction_count(account.address, 'pending')
    
    tx = {
        'nonce': nonce,
        'data': SIMPLE_CONTRACT_BYTECODE,
        'gas': 200000,
        'gasPrice': w3.eth.gas_price,
        'chainId': CHAIN_ID,
        'value': 0,
    }
    
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    log(f"  [DEPLOY] TX: {EXPLORER}/tx/0x{tx_hash.hex()}")
    
    receipt = wait_tx(w3, tx_hash)
    if receipt and receipt['status'] == 1:
        contract_addr = receipt['contractAddress']
        log(f"  [DEPLOY] ✅ Contract at: {contract_addr}")
        return contract_addr
    log(f"  [DEPLOY] ❌ Failed")
    return None

def batch_transfers(w3, account, count=3):
    """Multiple self-transfers with varying amounts"""
    log(f"  [BATCH] {count} random transfers...")
    success = 0
    for i in range(count):
        amount = random.randint(1, 1000)
        if self_transfer(w3, account, amount):
            success += 1
        time.sleep(random.uniform(3, 8))
    log(f"  [BATCH] Done: {success}/{count}")
    return success

def send_message(w3, account, msg=None):
    """Send arbitrary message on-chain"""
    if msg is None:
        messages = [
            "gm from arc farmer",
            "building on arc testnet",
            "arc to the moon",
            "stablecoin native future",
            "onchain finance"
        ]
        msg = random.choice(messages)
    
    log(f"  [MSG] Sending: {msg}")
    nonce = w3.eth.get_transaction_count(account.address, 'pending')
    
    data = "0x" + msg.encode().hex()
    
    tx = {
        'nonce': nonce,
        'to': account.address,
        'value': 0,
        'gas': 30000,
        'gasPrice': w3.eth.gas_price,
        'chainId': CHAIN_ID,
        'data': data
    }
    
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    log(f"  [MSG] TX: {EXPLORER}/tx/0x{tx_hash.hex()}")
    
    receipt = wait_tx(w3, tx_hash)
    if receipt and receipt['status'] == 1:
        log(f"  [MSG] ✅ Confirmed")
        return True
    log(f"  [MSG] ❌ Failed")
    return False

# ============ MAIN ============

def run_daily():
    """Run one cycle of daily interactions"""
    log("=" * 60)
    log("ARC Daily Interactions - Run Cycle")
    log("=" * 60)
    
    wallets = load_wallets()
    proxies = load_proxies()
    log(f"Loaded {len(wallets)} wallets, {len(proxies)} proxies")
    
    progress = load_progress()
    today = datetime.utcnow().strftime("%Y-%m-%d")
    
    total_success = 0
    total_failed = 0
    processed = 0
    
    for i, wallet in enumerate(wallets):
        address = wallet["address"]
        pk = wallet["private_key"]
        
        log(f"\n[{i+1}/{len(wallets)}] {address}")
        
        # Check if already done today
        wallet_key = address.lower()
        if progress.get(wallet_key, {}).get("last_run", "").startswith(today):
            log(f"  ⏭️ Already done today, skipping")
            processed += 1
            continue
        
        # Check balance first (via direct RPC, no proxy for speed)
        w3_direct = get_w3()
        balance = w3_direct.eth.get_balance(address)
        
        if balance == 0:
            log(f"  ⚠️ Balance is 0, need to claim faucet first")
            total_failed += 1
            continue
        
        log(f"  💰 Balance: {w3_direct.from_wei(balance, 'ether')} ETH")
        
        # Create account
        account = Account.from_key(pk)
        
        # Get proxy for this wallet (rotate through available proxies)
        proxy_url = None
        if proxies:
            proxy_url = proxies[i % len(proxies)]
        
        w3 = get_w3(proxy_url)
        
        # Run actions
        actions_done = []
        
        # 1. GM
        if send_gm(w3, account):
            actions_done.append("GM")
        time.sleep(3)
        
        # 2. Self transfer
        if self_transfer(w3, account):
            actions_done.append("Transfer")
        time.sleep(3)
        
        # 3. Deploy contract (50% chance)
        if random.random() < 0.5:
            addr = deploy_contract(w3, account)
            if addr:
                actions_done.append("Deploy")
            time.sleep(3)
        
        # 4. Batch transfers (2-4)
        count = random.randint(2, 4)
        success = batch_transfers(w3, account, count)
        if success > 0:
            actions_done.append(f"Batch({success}/{count})")
        time.sleep(3)
        
        # 5. Send message
        if send_message(w3, account):
            actions_done.append("Message")
        
        # Update progress
        progress[wallet_key] = {
            "last_run": datetime.utcnow().isoformat(),
            "actions": actions_done,
            "balance": str(balance)
        }
        save_progress(progress)
        processed += 1
        
        if actions_done:
            total_success += 1
            log(f"  ✅ Done: {', '.join(actions_done)}")
        else:
            total_failed += 1
            log(f"  ❌ No actions completed")
        
        # Delay between wallets
        if i < len(wallets) - 1:
            delay = random.uniform(30, 60)
            log(f"  ⏳ Waiting {delay:.0f}s...")
            time.sleep(delay)
    
    # Summary
    log("\n" + "=" * 60)
    log("CYCLE SUMMARY")
    log("=" * 60)
    log(f"Total wallets: {len(wallets)}")
    log(f"✅ Success: {total_success}")
    log(f"❌ Failed/Skipped: {total_failed}")
    log(f"⏭️ Already done: {processed - total_success - total_failed}")
    log("=" * 60)
    
    return total_success + total_failed > 0

def main():
    parser = argparse.ArgumentParser(description="ARC Testnet Daily Bot")
    parser.add_argument("--loop", action="store_true", help="Run in loop mode with 24h cooldown")
    parser.add_argument("--reset", action="store_true", help="Reset progress")
    args = parser.parse_args()
    
    if args.reset:
        save_progress({})
        log("📋 Progress reset!")
        return
    
    if args.loop:
        log("🚀 ARC Daily Bot Started - Loop Mode")
        log("Press Ctrl+C to stop")
        
        while True:
            try:
                had_activity = run_daily()
                
                if had_activity:
                    log("\n" + "=" * 60)
                    log("✅ All accounts processed! Starting 24h cooldown...")
                    log("=" * 60)
                    
                    save_progress({})
                    log("📋 Progress reset for next cycle")
                    
                    countdown(24 * 60 * 60, "Next cycle")
                else:
                    log("\n⚠️ No wallets with balance found. Waiting 1h before retry...")
                    countdown(3600, "Retry")
                    
            except KeyboardInterrupt:
                log("\n\n🛑 Bot stopped by user")
                break
            except Exception as e:
                log(f"\n❌ Unexpected error: {e}")
                log("Waiting 5 minutes before retry...")
                countdown(300, "Retry after error")
    else:
        # Single run
        run_daily()

if __name__ == "__main__":
    main()
