import hashlib


def _hex_to_int_list(hex_str: str) -> list[int]:
    """Chuyển chuỗi hex thành list số nguyên 0-15."""
    return [int(c, 16) for c in hex_str]


def predict_tai_xiu(md5: str, hash64: str, result_hash: str) -> dict:
    """
    Thuật toán dự đoán Tài/Xỉu nâng cao gồm 6 tầng:

    Tầng 1: Phân tích tần suất hex (frequency analysis)
    Tầng 2: Trọng số vị trí (positional weighting)
    Tầng 3: Hash chain (md5 -> hash -> result)
    Tầng 4: Entropy check (độ ngẫu nhiên)
    Tầng 5: Rolling XOR checksum
    Tầng 6: Tổng hợp trọng số có hệ số tin cậy

    Trả về:
      - prediction: "TÀI" hoặc "XỈU"
      - confidence: % độ tin cậy (0-100)
      - score: điểm 0-100 (>=50 = TÀI, <50 = XỈU)
      - breakdown: chi tiết từng tầng
    """

    # ============ TẦNG 1: Phân tích tần suất ============
    combined = md5 + hash64 + result_hash
    digits = _hex_to_int_list(combined)

    # Đếm số hex >= 8 (nửa cao) và < 8 (nửa thấp)
    high_count = sum(1 for d in digits if d >= 8)
    low_count = len(digits) - high_count
    freq_score = (high_count / len(digits)) * 100  # 0-100

    # ============ TẦNG 2: Trọng số vị trí ============
    # Vị trí càng về sau càng quan trọng (vì là kết quả mới nhất)
    weighted_sum = 0
    weight_total = 0
    for i, d in enumerate(digits):
        w = (i + 1) / len(digits)
        weighted_sum += d * w
        weight_total += 15 * w
    pos_score = (weighted_sum / weight_total) * 100

    # ============ TẦNG 3: Hash chain ============
    chain = hashlib.sha256((md5 + hash64).encode()).hexdigest()
    chain2 = hashlib.sha256((chain + result_hash).encode()).hexdigest()
    chain_digits = _hex_to_int_list(chain2[:32])
    chain_score = (sum(chain_digits) / (len(chain_digits) * 15)) * 100

    # ============ TẦNG 4: Entropy ============
    # Tính Shannon entropy
    freq_map = {}
    for d in digits:
        freq_map[d] = freq_map.get(d, 0) + 1
    total = len(digits)
    entropy = 0.0
    for count in freq_map.values():
        p = count / total
        entropy -= p * (p and __import__("math").log2(p))
    # entropy max = log2(16) = 4
    entropy_score = (entropy / 4.0) * 100

    # ============ TẦNG 5: Rolling XOR ============
    xor_acc = 0
    for d in digits:
        xor_acc ^= d
    # xor_acc trong 0-15, chuẩn hoá 0-100
    xor_score = (xor_acc / 15) * 100

    # ============ TẦNG 6: Tổng hợp có trọng số ============
    # Trọng số từng tầng (tổng = 1.0)
    weights = {
        "freq": 0.25,     # Tần suất — quan trọng nhất
        "pos": 0.15,      # Vị trí
        "chain": 0.25,    # Hash chain — quan trọng
        "entropy": 0.15,  # Entropy
        "xor": 0.20,      # XOR checksum
    }

    final_score = (
        freq_score * weights["freq"]
        + pos_score * weights["pos"]
        + chain_score * weights["chain"]
        + entropy_score * weights["entropy"]
        + xor_score * weights["xor"]
    )

    # ============ QUYẾT ĐỊNH ============
    prediction = "TÀI" if final_score >= 50 else "XỈU"

    # Độ tin cậy = khoảng cách tới 50 * 2 (0-100%)
    confidence = abs(final_score - 50) * 2
    confidence = min(confidence + 20, 99.0)  # Cộng base 20% tối thiểu, max 99%

    # Nếu score gần 50 → độ tin cậy thấp
    if 45 <= final_score <= 55:
        confidence = max(35.0, confidence - 25)

    return {
        "prediction": prediction,
        "confidence": round(confidence, 2),
        "score": round(final_score, 2),
        "breakdown": {
            "freq": round(freq_score, 2),
            "pos": round(pos_score, 2),
            "chain": round(chain_score, 2),
            "entropy": round(entropy_score, 2),
            "xor": round(xor_score, 2),
        },
    }
