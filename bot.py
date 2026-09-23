import hashlib

def _validate_hex(value: str, length: int, name: str) -> str:
    """Kiểm tra chuỗi hex hợp lệ và đúng độ dài."""
    value = value.strip().lower()
    if len(value) != length:
        raise ValueError(f"{name} phải đúng {length} ký tự (bạn nhập {len(value)}).")
    if any(c not in "0123456789abcdef" for c in value):
        raise ValueError(f"{name} chỉ được chứa ký tự hex (0-9, a-f).")
    return value

def advanced_algorithm(md5_input: str, hash_input: str) -> dict:
    """
    Thuật toán nâng cao kết hợp MD5 (32) và Hash (64):
    1. Validate đầu vào.
    2. Nhân đôi MD5 -> 64 ký tự.
    3. XOR(md5_x2, hash) -> lớp 1.
    4. SHA256(md5 + hash) -> salt.
    5. XOR(salt, hash) -> lớp 2.
    6. SHA512(xor1 + xor2) -> 128 ký tự.
    7. Lấy 64 ký tự đầu làm kết quả chính.
    8. Tạo signature 8 ký tự từ MD5(kết quả).
    """
    md5 = _validate_hex(md5_input, 32, "MD5")
    h64 = _validate_hex(hash_input, 64, "Hash")

    # Bước 1: Nhân đôi MD5
    md5_x2 = md5 + md5

    # Bước 2: XOR md5_x2 với hash
    xor1 = "".join(format(int(a, 16) ^ int(b, 16), "x") for a, b in zip(md5_x2, h64))

    # Bước 3: Tạo salt từ SHA256
    sha256_salt = hashlib.sha256((md5 + h64).encode()).hexdigest()

    # Bước 4: XOR salt với hash
    xor2 = "".join(format(int(a, 16) ^ int(b, 16), "x") for a, b in zip(sha256_salt, h64))

    # Bước 5: Băm SHA512
    sha512_full = hashlib.sha512((xor1 + xor2).encode()).hexdigest()

    # Bước 6: Lấy kết quả
    result = sha512_full[:64]
    signature = hashlib.md5(result.encode()).hexdigest()[:8]

    return {
        "md5": md5,
        "hash": h64,
        "xor1": xor1,
        "xor2": xor2,
        "sha512_full": sha512_full,
        "result": result,
        "signature": signature,
    }
