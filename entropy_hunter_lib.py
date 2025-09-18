#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import math
import random
from collections import Counter

# -------------------- core math --------------------

def shannon_entropy(freqs, total):
    e = 0.0
    for f in freqs:
        if f == 0:
            continue
        p = f / total
        e -= p * math.log2(p)
    return e

def analyze_tokens(tokens):
    """Return per-position stats for a list of equal-length tokens."""
    if not tokens:
        return []
    length = max(len(t) for t in tokens)
    tokens = [t.ljust(length, '\x00')[:length] for t in tokens]
    out = []
    total = len(tokens)
    for i in range(length):
        bucket = Counter(t[i] for t in tokens)
        uniq = len(bucket)
        (mc, mc_count) = bucket.most_common(1)[0]
        ratio = mc_count / total
        ent = shannon_entropy(list(bucket.values()), total)
        max_ent = math.log2(uniq) if uniq > 0 else 0.0
        anomaly = (ratio > 0.6) or (ent < 1.0)
        out.append({
            "pos": i,
            "unique": uniq,
            "most_char": mc,
            "most_count": mc_count,
            "ratio": ratio,
            "entropy": ent,
            "max_entropy": max_ent,
            "anomaly": anomaly,
            "bucket": bucket
        })
    return out

def print_analysis(stats, print_summary=True):
    header = f'{"Position":>8}{"Unique":>8}{"MaxChar":>8}{"MaxFreq":>9}{"Ratio":>8}{"Entropy":>9}{"MaxEnt":>8}{"Anomaly":>9}'
    print(header)
    for s in stats:
        mc = s["most_char"]
        mc_disp = mc if mc != "\x00" else "\\u0000"
        flag = "*" if s["anomaly"] else ""
        print(f'{s["pos"]:8d}{s["unique"]:8d}{mc_disp:8s}{s["most_count"]:9d}{s["ratio"]:8.4f}{s["entropy"]:9.4f}{s["max_entropy"]:8.4f}{flag:9s}')
    if print_summary:
        H_total = sum(s["entropy"] for s in stats)
        print("\n--- Summary ---")
        print(f"Total entropy H_total  = {H_total:.4f} bits")
        print(f"Effective space S_eff  = 2^{H_total:.4f}")
        print(f"P(match per random guess) ≈ 2^{-H_total:.4f}")
        print(f"Expected guesses (avg) ≈ 2^{H_total-1:.4f}")

def generate_candidates(tokens, num=1000, seed=None):
    if seed is not None:
        random.seed(seed)
    length = max(len(t) for t in tokens)
    tokens = [t.ljust(length, '\x00')[:length] for t in tokens]
    stats = analyze_tokens(tokens)
    pos_choices = []
    for s in stats:
        bucket = s["bucket"]
        total = sum(bucket.values())
        items = []
        weights = []
        for ch, cnt in bucket.items():
            items.append(ch)
            weights.append(cnt/total)
        pos_choices.append((items, weights))
    out = []
    for _ in range(num):
        chars = []
        for items, weights in pos_choices:
            r = random.random()
            cum = 0.0
            pick = items[-1]
            for ch, w in zip(items, weights):
                cum += w
                if r <= cum:
                    pick = ch
                    break
            chars.append(pick)
        out.append(''.join(chars))
    return out

# -------------------- subtle-mode theory helpers --------------------

def subtle_per_position_entropy(subset_k, fav_weight):
    """Entropy of a position with k-symbol subset and one favored symbol with given weight."""
    pf = fav_weight / (fav_weight + (subset_k - 1))
    po = 1.0 / (fav_weight + (subset_k - 1))
    H = - (pf * math.log2(pf) + (subset_k - 1) * po * math.log2(po))
    return H

def subtle_predict_bits(subset_k, fav_weight, length):
    Hpos = subtle_per_position_entropy(subset_k, fav_weight)
    Htotal = Hpos * length
    return Hpos, Htotal

def expected_matches(Htotal, sample_size, guesses):
    return (guesses * sample_size) / (2 ** Htotal)
