#!/usr/bin/env python3
"""safe-buddy — Safe multisig CLI with rich terminal UI. Track transactions, owners, balances."""

import json
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone

# ── Safe Transaction Service ────────────────────────────────
_BASE = "https://api.safe.global/tx-service"
NETWORKS = {
    # Mainnet aliases
    "mainnet":   f"{_BASE}/eth",
    "ethereum":  f"{_BASE}/eth",
    "eth":       f"{_BASE}/eth",
    # L2s
    "base":      f"{_BASE}/base",
    "arbitrum":  f"{_BASE}/arb1",
    "arb":       f"{_BASE}/arb1",
    "arb1":      f"{_BASE}/arb1",
    "optimism":  f"{_BASE}/oeth",
    "op":        f"{_BASE}/oeth",
    "oeth":      f"{_BASE}/oeth",
    "polygon":   f"{_BASE}/pol",
    "matic":     f"{_BASE}/pol",
    "pol":       f"{_BASE}/pol",
    "gnosis":    f"{_BASE}/gno",
    "xdai":      f"{_BASE}/gno",
    "gno":       f"{_BASE}/gno",
    "avalanche": f"{_BASE}/avax",
    "avax":      f"{_BASE}/avax",
    "bsc":       f"{_BASE}/bnb",
    "bnb":       f"{_BASE}/bnb",
    "zksync":    f"{_BASE}/zksync",
    "scroll":    f"{_BASE}/scr",
    "scr":       f"{_BASE}/scr",
    "linea":     f"{_BASE}/linea",
    "berachain": f"{_BASE}/berachain",
    "mantle":    f"{_BASE}/mantle",
    "celo":      f"{_BASE}/celo",
    "aurora":    f"{_BASE}/aurora",
    "zkevm":     f"{_BASE}/zkevm",
    "ink":       f"{_BASE}/ink",
    "sonic":     f"{_BASE}/sonic",
    # Testnets
    "sepolia":   f"{_BASE}/sep",
    "sep":       f"{_BASE}/sep",
}

# ── ANSI Colors ─────────────────────────────────────────────
CYAN    = "\033[38;2;0;212;255m"
DIM_CYN = "\033[38;2;0;140;180m"
PURPLE  = "\033[38;2;160;100;255m"
YELLOW  = "\033[38;2;255;215;0m"
GREEN   = "\033[38;2;0;255;120m"
RED     = "\033[38;2;255;80;80m"
WHITE   = "\033[97m"
BOLD    = "\033[1m"
DIM     = "\033[2m"
RESET   = "\033[0m"

def c(s):  return f"{CYAN}{s}{RESET}"
def dc(s): return f"{DIM_CYN}{s}{RESET}"
def p(s):  return f"{PURPLE}{s}{RESET}"
def y(s):  return f"{YELLOW}{s}{RESET}"
def g(s):  return f"{GREEN}{s}{RESET}"
def r(s):  return f"{RED}{s}{RESET}"
def w(s):  return f"{WHITE}{BOLD}{s}{RESET}"
def dim(s): return f"{DIM}{s}{RESET}"

# ── Box Drawing ─────────────────────────────────────────────
TL = "┌"; TR = "┐"; BL = "└"; BR = "┘"
H = "─"; V = "│"; LT = "├"; RT = "┤"
DTL = "╔"; DTR = "╗"; DBL = "╚"; DBR = "╝"
DH = "═"; DV = "║"

def box_top(width, title=""):
    if title:
        inner = f" {title} "
        line = H * 2 + inner + H * (width - 4 - len(title))
    else:
        line = H * (width - 2)
    return dc(f"  {TL}{line}{TR}")

def box_mid(width):
    return dc(f"  {LT}{H * (width - 2)}{RT}")

def box_bot(width):
    return dc(f"  {BL}{H * (width - 2)}{BR}")

def box_row(label, value, width, val_color=c):
    col1 = 18
    l = f"{label}:".ljust(col1)
    val_str = str(value)
    remaining = width - 4 - col1 - len(val_str)
    return f"  {dc(V)} {dc(l)}{val_color(val_str)}{' ' * max(remaining, 0)} {dc(V)}"

def box_empty(width):
    return f"  {dc(V)}{' ' * (width - 2)}{dc(V)}"

def box_text(text, width, color_fn=c):
    pad = width - 4 - len(text)
    return f"  {dc(V)} {color_fn(text)}{' ' * max(pad, 0)} {dc(V)}"

# ── ASCII Banner ─────────────────────────────────────────────
LOGO = r"""
  ███████╗ █████╗ ███████╗███████╗
  ██╔════╝██╔══██╗██╔════╝██╔════╝
  ███████╗███████║█████╗  █████╗
  ╚════██║██╔══██║██╔══╝  ██╔══╝
  ███████║██║  ██║██║     ███████╗
  ╚══════╝╚═╝  ╚═╝╚═╝     ╚══════╝"""

LOGO2 = r"""
  ██████╗ ██╗   ██╗██████╗ ██████╗ ██╗   ██╗
  ██╔══██╗██║   ██║██╔══██╗██╔══██╗╚██╗ ██╔╝
  ██████╔╝██║   ██║██║  ██║██║  ██║ ╚████╔╝
  ██╔══██╗██║   ██║██║  ██║██║  ██║  ╚██╔╝
  ██████╔╝╚██████╔╝██████╔╝██████╔╝   ██║
  ╚═════╝  ╚═════╝ ╚═════╝ ╚═════╝    ╚═╝"""

def print_header(cmd_text="", network="mainnet"):
    print()
    print(f"  {p('⬡')} {w('safe-buddy')}  {dc('|')}  {dim(network)}")
    print(f"  {c('✓')} {dc('Connected to Safe Transaction Service')}")
    for line in LOGO.strip("\n").split("\n"):
        print(f"{CYAN}{line}{RESET}")
    for line in LOGO2.strip("\n").split("\n"):
        print(f"{PURPLE}{line}{RESET}")
    print(f"  {DIM_CYN}{'Multisig Transaction Explorer':>45}{RESET}")
    if cmd_text:
        print()
        print(f"  {dc('safe>')} {w(cmd_text)}")
    print()

# ── Helpers ──────────────────────────────────────────────────
def fetch(url, silent=False):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "safe-buddy/1.0"})
        with urllib.request.urlopen(req, timeout=20) as res:
            return json.loads(res.read())
    except urllib.error.HTTPError as e:
        if not silent:
            print(f"  {r('✗')} HTTP {e.code}: {e.reason} — {url}")
        return None
    except Exception as e:
        if not silent:
            print(f"  {r('✗')} Request failed: {e}")
        return None

def api(base_url, path, params=None):
    url = f"{base_url}/api/v1{path}"
    if params:
        qs = "&".join(f"{k}={v}" for k, v in params.items())
        url += "?" + qs
    return fetch(url)

def parse_args(args):
    """Parse --network / -n flag from args. Returns (filtered_args, network, base_url)."""
    network = "mainnet"
    filtered = []
    i = 0
    while i < len(args):
        if args[i] in ("--network", "-n") and i + 1 < len(args):
            network = args[i + 1].lower()
            i += 2
        else:
            filtered.append(args[i])
            i += 1
    base_url = NETWORKS.get(network)
    if not base_url:
        print(f"  {r('✗')} Unknown network '{network}'. Run 'safe_buddy.py networks' to see options.")
        sys.exit(1)
    return filtered, network, base_url

def fmt_addr(addr, short=True):
    if not addr:
        return "—"
    if short:
        return f"{addr[:6]}...{addr[-4:]}"
    return addr

def fmt_eth(wei_str):
    try:
        wei = int(wei_str)
        eth = wei / 1e18
        if eth == 0:
            return "0 ETH"
        elif eth < 0.0001:
            return f"{eth:.8f} ETH"
        elif eth < 1:
            return f"{eth:.6f} ETH"
        else:
            return f"{eth:.4f} ETH"
    except Exception:
        return str(wei_str)

def fmt_time(ts):
    if not ts:
        return "—"
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        diff = now - dt
        seconds = int(diff.total_seconds())
        if seconds < 60:
            return f"{seconds}s ago"
        elif seconds < 3600:
            return f"{seconds // 60}m ago"
        elif seconds < 86400:
            return f"{seconds // 3600}h ago"
        else:
            return f"{seconds // 86400}d ago"
    except Exception:
        return ts[:10]

def fmt_usd(val):
    if val is None:
        return "—"
    val = float(val)
    if val >= 1_000_000:
        return f"${val / 1_000_000:,.2f}M"
    elif val >= 1_000:
        return f"${val:,.0f}"
    else:
        return f"${val:,.2f}"

def sig_bar(confirmations, threshold):
    """Visual signature progress bar."""
    n = min(confirmations, threshold)
    filled = "▓" * n
    empty = "░" * (threshold - n)
    return f"{filled}{empty}"

def tx_type_label(tx):
    to = tx.get("to", "")
    value = int(tx.get("value", "0") or "0")
    data = tx.get("data") or ""

    if data and data != "0x" and len(data) > 10:
        method = data[:10]
        known = {
            "0xa9059cbb": "ERC20 transfer",
            "0x23b872dd": "ERC20 transferFrom",
            "0x095ea7b3": "ERC20 approve",
            "0x6ea056a9": "Sweep",
            "0x4f48eedf": "Deploy",
            "0xd0e30db0": "Wrap ETH",
        }
        return known.get(method, f"Contract call ({method})")
    elif value > 0:
        return "ETH transfer"
    elif not data or data == "0x":
        return "Contract interaction"
    return "Unknown"

# ── Commands ─────────────────────────────────────────────────

def cmd_safe(args):
    """Show Safe overview: owners, threshold, nonce, balances."""
    args, network, base_url = parse_args(args)

    if not args:
        print(f"  {y('Usage:')} safe_buddy.py safe <address> [--network <net>]")
        print(f"  {dim('Example: safe_buddy.py safe 0xABC...123 --network base')}")
        return

    addr = args[0]
    print_header(f"safe {fmt_addr(addr, short=False)}", network)

    safe_data = api(base_url, f"/safes/{addr}/")
    if not safe_data:
        return

    balances = api(base_url, f"/safes/{addr}/balances/usd/") or []

    owners = safe_data.get("owners", [])
    threshold = safe_data.get("threshold", "?")
    nonce = safe_data.get("nonce", "?")
    version = safe_data.get("version", "?")
    master_copy = safe_data.get("masterCopy", "")
    fallback_handler = safe_data.get("fallbackHandler", "")

    # Compute USD total
    total_usd = 0.0
    token_balances = []
    for b in balances:
        usd = b.get("fiatBalance") or "0"
        try:
            total_usd += float(usd)
        except Exception:
            pass
        token = b.get("tokenAddress")
        symbol = "ETH" if not token else (b.get("token", {}) or {}).get("symbol", "?")
        bal = b.get("balance", "0")
        token_balances.append((symbol, bal, float(usd or 0), token))

    token_balances.sort(key=lambda x: x[2], reverse=True)

    W = 56

    # Header box
    print(box_top(W, "Safe Info"))
    print(box_empty(W))
    print(box_row("Address", fmt_addr(addr), W, val_color=p))
    print(box_row("Network", network.title(), W, val_color=c))
    print(box_row("Version", f"Safe v{version}", W))
    print(box_row("Nonce", str(nonce), W, val_color=y))
    print(box_row("Threshold", f"{threshold} of {len(owners)}", W, val_color=y))
    print(box_empty(W))
    print(box_mid(W))

    # Owners
    print(box_empty(W))
    print(box_text("OWNERS", W, color_fn=p))
    print(box_empty(W))
    for i, owner in enumerate(owners, 1):
        branch = "└" if i == len(owners) else "├"
        line = f"{branch}─ [{i}] {fmt_addr(owner)}"
        pad = W - 4 - len(line)
        print(f"  {dc(V)} {c(line)}{' ' * max(pad, 0)} {dc(V)}")

    print(box_empty(W))
    print(box_mid(W))

    # Balances
    print(box_empty(W))
    print(box_text("BALANCES", W, color_fn=p))
    print(box_empty(W))
    print(box_row("Total USD", fmt_usd(total_usd), W, val_color=w))
    print(box_empty(W))

    for symbol, bal, usd, _ in token_balances[:8]:
        if symbol == "ETH":
            display = fmt_eth(bal)
        else:
            try:
                display = f"{int(bal) / 1e18:,.4f} {symbol}"
            except Exception:
                display = f"{bal} {symbol}"
        usd_str = fmt_usd(usd) if usd > 0 else ""
        label = symbol[:12]
        val = f"{display}  {dim(usd_str)}" if usd_str else display
        # strip ANSI for length calc
        plain_val = f"{display}  {usd_str}" if usd_str else display
        pad = W - 4 - len(label) - 2 - len(plain_val)
        print(f"  {dc(V)} {dc(label + ':')}  {c(display)}  {dim(usd_str)}{' ' * max(pad, 0)} {dc(V)}")

    if len(token_balances) > 8:
        print(box_text(f"+ {len(token_balances) - 8} more tokens", W, color_fn=dim))

    print(box_empty(W))
    print(box_bot(W))
    print()
    print(f"  {dim('MasterCopy:  ' + fmt_addr(master_copy, short=False))}")
    print(f"  {dim('Fallback:    ' + fmt_addr(fallback_handler, short=False))}")
    print()


def cmd_txs(args):
    """List recent transactions."""
    args, network, base_url = parse_args(args)

    if not args:
        print(f"  {y('Usage:')} safe_buddy.py txs <address> [limit] [--network <net>]")
        print(f"  {dim('Example: safe_buddy.py txs 0xABC...123 20 --network base')}")
        return

    addr = args[0]
    limit = int(args[1]) if len(args) > 1 else 15
    print_header(f"txs {fmt_addr(addr)}", network)

    data = api(base_url, f"/safes/{addr}/multisig-transactions/", {
        "executed": "true",
        "limit": limit,
        "ordering": "-nonce",
    })
    if not data:
        return

    results = data.get("results", [])
    count = data.get("count", 0)

    print(f"  {c('✓')} {w(str(count))} {dc('total executed transactions')}")
    print(f"  {dc('Showing last')} {w(str(len(results)))}")
    print()

    hdr = f"  {dc('#'):<8} {dc('Nonce'):<8} {dc('Type'):<28} {dc('To'):<16} {dc('Value'):<14} {dc('Age')}"
    print(hdr)
    print(f"  {DIM_CYN}{'─' * 88}{RESET}")

    for tx in results:
        nonce = str(tx.get("nonce", "?"))
        to = fmt_addr(tx.get("to", ""))
        value = fmt_eth(tx.get("value", "0"))
        age = fmt_time(tx.get("executionDate"))
        tx_hash = tx.get("transactionHash", "")
        safe_hash = tx.get("safeTxHash", "")[:8]
        kind = tx_type_label(tx)

        value_color = y if int(tx.get("value", "0") or 0) > 0 else dc

        print(f"  {p(safe_hash):<16} {dc(nonce):<10} {c(kind[:24]):<32} {dc(to):<24} {value_color(value):<22} {dim(age)}")

    print()


def cmd_pending(args):
    """Show pending transactions waiting for signatures."""
    args, network, base_url = parse_args(args)

    if not args:
        print(f"  {y('Usage:')} safe_buddy.py pending <address> [--network <net>]")
        print(f"  {dim('Example: safe_buddy.py pending 0xABC...123 --network arbitrum')}")
        return

    addr = args[0]
    print_header(f"pending {fmt_addr(addr)}", network)

    # Get safe info for threshold
    safe_data = api(base_url, f"/safes/{addr}/") or {}
    threshold = safe_data.get("threshold", 1)

    data = api(base_url, f"/safes/{addr}/multisig-transactions/", {
        "executed": "false",
        "ordering": "-nonce",
    })
    if not data:
        return

    results = data.get("results", [])

    if not results:
        print(f"  {g('✓')} No pending transactions — safe is clear")
        print()
        return

    print(f"  {y('⚠')} {w(str(len(results)))} {dc('pending transaction(s)')} {dc(f'— threshold: {threshold}')}")
    print()

    for tx in results:
        nonce = tx.get("nonce", "?")
        to = tx.get("to", "?")
        value = tx.get("value", "0")
        data_hex = tx.get("data") or "0x"
        safe_hash = tx.get("safeTxHash", "?")
        created = tx.get("submissionDate")
        kind = tx_type_label(tx)

        confirmations = tx.get("confirmations") or []
        n_confirmed = len(confirmations)
        n_needed = max(threshold - n_confirmed, 0)

        bar = sig_bar(n_confirmed, threshold)
        bar_color = g if n_confirmed >= threshold else y

        W = 60

        print(box_top(W, f"Nonce #{nonce}"))
        print(box_empty(W))
        print(box_row("Type", kind, W, val_color=c))
        print(box_row("To", fmt_addr(to), W, val_color=p))
        print(box_row("Value", fmt_eth(value), W, val_color=y if int(value or 0) > 0 else dc))
        print(box_row("Submitted", fmt_time(created), W, val_color=dim))
        print(box_empty(W))
        print(box_mid(W))
        print(box_empty(W))

        # Signature status
        sig_label = f"Signatures  {bar}  {n_confirmed}/{threshold}"
        sig_c = g if n_confirmed >= threshold else y
        pad = W - 4 - len(sig_label)
        print(f"  {dc(V)} {sig_c(sig_label)}{' ' * max(pad, 0)} {dc(V)}")

        if confirmations:
            print(box_empty(W))
            for conf in confirmations:
                signer = fmt_addr(conf.get("owner", "?"))
                when = fmt_time(conf.get("submissionDate"))
                line = f"  ✔ {signer}  {dim(when)}"
                pad = W - 4 - len(f"  ✔ {signer}  {when}")
                print(f"  {dc(V)} {g(line)}{' ' * max(pad, 0)} {dc(V)}")

        if n_needed > 0:
            print(box_empty(W))
            line = f"  Needs {n_needed} more signature{'s' if n_needed > 1 else ''}"
            pad = W - 4 - len(line)
            print(f"  {dc(V)} {r(line)}{' ' * max(pad, 0)} {dc(V)}")

        print(box_empty(W))
        print(box_bot(W))
        print()
        print(f"  {dim('safeTxHash: ' + safe_hash)}")
        print(f"  {dim('data: ' + (data_hex[:64] + '...' if len(data_hex) > 64 else data_hex))}")
        print()


def cmd_watch(args):
    """Watch a Safe for new pending transactions (live poll)."""
    args, network, base_url = parse_args(args)

    interval = 15
    filtered = []
    for arg in args:
        try:
            interval = int(arg)
        except ValueError:
            filtered.append(arg)
    args = filtered

    if not args:
        print(f"  {y('Usage:')} safe_buddy.py watch <address> [interval_secs] [--network <net>]")
        print(f"  {dim('Example: safe_buddy.py watch 0xABC...123 30 --network base')}")
        return

    addr = args[0]
    print_header(f"watch {fmt_addr(addr)}", network)
    print(f"  {c('◉')} {w('Live watch mode')} — polling every {interval}s")
    print(f"  {dc('Ctrl+C to stop')}")
    print()

    seen_hashes = set()
    first = True

    try:
        while True:
            data = api(base_url, f"/safes/{addr}/multisig-transactions/", {
                "executed": "false",
                "ordering": "-nonce",
            })
            if data:
                results = data.get("results", [])
                new_txs = [tx for tx in results if tx.get("safeTxHash") not in seen_hashes]

                if first:
                    print(f"  {dim(datetime.now().strftime('%H:%M:%S'))} {c('●')} {w(str(len(results)))} pending tx(s) on startup")
                    for tx in results:
                        seen_hashes.add(tx.get("safeTxHash"))
                    first = False
                else:
                    ts = datetime.now().strftime("%H:%M:%S")
                    if new_txs:
                        for tx in new_txs:
                            safe_hash = tx.get("safeTxHash", "?")[:12]
                            kind = tx_type_label(tx)
                            nonce = tx.get("nonce", "?")
                            print(f"  {dim(ts)} {y('▲')} New tx nonce #{nonce}  {c(kind)}  {p(safe_hash)}")
                            seen_hashes.add(tx.get("safeTxHash"))
                    else:
                        confs_changed = False
                        for tx in results:
                            h = tx.get("safeTxHash")
                            confs = len(tx.get("confirmations") or [])
                            key = f"{h}:{confs}"
                            if key not in seen_hashes:
                                if h in seen_hashes:
                                    nonce = tx.get("nonce", "?")
                                    print(f"  {dim(ts)} {g('✔')} Signature added on nonce #{nonce}  ({confs} signed)")
                                seen_hashes.add(key)

                        if not confs_changed:
                            print(f"  {dim(ts)} {dc('·')} {dim('no changes')}", end="\r")

            time.sleep(interval)

    except KeyboardInterrupt:
        print(f"\n\n  {c('◎')} Watch stopped")
        print()


def cmd_owners(args):
    """List all owners of a Safe."""
    args, network, base_url = parse_args(args)

    if not args:
        print(f"  {y('Usage:')} safe_buddy.py owners <address> [--network <net>]")
        return

    addr = args[0]
    print_header(f"owners {fmt_addr(addr)}", network)

    safe_data = api(base_url, f"/safes/{addr}/")
    if not safe_data:
        return

    owners = safe_data.get("owners", [])
    threshold = safe_data.get("threshold", "?")
    nonce = safe_data.get("nonce", 0)

    print(f"  {c('✓')} {w(str(len(owners)))} {dc('owners')}  {dc('·')}  {y(str(threshold))}{dc('-of-')}{y(str(len(owners)))} {dc('threshold')}")
    print(f"  {dc('Nonce:')} {w(str(nonce))}")
    print()

    W = 52
    print(box_top(W, "Signers"))
    print(box_empty(W))
    for i, owner in enumerate(owners, 1):
        branch = "└" if i == len(owners) else "├"
        line = f"{branch}─ {i:02d}  {owner}"
        pad = W - 4 - len(line)
        print(f"  {dc(V)} {c(line)}{' ' * max(pad, 0)} {dc(V)}")
    print(box_empty(W))
    print(box_bot(W))
    print()


def cmd_history(args):
    """Full transaction history including module and ETH transfers."""
    args, network, base_url = parse_args(args)
    limit = 20
    filtered = []
    for arg in args:
        try:
            limit = int(arg)
        except ValueError:
            filtered.append(arg)
    args = filtered

    if not args:
        print(f"  {y('Usage:')} safe_buddy.py history <address> [limit] [--network <net>]")
        return

    addr = args[0]
    print_header(f"history {fmt_addr(addr)}", network)

    data = api(base_url, f"/safes/{addr}/all-transactions/", {"limit": limit})
    if not data:
        return

    results = data.get("results", [])
    total = data.get("count", 0)

    print(f"  {c('✓')} {w(str(total))} {dc('total transactions')}")
    print()

    hdr = f"  {dc('Type'):<20} {dc('From/To'):<16} {dc('Value'):<14} {dc('Age'):<14} {dc('Status')}"
    print(hdr)
    print(f"  {DIM_CYN}{'─' * 78}{RESET}")

    for tx in results:
        tx_type = tx.get("txType", "MULTISIG")
        is_success = tx.get("isSuccessful", None)
        executed = tx.get("executionDate") or tx.get("blockTimestamp")
        age = fmt_time(executed)
        value = tx.get("value") or "0"
        eth_val = fmt_eth(value)
        to = fmt_addr(tx.get("to") or tx.get("safe") or "")

        if tx_type == "MULTISIG_TRANSACTION":
            label = tx_type_label(tx)
            kind_str = f"Multisig"
        elif tx_type == "MODULE_TRANSACTION":
            kind_str = "Module"
            label = "Module exec"
        elif tx_type == "ETHEREUM_TRANSACTION":
            kind_str = "ETH Transfer"
            label = "Incoming ETH"
        else:
            kind_str = tx_type[:16]
            label = ""

        status = g("Executed") if is_success else (r("Failed") if is_success is False else y("Pending"))

        print(f"  {c(kind_str):<28} {dc(to):<24} {y(eth_val):<22} {dim(age):<22} {status}")

    print()


def cmd_networks(args):
    """List supported networks."""
    print_header("networks")

    seen = set()
    W = 52
    print(box_top(W, "Supported Networks"))
    print(box_empty(W))

    for slug, url in NETWORKS.items():
        if url in seen:
            continue
        seen.add(url)
        aliases = [k for k, v in NETWORKS.items() if v == url and k != slug]
        alias_str = f"  ({', '.join(aliases)})" if aliases else ""
        line = f"{slug}{alias_str}"
        host = url.replace("https://safe-transaction-", "").replace(".safe.global", "")
        pad = W - 4 - len(line) - len(host)
        print(f"  {dc(V)} {c(line)}{' ' * max(pad, 0)}{dim(host)} {dc(V)}")

    print(box_empty(W))
    print(box_bot(W))
    print()


# ── CLI Entry ─────────────────────────────────────────────────

COMMANDS = {
    "safe":     (cmd_safe,     "Safe overview — owners, threshold, nonce, balances"),
    "txs":      (cmd_txs,      "Recent executed transactions <address> [limit]"),
    "pending":  (cmd_pending,  "Pending transactions awaiting signatures <address>"),
    "watch":    (cmd_watch,    "Live watch for new transactions <address> [interval]"),
    "owners":   (cmd_owners,   "List all signers <address>"),
    "history":  (cmd_history,  "Full tx history (multisig + ETH + module) <address>"),
    "networks": (cmd_networks, "List supported networks"),
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print_header()
        print(f"  {w('Usage:')} safe_buddy.py <command> [args]")
        print()
        for name, (_, desc) in COMMANDS.items():
            print(f"    {c(name):<20} {dc(desc)}")
        print()
        print(f"  {dim('All commands accept --network / -n <net> (default: mainnet)')}")
        print(f"  {dim('Example: safe_buddy.py safe 0xABC...123 --network base')}")
        print()
        sys.exit(1)

    cmd = sys.argv[1]
    fn, _ = COMMANDS[cmd]
    fn(sys.argv[2:])


if __name__ == "__main__":
    main()
