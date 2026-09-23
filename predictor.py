import hashlib
import math

def _hex_to_int_list(hex_str: str) -> list:
    return [int(c, 16) for c in hex_str]

def predict_tai_xiu(md5: str, hash64: str, result_hash: str) -> dict:
    combined = md5 + hash64 + result_hash
    digits = _hex_to_int_list(combined)

    # Tầng 1: Tần suất
    high_count = sum(1 for d in digits if d >= 8)
    freq_score = (high_count / len(digits)) * 100

    # Tầng 2: Vị trí
    weighted_sum, weight_total = 0, 0
    for i, d in enumerate(digits):
        w = (i + 1) / len(digits)
        weighted_sum += d * w
        weight_total += 15 * w
    pos_score = (weighted_sum / weight_total) * 100

    # Tầng 3: Hash chain
    chain = hashlib.sha256((md5 + hash64).encode()).hexdigest()
    chain2 = hashlib.sha256((chain + result_hash).encode()).hexdigest()
    chain_digits = _hex_to_int_list(chain2[:32])
    chain_score = (sum(chain_digits) / (len(chain_digits) * 15)) * 100

    # Tầng 4: Entropy
    freq_map = {}
    for d in digits:
        freq_map[d] = freq_map.get(d, 0) + 1
    total = len(digits)
    entropy = 0.0
    for count in freq_map.values():
        p = count / total
        entropy -= p * math.log2(p)
    entropy_score = (entropy / 4.0) * 100

    # Tầng 5: XOR
    xor_acc = 0
    for d in digits:
        xor_acc ^= d
    xor_score = (xor_acc / 15) * 100

    # Tầng 6: Tổng hợp
    weights = {"freq": 0.25, "pos": 0.15, "chain": 0.25, "entropy": 0.15, "xor": 0.20}
    final_score = (
        freq_score * weights["freq"] +
        pos_score * weights["pos"] +
        chain_score * weights["chain"] +
        entropy_score * weights["entropy"] +
        xor_score * weights["xor"]
    )

    prediction = "TÀI" if final_score >= 50 else "XỈU"
    confidence = abs(final_score - 50) * 2
    confidence = min(confidence + 20, 99.0)
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
