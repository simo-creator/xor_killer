# XORKILLER

**by X_9**
<img width="1300" height="555" alt="image" src="https://github.com/user-attachments/assets/89c1eff9-fb27-48a0-9f6d-1d105a76063b" />

A command-line tool for reversing simple byte-level obfuscation chains — XOR, ROL, ROR, ADD, and SUB — in whatever order they were originally applied. Built for malware reverse engineering (recovering obfuscated strings/config data) and CTF crackme challenges.

Most "custom encryption" found in malware samples and beginner-to-intermediate crackmes isn't real crypto — it's a small stack of these five operations applied byte-by-byte. XORKILLER lets you replay that stack in the exact order it was applied, with a single-key or known-plaintext XOR, and Ghidra-friendly input, without writing a one-off Python script every time.

---

## Features

- **Chained operations** — combine `xor`, `rol`, `ror`, `add`, `sub` in any order.
- **Order-aware** — the order you type the flags on the command line is the order the operations run in. `--sub index --key A7` decrypts differently than `--key A7 --sub index`, and the tool respects that.
- **Dynamic index-based add/sub** — use `index` instead of a fixed number when the obfuscation adds/subtracts the byte's position (`data[i] - i`, a very common pattern).
- **Ghidra-style input** — paste `0xVALUE/LEN` tokens straight from a Ghidra decompiler view via `--multihex`.
- **Known-plaintext key recovery** — don't have the XOR key? Give a known/guessed plaintext prefix and XORKILLER derives the key from it.
- **Interactive fallback** — if you don't pass a key or exact length via flags, it will prompt you for it.

---

## Requirements

- Python 3.7+
- No third-party dependencies (standard library only)

---

## Installation

```bash
git clone https://github.com/simo-creator/xor_killer.git
cd xor_killer
```

No install step needed — it's a single script.

---

## Basic Usage

```bash
python3 xorkiller.py [--hex ... | --multihex ...] [--key ...] [--ror N] [--rol N] [--sub N|index] [--add N|index]
```

You must supply the encrypted bytes via **either** `--hex` or `--multihex`. Everything else is optional and depends on the obfuscation scheme you're reversing.

---

## Input Formats

### `--hex` — plain hex bytes

Space-separated hex byte values:

```bash
python3 xorkiller.py --hex 5a 3f 12 8b --key aa
```

### `--multihex` — Ghidra-style dumps

For when you've pulled `0xVALUE/LEN` pairs straight out of Ghidra's decompiler (e.g. a `DWORD`/`WORD`/`BYTE` array being built up):

```bash
python3 xorkiller.py --multihex 0x1a2b3c4d/4 0x9f/1 0x00ff/2 --key 13
```

You'll be asked if you know the *exact total byte length* of the buffer — useful when the last chunk includes padding you want to trim off.

---

## Scenario Walkthroughs

### Scenario 1: Simple single-byte XOR

You found `enc = data[i] ^ 0x37` in the disassembly.

```bash
python3 xorkiller.py --hex 6a 5d 12 ff --key 37
```

### Scenario 2: Multi-byte XOR key

The key is a repeating multi-byte sequence, e.g. `"AB12"`:

```bash
python3 xorkiller.py --hex 6a 5d 12 ff 90 --key 41 42 31 32
```

### Scenario 3: You don't have the key, but you know the plaintext starts with something

Common when decrypting strings you can guess (e.g. you expect it starts with `"http"` or `"MZ"`):

```bash
python3 xorkiller.py --hex 6a 5d 12 ff
Do you have the key?(y/n): n
Type known beginning: http
```

XORKILLER XORs the known plaintext against the ciphertext to recover the key, then shows you the deduced key so you can reuse it on the rest of the buffer.

### Scenario 4: XOR + ROL chain (stacked obfuscation)

The malware does `rol(data[i], 3)` **then** XORs with a key — you need to reverse in the opposite order: XOR first, then ROR (inverse of ROL) — just type the flags in the order you want them applied:

```bash
python3 xorkiller.py --hex 6a 5d 12 ff --key 37 --ror 3
```

Flip the order if the original obfuscation was applied the other way:

```bash
python3 xorkiller.py --hex 6a 5d 12 ff --ror 3 --key 37
```

### Scenario 5: Index-based SUB (position-dependent obfuscation)

You see something like `enc[i] = (plain[i] + i) & 0xFF` in the code, meaning decryption needs `data[i] - i`:

```bash
python3 xorkiller.py --hex 6a 5d 12 ff --sub index
```

### Scenario 6: Full multi-stage pipeline

A more elaborate scheme: subtract the index, XOR with a key, then rotate right by 5:

```bash
python3 xorkiller.py --hex 6a 5d 12 ff 90 21 --sub index --key de --ror 5
```

Output shows the pipeline that was run, so you can double check the order matched what you intended:

```
PIPELINE: sub -> xor -> ror
HEX:      48656c6c6f21
STRING:   Hello!
```

### Scenario 7: Ghidra dump with unknown padding

You copy-pasted an array construction from Ghidra and the last value includes extra padding bytes you don't want:

```bash
python3 xorkiller.py --multihex 0x48656c6c6f2100/7 --key 00
Do you know the exact total length of the bytes?(y/n): y
Enter it: 6
```

This trims the result down to the first 6 real bytes before decryption.

---

## How Operation Order Works

XORKILLER inspects `sys.argv` directly (not just the parsed flags) so it can tell the difference between:

```bash
--sub index --key A7      # sub runs first, then xor
--key A7 --sub index      # xor runs first, then sub
```

This matters a lot when reversing multi-stage obfuscation — get the order wrong and you'll get garbage output even with the correct key and operations. If you're not sure of the original order, it's often faster to just try both directions.

---

## Output

Every run prints:

```
[*] Encrypted Buffer: <hex of input>
------------------------------
PIPELINE: <operations in the order they ran>
HEX:      <decrypted bytes as hex>
STRING:   <decrypted bytes as latin-1 text (best-effort)>
------------------------------
```

The `STRING` line uses `errors="ignore"` decoding, so garbage bytes won't crash the tool — if the pipeline/key/order is wrong you'll usually see it immediately as unreadable output, which is your cue to try a different order or operation.

---

## Disclaimer

This tool is intended for legitimate security research, malware analysis, and CTF/educational use on systems and samples you are authorized to analyze. It does not perform any brute-forcing or unauthorized decryption — it only replays known/guessed transformations that you supply.


## Contributing

PRs welcome — especially additional operations (e.g. bit shifts, byte-swap/endian ops) or output formats (e.g. `--out file`, base64 input support).
