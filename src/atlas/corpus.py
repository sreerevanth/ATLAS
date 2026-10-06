"""HotpotQA acquisition, explicit cleaning, and pinned text embeddings."""

import hashlib
import html
import re
import time
import urllib.request
from pathlib import Path

import numpy as np

from atlas.evidence import digest, write_json

DATA_REVISION = "a8af52d40ca73810f304ad1aa28b0cbb518f37de"
DATA_URL = f"https://huggingface.co/datasets/hotpotqa/hotpot_qa/resolve/{DATA_REVISION}/distractor/validation-00000-of-00001.parquet"
MODEL = "sentence-transformers/all-MiniLM-L6-v2"
REVISION = "c9745ed1d9f207416be6d2e6f8de32d1f16199bf"


def acquire(directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    destination = directory / "hotpot_dev_distractor_v1.parquet"
    if not destination.exists():
        temporary = destination.with_suffix(".partial")
        with urllib.request.urlopen(DATA_URL, timeout=60) as response, temporary.open("wb") as target:
            while block := response.read(1024 * 1024):
                target.write(block)
        temporary.replace(destination)
    return destination


def prepare(raw_path: Path, count: int, seed: int):
    import pyarrow.parquet as parquet
    raw = parquet.read_table(raw_path).to_pylist()
    if not 1 <= count <= len(raw):
        raise ValueError("Question sample exceeds dataset")
    chosen = np.random.default_rng(seed).permutation(len(raw))[:count]
    documents, questions, exclusions = [], [], []
    hashes, title_map = {}, {}
    original = 0
    for index in chosen:
        record = raw[int(index)]
        for title, sentences in zip(record["context"]["title"], record["context"]["sentences"], strict=True):
            original += 1
            text = " ".join(html.unescape(" ".join(sentences)).split())
            text = re.sub(r"<[^>]+>", " ", text).strip()
            if "\ufffd" in text:
                exclusions.append({"question": record["id"], "title": title, "reason": "replacement_character"})
                continue
            if len(text) < 20:
                exclusions.append({"question": record["id"], "title": title,
                                   "reason": "empty" if not text else "near_empty_under_20_chars"})
                continue
            content_hash = hashlib.sha256((title + "\n" + text).encode()).hexdigest()
            if content_hash in hashes:
                exclusions.append({"question": record["id"], "title": title, "reason": "exact_duplicate"})
            else:
                hashes[content_hash] = len(documents)
                documents.append({"id": content_hash, "title": title, "text": text})
            title_map.setdefault(title, set()).add(hashes[content_hash])
        questions.append({
            "id": record["id"], "question": record["question"],
            "type": record["type"], "level": record["level"],
            "support_titles": sorted(set(record["supporting_facts"]["title"])),
        })
    missing = [query["id"] for query in questions if any(
        title not in title_map for title in query["support_titles"]
    )]
    quality = {
        "dataset": "HotpotQA dev distractor v1", "url": DATA_URL, "revision": DATA_REVISION,
        "license": "CC BY-SA 4.0",
        "raw_sha256": digest(raw_path), "available_questions": len(raw),
        "sampled_questions": count, "seed": seed,
        "original_document_occurrences": original, "cleaned_documents": len(documents),
        "duplicates": sum(row["reason"] == "exact_duplicate" for row in exclusions),
        "invalid_text": sum(row["reason"] == "replacement_character" for row in exclusions),
        "empty_documents": sum(row["reason"] == "empty" for row in exclusions),
        "near_empty_documents": sum(row["reason"] == "near_empty_under_20_chars" for row in exclusions),
        "encoding_errors": 0,
        "encoding_policy": "Parquet UTF-8 decode is strict; invalid decode aborts acquisition processing",
        "exclusions": exclusions, "missing_support_queries": missing,
        "deduplication": "SHA256 of normalized title and text; near-duplicates not removed",
        "evaluation": "Pooled corpus from sampled distractor contexts, not official fullwiki",
    }
    if missing:
        raise ValueError(f"Missing supporting documents: {missing}")
    return documents, questions, quality


def embed(documents, questions, directory: Path, batch_size: int = 64):
    import torch
    from sentence_transformers import SentenceTransformer

    torch.set_num_threads(4)
    torch.manual_seed(42)
    model = SentenceTransformer(MODEL, revision=REVISION, device="cpu")
    texts = [item["title"] + ": " + item["text"] for item in documents]
    texts += [item["question"] for item in questions]
    started = time.perf_counter()
    vectors = model.encode(texts, batch_size=batch_size, normalize_embeddings=True, show_progress_bar=True)
    elapsed = time.perf_counter() - started
    check_first = model.encode(texts[:8], batch_size=8, normalize_embeddings=True)
    check_second = model.encode(texts[:8], batch_size=8, normalize_embeddings=True)
    deviation = float(np.max(np.abs(check_first - check_second)))
    if deviation > 1e-6:
        raise AssertionError("Embedding reproducibility failed")
    np.save(directory / "documents.npy", vectors[:len(documents)])
    np.save(directory / "queries.npy", vectors[len(documents):])
    metadata = {
        "model": MODEL, "revision": REVISION, "dimensions": int(vectors.shape[1]),
        "batch_size": batch_size, "hardware": "CPU", "threads": 4,
        "wall_seconds": elapsed, "texts_per_second": len(texts) / elapsed,
        "max_sequence_length": model.max_seq_length,
        "truncation": "Model truncates beyond max_sequence_length; no chunking",
        "repeated_subsample_max_abs_difference": deviation,
        "documents_sha256": digest(directory / "documents.npy"),
        "queries_sha256": digest(directory / "queries.npy"),
    }
    write_json(directory / "embedding_metadata.json", metadata)
    return vectors[:len(documents)], vectors[len(documents):], metadata
