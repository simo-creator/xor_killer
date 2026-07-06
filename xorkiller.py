import argparse
import sys


exact_len = -1
parser = argparse.ArgumentParser(description="XORKILLER tool by X_9 - DECRYPT THE PLANET (>.<)")



# Data Inputs
parser.add_argument("--hex", nargs="+", help="Hex values")
parser.add_argument("--multihex", nargs="+", help="Ghidra style (0xVALUE/LEN)")
parser.add_argument("--key", nargs="+", help="XOR Key in hex")


# Operations
parser.add_argument("--ror", type=int, help="Rotate Right value")
parser.add_argument("--rol", type=int, help="Rotate Left value")
parser.add_argument("--sub", help="Subtract value (type 'index' for dynamic i subtraction)")
parser.add_argument("--add", help="Add value (type 'index' for dynamic i addition)")


args = parser.parse_args()



def rol(b, n): return ((b << n) | (b >> (8 - n))) & 0xFF
def ror(b, n): return ((b >> n) | (b << (8 - n))) & 0xFF

def parse_multihex(tokens, endian="little"):
    global exact_len
    chunks = []
    print(f"[*] Parsing {len(tokens)} multihex tokens...")
    answer0 = input("Do you know the exact total length of the bytes?(y/n): ")
    if answer0.lower().startswith("y"):
        exact_len = int(input("Enter it: "))
    for t in tokens:
        if "/" not in t:
            print(f"[!] Warning: Skipping invalid token {t}")
            continue
        v_str, l_str = t.split("/", 1)
        v = int(v_str, 16)
        ln = int(l_str)
        chunks.append(v.to_bytes(ln, endian))
    return b"".join(chunks)

# 1-Load Data
if args.multihex:
    enc = parse_multihex(args.multihex, endian="little")
    if exact_len != -1: 
        enc = enc[:exact_len]
elif args.hex:
    try:
        enc = bytes([int(x, 16) for x in args.hex])
    except ValueError:
        raise SystemExit("Error: Invalid hex in --hex")
else:
    raise SystemExit("Error: Give --hex OR --multihex")

print(f"[*] Encrypted Buffer: {enc.hex()}")

# 2-Key Setup
if args.key:
    try:
        key_bytes = bytes([int(x, 16) for x in args.key])
    except ValueError:
        raise SystemExit("Error: Invalid hex in --key")
else:
    answer1 = input("Do you have the key?(y/n): ")
    if answer1.lower().startswith("y"):
        key_input = str(input("Enter key (hex bytes): ")).split()
        key_bytes = bytes([int(x, 16) for x in key_input])
    else:
        known = input("Type known beginning: ").encode()
        key_bytes = bytes(b ^ l for b, l in zip(enc, known))
        print(f"[*] Deduced Key: {key_bytes.hex()}")

# 3-Decrypt Order handeling
# this ensures that typing "--sub index --key A7" is different from "--key A7 --sub index"
ops_order = []
for arg in sys.argv:
    if arg == '--key': ops_order.append('xor')
    elif arg == '--ror': ops_order.append('ror')
    elif arg == '--rol': ops_order.append('rol')
    elif arg == '--sub': ops_order.append('sub')
    elif arg == '--add': ops_order.append('add')


if not ops_order:
    if args.key: ops_order.append('xor')
    if args.sub: ops_order.append('sub')
    if args.add: ops_order.append('add')
    if args.ror: ops_order.append('ror')
    if args.rol: ops_order.append('rol')

# 4-Decryption

dec_list = []
for i in range(len(enc)):
    res = enc[i]
    
    for op in ops_order:
        if op == 'xor':

            if 'key_bytes' in locals() and len(key_bytes) > 0:
                k = key_bytes[i % len(key_bytes)]
                res = res ^ k
        elif op == 'ror':
            res = ror(res, args.ror)
        elif op == 'rol':
            res = rol(res, args.rol)
        elif op == 'sub':
            val = i if args.sub == "index" else int(args.sub)
            res = (res - val) % 256
        elif op == 'add':
            val = i if args.add == "index" else int(args.add)
            res = (res + val) % 256
            
    dec_list.append(res)

dec = bytes(dec_list)




# 5-Output
print("-" * 30)
print(f"PIPELINE: {' -> '.join(ops_order)}")
print(f"HEX:      {dec.hex()}")
print(f"STRING:   {dec.decode('latin-1', errors='ignore')}")
print("-" * 30)


#THANKS FOR USING MY TOOL :)
