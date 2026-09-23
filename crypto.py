import hashlib

def _validate_hex(value: str, length: int, name: str) -> str:
    value = value.strip().lower()
    if len(value) != length:
        raise ValueError(f"{name} phải đúng {length} ký tự.")
    if any(c not in "0123456789abcdef" for c in value):
        raise ValueError(f"{name} chỉ chứa hex 0-9a-f.")
    return value

def advanced_algorithm(md5_input: str, hash_input: str) -> dict:
    md5 = _validate_hex(md5_input, 32, "MD5")
    h64 = _validate_hex(hash_input, 64, "Hash")

    md5_x2 = md5 + md5
    xor1 = "".join(format(int(a, 16) ^ int(b, 16), "x") for a, b in zip(md5_x2, h64))
    sha256_salt = hashlib.sha256((md5 + h64).encode()).hexdigest()
    xor2 = "".join(format(int(a, 16) ^ int(b, 16), "x") for a, b in zip(sha256_salt, h64))
    sha512_full = hashlib.sha512((xor1 + xor2).encode()).hexdigest()

    result = sha512_full[:64]
    signature = hashlib.md5(result.encode()).hexdigest()[:8]

    return {
        "md5": md5, "hash": h64, "xor1": xor1, "xor2": xor2,
        "sha512_full": sha512_full, "result": result, "signature": signature,
    }
