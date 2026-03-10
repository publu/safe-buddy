```
  ███████╗ █████╗ ███████╗███████╗
  ██╔════╝██╔══██╗██╔════╝██╔════╝
  ███████╗███████║█████╗  █████╗
  ╚════██║██╔══██║██╔══╝  ██╔══╝
  ███████║██║  ██║██║     ███████╗
  ╚══════╝╚═╝  ╚═╝╚═╝     ╚══════╝
  ██████╗ ██╗   ██╗██████╗ ██████╗ ██╗   ██╗
  ██╔══██╗██║   ██║██╔══██╗██╔══██╗╚██╗ ██╔╝
  ██████╔╝██║   ██║██║  ██║██║  ██║ ╚████╔╝
  ██╔══██╗██║   ██║██║  ██║██║  ██║  ╚██╔╝
  ██████╔╝╚██████╔╝██████╔╝██████╔╝   ██║
  ╚═════╝  ╚═════╝ ╚═════╝ ╚═════╝    ╚═╝
                        Multisig Transaction Explorer
```

Track Safe multisig wallets across 20+ chains. Pending signatures, signer status, transaction history, live watch mode — rich terminal UI, zero dependencies.

Agent skill for [cryptoskills.sh](https://cryptoskills.sh/skill/safe-buddy).

## Install

```bash
curl -sL https://raw.githubusercontent.com/publu/safe-buddy/master/safe_buddy.py -o /tmp/safe_buddy.py
```

## Commands

```
safe <address>           Safe overview — owners, threshold, nonce, balances
txs <address> [limit]   Recent executed transactions (default 15)
pending <address>        Pending txs waiting for signatures + signer status
watch <address> [secs]  Live poll for new transactions (default 15s interval)
owners <address>         List all signers with full addresses
history <address>        Full tx history — multisig + ETH transfers + module txs
networks                 List all supported networks
```

All commands accept `--network <name>` or `-n <name>` (default: `mainnet`).

## Examples

```bash
# Safe overview with balances and signers
python3 /tmp/safe_buddy.py safe 0x849D52316331967b6fF1198e5E32A0eB168D039d --network base

# See what's waiting to be signed
python3 /tmp/safe_buddy.py pending 0x849D52316331967b6fF1198e5E32A0eB168D039d --network base

# Recent 20 transactions on Arbitrum
python3 /tmp/safe_buddy.py txs 0xYourSafe 20 --network arbitrum

# Watch live for new transactions (poll every 30s)
python3 /tmp/safe_buddy.py watch 0xYourSafe 30 --network mainnet

# Full history including ETH transfers + module calls
python3 /tmp/safe_buddy.py history 0xYourSafe --network optimism

# List all supported networks
python3 /tmp/safe_buddy.py networks
```

## Terminal Output

```
  ⬡ safe-buddy  |  base
  ✓ Connected to Safe Transaction Service

  safe> pending 0x849D52316331967b6fF1198e5E32A0eB168D039d

  ⚠ 2 pending transaction(s) — threshold: 3

  ┌── Nonce #42 ────────────────────────────────────────────────┐
  │                                                              │
  │ Type:             ERC20 transfer                             │
  │ To:               0x1f9e...4a2b                              │
  │ Value:            0 ETH                                      │
  │ Submitted:        2h ago                                     │
  │                                                              │
  ├──────────────────────────────────────────────────────────────┤
  │                                                              │
  │ Signatures  ▓▓░░░  2/3                                       │
  │                                                              │
  │   ✔ 0xAbC4...1234  3m ago                                    │
  │   ✔ 0xDeF7...5678  1h ago                                    │
  │                                                              │
  │   Needs 1 more signature                                     │
  │                                                              │
  └──────────────────────────────────────────────────────────────┘

  ┌── Nonce #43 ────────────────────────────────────────────────┐
  │                                                              │
  │ Type:             Contract call (0xa9059cbb)                 │
  │ To:               0x833D...9fAa                              │
  │ Value:            0.5 ETH                                    │
  │ Submitted:        14m ago                                    │
  │                                                              │
  ├──────────────────────────────────────────────────────────────┤
  │                                                              │
  │ Signatures  ░░░░░  0/3                                       │
  │                                                              │
  │   Needs 3 more signatures                                    │
  │                                                              │
  └──────────────────────────────────────────────────────────────┘
```

## Supported Networks

Ethereum, Base, Arbitrum, Optimism, Polygon, Gnosis Chain, Avalanche, BNB Chain, zkSync, Scroll, Linea, Berachain, Mantle, Celo, Aurora, Polygon zkEVM, Ink, Sonic, Sepolia.

## Data Sources

All data from the [Safe Transaction Service API](https://docs.safe.global/core-api/api-safe-transaction-service) — no API keys required.

- `GET /api/v1/safes/{address}/` — safe metadata
- `GET /api/v1/safes/{address}/multisig-transactions/` — transactions
- `GET /api/v1/safes/{address}/balances/usd/` — token balances with USD
- `GET /api/v1/safes/{address}/all-transactions/` — full history

## Requirements

Python 3.6+ — zero external dependencies.
