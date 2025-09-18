#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EntropyHunter CLI.

Usage:
  python3 entropy-hunter.py analyze  --input tokens.txt
  python3 entropy-hunter.py generate --input tokens.txt --num 20000 --output guesses.txt
  python3 entropy-hunter.py theory   --subset-k 4 --fav-weight 8.0 --length 24                                      --sample-size 50000 --guesses 100000
"""
import argparse

from entropy_hunter_lib import (
    analyze_tokens, print_analysis, generate_candidates,
    subtle_predict_bits, expected_matches
)

def main():
    ap = argparse.ArgumentParser(description="EntropyHunter CLI")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_an = sub.add_parser("analyze", help="Analyze tokens from a file (one per line)")
    p_an.add_argument("--input", "-i", required=True)

    p_gen = sub.add_parser("generate", help="Generate candidates from learned biases")
    p_gen.add_argument("--input", "-i", required=True)
    p_gen.add_argument("--num", "-n", type=int, default=20000)
    p_gen.add_argument("--output", "-o", default=None)

    p_th = sub.add_parser("theory", help="Predict H_total and expected matches for subtle parameters")
    p_th.add_argument("--subset-k", type=int, default=8, help="symbols per position subset (k)")
    p_th.add_argument("--fav-weight", type=float, default=6.0, help="favored symbol weight multiplier")
    p_th.add_argument("--length", type=int, default=24, help="token length (positions)")
    p_th.add_argument("--sample-size", type=int, default=50000, help="size of captured token set")
    p_th.add_argument("--guesses", type=int, default=100000, help="number of attack guesses")

    args = ap.parse_args()

    if args.cmd == "analyze":
        with open(args.input, "r", encoding="utf-8", errors="ignore") as f:
            tokens = [line.rstrip("\n") for line in f if line.strip()]
        stats = analyze_tokens(tokens)
        print_analysis(stats, print_summary=True)

    elif args.cmd == "generate":
        with open(args.input, "r", encoding="utf-8", errors="ignore") as f:
            tokens = [line.rstrip("\n") for line in f if line.strip()]
        guesses = generate_candidates(tokens, num=args.num)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as out:
                out.write("\n".join(guesses) + "\n")
        else:
            for g in guesses[:50]:
                print(g)

    elif args.cmd == "theory":
        Hpos, Htotal = subtle_predict_bits(args.subset_k, args.fav_weight, args.length)
        print(f"Per-position entropy (theory): {Hpos:.6f} bits")
        print(f"Total entropy (theory):        {Htotal:.6f} bits")
        print(f"S_eff = 2^{Htotal:.6f}")
        print(f"P(hit per random guess) ≈ 2^{-Htotal:.6f}")
        em = expected_matches(Htotal, args.sample_size, args.guesses)
        print(f"Expected matches for guesses={args.guesses:,} & sample_size={args.sample_size:,}: {em:.4f}")

if __name__ == "__main__":
    main()
