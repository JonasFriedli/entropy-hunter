# entropy-hunter

Token entropy and bias analyzer with candidate generation — a compact, scriptable analogue to Burp Sequencer.

- Analyze a corpus of tokens (one per line)
- Per-position stats: unique chars, most common char & ratio, Shannon entropy, max entropy
- Flags likely anomalies (`ratio > 0.6` or `entropy < 1.0`)
- Generate **biased candidates** from observed distributions
- Includes demos for **vulnerable**, **secure**, and **subtle** token generators
- A **theory** tool to predict entropy & expected matches for subtle-mode parameters

> Educational use only. Only test systems you have explicit permission to assess.

## Quick start

```bash
git clone https://github.com/<you>/entropy-hunter.git
cd entropy-hunter
python3 -m venv venv && source venv/bin/activate
```

## CLI: `entropy-hunter.py`

### Analyze tokens
```bash
python3 entropy-hunter.py analyze --input sample_tokens.txt
```
You’ll see a table per position and a summary:
- `H_total` — total Shannon entropy (bits)
- `S_eff = 2^H_total` — effective search space
- `P(match per random guess) ≈ 2^{-H_total}`
- `Expected guesses ≈ 2^{H_total-1}`

### Generate candidates from learned biases
```bash
python3 entropy-hunter.py generate --input sample_tokens.txt --num 20000 --output guesses.txt
```

### Predict subtle-mode entropy & expected matches
```bash
python3 entropy-hunter.py theory --subset-k 4 --fav-weight 8.0 --length 24   --sample-size 50000 --guesses 100000
```
This computes theoretical per-position entropy, total entropy, and expected matches for your guess/sample budget using the subtle model (subset size `k`, favored weight `w`).

## Demos

```bash
# vulnerable: obvious weaknesses (fixed parts, small numeric ranges, timestamp bits)
python3 demos/vulnerable_demo.py --mode vulnerable --sample-size 50000 --guesses 20000

# secure: CSPRNG (base64 urlsafe), expect ~0 matches even with many guesses
python3 demos/vulnerable_demo.py --mode secure     --sample-size 50000 --guesses 20000

# subtle: realistic soft biases (no fixed chars), tunable to hit your budget
python3 demos/vulnerable_demo.py --mode subtle     --sample-size 50000 --guesses 100000   --subset-k 4 --fav-weight 8.0 --length 24
```
Tip: Aim for `H_total ≈ log2(guesses * sample_size)` if you want to see a few matches.  
Example: `guesses=100k`, `sample=50k` → target ~`log2(5e9) ≈ 32.2 bits`.

## How this helps

- **Blue team:** Confirm tokens are using CSPRNG, no fixed prefixes/suffixes, no timestamp/counter leakage; quantify entropy.
- **Red team:** From captured tokens, detect positional bias and focus guesses; simulate risk given rate limits/lifetimes.

---

## Mathematical background (in depth)

Let a token be positions \(i=1..L\). With per-position empirical frequencies \(p_i(c)\),
the **Shannon entropy** is
\( H_i = -\sum_c p_i(c)\log_2 p_i(c) \).
Uniform over \(N_i\) symbols gives \(H_i=\log_2 N_i\) bits; bias reduces \(H_i\).

Assuming independence,
\( H_{\text{total}}=\sum_i H_i \),
effective search space
\( S_{\text{eff}}=2^{H_{\text{total}}} \),
hit probability per random guess
\( p=2^{-H_{\text{total}}} \),
and expected guesses
\( \mathbb{E}[\text{guesses}]\approx 2^{H_{\text{total}}-1} \).

### Speedup from anomalies
Dropping entropy from \(H\) to \(H'\) multiplies attacker advantage by \(2^{H-H'}\).
Small per-position losses compound (e.g., 0.25 bit loss across 16 positions → 4 bits total → 16× speedup).

### Subtle model (used by `theory` and the demo)
Each position uses a subset of size \(k\) from the full alphabet; one symbol is **favored** with weight \(w\) and others weight \(1\).
Per-position probabilities: \(p_f = w/(w+k-1)\), \(p_o = 1/(w+k-1)\).
Per-position entropy:
\( H_{\text{pos}} = -p_f\log_2 p_f - (k-1)p_o\log_2 p_o \),
and \( H_{\text{total}} = L \cdot H_{\text{pos}} \).

### Practical constraints
- Rate limiting, token TTL, and anomaly detection can dwarf a purely statistical attack.
- Large samples are needed to measure small biases reliably.
- Use CSPRNG tokens ≥ 128 bits to remain safe even under strong sampling.

## License
MIT
