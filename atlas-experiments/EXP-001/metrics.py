import numpy as np

def hash_agreement(hash1, hash2):
    return np.mean(hash1 == hash2)

def collision_rate(hashes):
    n = len(hashes)
    collisions = 0
    total_pairs = n * (n - 1) / 2
    for i in range(n):
        for j in range(i+1, n):
            if np.array_equal(hashes[i], hashes[j]):
                collisions += 1
    return collisions / total_pairs if total_pairs > 0 else 0
