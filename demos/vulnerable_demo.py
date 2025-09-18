#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dual-mode demo with optional subtle-bias mode for entropy-hunter.
"""
import argparse
import base64
import os
import random
import secrets
import sys
import time

# Import library from repo root
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import entropy_hunter_lib as eh  # noqa: E402

# -------- token generators --------

def vulnerable_generator():
    prefix = "AAAA"
    suffix = "ZZ"
    user = f"{random.randint(0, 99):02d}"
    ts_low = f"{int(time.time()) % 10000:04d}"
    rand4 = f"{random.randint(0, 9999):04d}"
    return prefix + user + ts_low + rand4 + suffix

def vulnerable_generator_variant():
    prefix = "APP"
    ts_low_hex = f"{int(time.time()) & 0xFFF:03x}"
    rand5 = "".join(str(random.randint(0, 9)) for _ in range(5))
    suffix = "XY"
    return (prefix + ts_low_hex + rand5 + suffix).upper()

def secure_generator(n_bytes: int = 16) -> str:
    return base64.urlsafe_b64encode(secrets.token_bytes(n_bytes)).rstrip(b"=").decode()

# -------- subtle mode model (shared across the whole sample) --------

def subtle_model_build(length: int, alphabet: str, subset_k: int, fav_weight: float):
    if not (2 <= subset_k <= len(alphabet)):
        raise ValueError("subset-k must be between 2 and len(alphabet)")
    model = []
    rng = random
    for _ in range(length):
        subset = rng.sample(alphabet, subset_k)
        fav = rng.choice(subset)
        weights = [fav_weight if ch == fav else 1.0 for ch in subset]
        # cumulative weights
        cum = []
        acc = 0.0
        for w in weights:
            acc += w
            cum.append(acc)
        model.append((subset, cum))
    return model

def subtle_sample_from_model(model):
    token_chars = []
    rng = random
    for subset, cum in model:
        r = rng.random() * cum[-1]
        idx = 0
        while idx < len(cum) and r > cum[idx]:
            idx += 1
        if idx >= len(subset):
            idx = len(subset) - 1
        token_chars.append(subset[idx])
    return "".join(token_chars)

def run(mode: str = "vulnerable",
        sample_size: int = 50_000,
        guesses: int = 20_000,
        seed: int | None = None,
        subset_k: int = 8,
        fav_weight: float = 6.0,
        length: int = 24) -> None:
    if seed is not None:
        random.seed(seed)
    else:
        random.seed(None)

    tokens: list[str] = []

    if mode == "subtle":
        Hpos, Htotal = eh.subtle_predict_bits(subset_k, fav_weight, length)
        print(f"[subtle] predicted per-position entropy ≈ {Hpos:.3f} bits")
        print(f"[subtle] predicted total entropy      ≈ {Htotal:.3f} bits\n")
        alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
        subtle_model = subtle_model_build(length, alphabet, subset_k, fav_weight)
    else:
        subtle_model = None

    print(f"Generating {sample_size:,} {mode} tokens...\n")
    for i in range(sample_size):
        if mode == "vulnerable":
            t = vulnerable_generator_variant() if (i % 5) else vulnerable_generator()
        elif mode == "secure":
            t = secure_generator(16)
        else:
            t = subtle_sample_from_model(subtle_model)
        tokens.append(t)

    maxlen = max(len(t) for t in tokens)
    tokens = [t.ljust(maxlen, "\x00")[:maxlen] for t in tokens]

    print("Analysing token sample...\n")
    stats = eh.analyze_tokens(tokens)
    eh.print_analysis(stats)
    print()

    print(f"Generating {guesses:,} candidate tokens based on learned biases...\n")
    candidates = eh.generate_candidates(tokens, num=guesses)
    token_set = set(tokens)
    matches = [c for c in candidates if c in token_set]
    print(f"Number of matches: {len(matches)} out of {guesses}")
    if matches:
        print("Example matches:")
        for m in matches[:10]:
            print(" ", m)
    elif mode == "secure":
        print("No matches found (expected for secure tokens).")

def main() -> None:
    p = argparse.ArgumentParser(description="entropy-hunter demo")
    p.add_argument("--mode", choices=["vulnerable", "secure", "subtle"], default="vulnerable")
    p.add_argument("--sample-size", type=int, default=50_000)
    p.add_argument("--guesses", type=int, default=20_000)
    p.add_argument("--seed", type=int, default=None, help="Optional seed for reproducible runs")
    # subtle controls (mirror CLI 'theory' names)
    p.add_argument("--subset-k", type=int, default=8, help="symbols per position subset (k)")
    p.add_argument("--fav-weight", type=float, default=6.0, help="favored symbol weight multiplier")
    p.add_argument("--length", type=int, default=24, help="token length (positions)")
    a = p.parse_args()
    run(a.mode, a.sample_size, a.guesses, a.seed, a.subset_k, a.fav_weight, a.length)

if __name__ == "__main__":
    main()
