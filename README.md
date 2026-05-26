# ARC Testnet Daily Bot 🚀

Automated daily interactions on **ARC Testnet** (Circle's stablecoin-native L1 blockchain).

## Features

- ✅ **Multi-wallet** support
- ✅ **Proxy rotation** (unique proxy per wallet)
- ✅ **Progress tracking** (skip already processed wallets)
- ✅ **24h cooldown loop** mode
- ✅ **Random delays** to avoid rate limiting
- ✅ **Multiple actions**: GM, transfers, contract deploy, messages

## Actions Per Wallet

1. **GM Message** - Send "gm" on-chain
2. **Self Transfer** - Create on-chain activity
3. **Deploy Contract** - Deploy minimal contract (50% chance)
4. **Batch Transfers** - 2-4 random self-transfers
5. **On-chain Message** - Send random message

## Setup

### 1. Install dependencies

```bash
pip install web3 eth-account
```

### 2. Create `privkey.txt`

Add your wallet private keys (1 per line):

```
abc123def456789...
0xabc123def456789...
```

### 3. Create `proxy.txt` (optional)

Add your proxies (1 per line):

```
http://user:pass@host:port
http://user2:pass2@host2:port2
```

### 4. Get testnet tokens

Claim USDC from Circle faucet:
https://faucet.circle.com

Select **Arc Testnet** → paste wallet address → claim

## Usage

### Single run
```bash
python3 arcdaily.py
```

### Loop mode (24h cooldown)
```bash
python3 arcdaily.py --loop
```

### Reset progress
```bash
python3 arcdaily.py --reset
```

### Run in background (screen)
```bash
screen -dmS arc python3 arcdaily.py --loop

# Check logs
screen -r arc

# Detach: Ctrl+A, then D
```

### Run in background (nohup)
```bash
nohup python3 arcdaily.py --loop > output.log 2>&1 &
```

## Files

| File | Description |
|------|-------------|
| `arcdaily.py` | Main script |
| `privkey.txt` | Wallet private keys |
| `proxy.txt` | Proxy list (optional) |
| `progress.json` | Progress tracking (auto-generated) |
| `daily.log` | Activity log (auto-generated) |

## ARC Network Info

- **Chain**: ARC Testnet
- **Chain ID**: 5042002
- **RPC**: https://rpc.testnet.arc.network
- **Explorer**: https://testnet.arcscan.app
- **Faucet**: https://faucet.circle.com

## About ARC

ARC is a **stablecoin-native L1 blockchain** built by **Circle** (USDC issuer). 

- Gas fees paid in USDC (predictable, dollar-based)
- Deterministic finality < 1 second
- Native Circle integration (USDC, CCTP, Gateway)
- EVM compatible

**Airdrop potential**: Very high (Circle + Goldman Sachs backing)

## Disclaimer

This script is for educational purposes. Use at your own risk. Always verify transactions on the explorer.

## Links

- [ARC Website](https://arc.io)
- [ARC Docs](https://docs.arc.io)
- [ARC Twitter](https://x.com/arc)
- [Circle Faucet](https://faucet.circle.com)
