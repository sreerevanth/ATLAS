import hashlib
import html
import re
import time
import urllib.request

import numpy as np
import pyarrow.parquet as parquet

from atlas.corpus import DATA_URL, MODEL, REVISION
from .common import CACHE, OUT, ROOT, SEED, digest, manifest, read, write

MUSIQUE_URL = "https://huggingface.co/datasets/bdsaglam/musique/resolve/22873a405dd809893b22ada0b499299fb612d2df/musique_ans_v1.0_dev.jsonl"
MUSIQUE_SHA = "15fa63794d18a94ce12411aca6e2327e65b6e83b0b1490efab3f1962e48abf3b"
HOTPOT_SHA = "c20b638ca82b21d04fe12e14ff417ad05153d4d215a65de54497fca4e972f7c6"


def normalize(text):
    return " ".join(re.sub(r"<[^>]+>", " ", html.unescape(text)).split())


def download(path, url, expected):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        urllib.request.urlretrieve(url, path)
    if digest(path) != expected:
        raise AssertionError(f"Dataset checksum mismatch: {path}")


def components(records):
    parents = list(range(len(records)))

    def root(index):
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    owners = {}
    for index, record in enumerate(records):
        for key in record["support_keys"] + ["question:" + normalize(record["question"]).casefold()]:
            if key in owners:
                parents[root(index)] = root(owners[key])
            owners[key] = index
    return [root(index) for index in range(len(records))]


def hotpot_record(record):
    return {"id": record["id"], "question": record["question"], "type": record["type"],
            "level": record["level"], "support_keys": sorted(set(record["supporting_facts"]["title"])),
            "contexts": [(title, " ".join(sentences)) for title, sentences in
                         zip(record["context"]["title"], record["context"]["sentences"], strict=True)]}


def corpus(records, name):
    docs, mapping, exclusions, questions = [], {}, [], []
    original = 0
    for record in records:
        for title, raw_text in record["contexts"]:
            original += 1
            text = normalize(raw_text)
            identity = hashlib.sha256((title + "\n" + text).encode()).hexdigest()
            if not text or "\ufffd" in text:
                exclusions.append({"question_id": record["id"], "title": title, "reason": "invalid_or_empty"})
                continue
            if identity in mapping:
                exclusions.append({"question_id": record["id"], "title": title, "reason": "duplicate"})
                continue
            mapping[identity] = len(docs)
            docs.append({"id": identity, "title": title, "text": text,
                         "key": title if name == "hotpot" else identity})
        questions.append({key: value for key, value in record.items() if key != "contexts"})
    available = {doc["key"] for doc in docs}
    assert all(set(query["support_keys"]) <= available for query in questions)
    write(CACHE / name / "documents.json", docs)
    write(CACHE / name / "questions.json", questions)
    write(OUT / f"{name}-quality.json", {"original_occurrences": original, "cleaned_count": len(docs),
          "duplicates": sum(item["reason"] == "duplicate" for item in exclusions),
          "invalid_empty": sum(item["reason"] != "duplicate" for item in exclusions),
          "exclusions": exclusions, "document_sha256": digest(CACHE / name / "documents.json")})
    write(OUT / f"{name}-split.json", [{key: value for key, value in query.items()
                                      if key != "question"} for query in questions])
    return docs, questions


def prepare():
    info = manifest(".venv-release/Scripts/python -m research.v2.run prepare")
    download(ROOT / "data/raw/hotpot_dev_distractor_v1.parquet", DATA_URL, HOTPOT_SHA)
    download(ROOT / "data/raw/musique_ans_v1.0_dev.jsonl", MUSIQUE_URL, MUSIQUE_SHA)
    raw = parquet.read_table(ROOT / "data/raw/hotpot_dev_distractor_v1.parquet").to_pylist()
    old_path = ROOT / "artifacts/local/research/questions.json"
    old = read(old_path) if old_path.exists() else [
        {"id": raw[int(index)]["id"], "question": raw[int(index)]["question"],
         "support_titles": sorted(set(raw[int(index)]["supporting_facts"]["title"]))}
        for index in np.random.default_rng(42).permutation(len(raw))[:1500]]
    old_ids = {item["id"] for item in old}
    old_titles = {title for item in old for title in item["support_titles"]}
    old_text = {normalize(item["question"]).casefold() for item in old}
    eligible, excluded = [], []
    for item in raw:
        record = hotpot_record(item)
        reason = ("v1_question" if record["id"] in old_ids else "v1_support_overlap"
                  if set(record["support_keys"]) & old_titles else "duplicate_question"
                  if normalize(record["question"]).casefold() in old_text else None)
        if reason:
            excluded.append({"id": record["id"], "reason": reason})
        else:
            eligible.append(record)
    groups = components(eligible)
    unique = sorted(set(groups))
    rng = np.random.default_rng(SEED)
    order = rng.permutation(unique)
    first, second = len(order) // 4, len(order) // 2
    pool = {int(group): "dev" if index < first else "validation" if index < second else "test"
            for index, group in enumerate(order)}
    selected = []
    for split, count in [("dev", 200), ("validation", 200), ("test", 400)]:
        choices = [index for index, group in enumerate(groups) if pool[group] == split]
        if len(choices) < count:
            raise RuntimeError(f"Insufficient eligible {split} questions: {len(choices)}")
        for index in rng.permutation(choices)[:count]:
            record = eligible[int(index)]
            record.update(split=split, group=str(groups[index]))
            selected.append(record)
    corpus(selected, "hotpot")
    avoid_titles = old_titles | {title for item in selected for title in item["support_keys"]}
    avoid_text = old_text | {normalize(item["question"]).casefold() for item in selected}
    music, music_excluded = [], []
    with (ROOT / "data/raw/musique_ans_v1.0_dev.jsonl").open(encoding="utf8") as stream:
        import json
        for line in stream:
            item = json.loads(line)
            support = [para for para in item["paragraphs"] if para["is_supporting"]]
            if (not item["answerable"] or normalize(item["question"]).casefold() in avoid_text
                    or {para["title"] for para in support} & avoid_titles):
                music_excluded.append(item["id"])
                continue
            keys = [hashlib.sha256((para["title"] + "\n" + normalize(para["paragraph_text"])).encode()).hexdigest()
                    for para in support]
            music.append({"id": item["id"], "question": item["question"], "support_keys": sorted(set(keys)),
                          "type": "musique", "level": str(len(item["question_decomposition"])),
                          "contexts": [(para["title"], para["paragraph_text"]) for para in item["paragraphs"]]})
    assert len(music) >= 300
    music = [music[int(index)] for index in rng.permutation(len(music))[:300]]
    for record, group in zip(music, components(music), strict=True):
        record.update(split="test", group=str(group))
    corpus(music, "musique")
    info.update(hotpot_url=DATA_URL, hotpot_sha256=HOTPOT_SHA, musique_url=MUSIQUE_URL,
                musique_sha256=MUSIQUE_SHA, hotpot_available=len(raw), hotpot_eligible=len(eligible),
                hotpot_exclusions=excluded, musique_exclusions=music_excluded,
                split_policy="shared-support components; transductive pooled distractor corpus")
    write(OUT / "prepare-manifest.json", info)
    print({"hotpot_eligible": len(eligible), "components": len(unique), "musique_selected": len(music)}, flush=True)


def embed():
    info = manifest(".venv-release/Scripts/python -m research.v2.run embed")
    import torch
    from sentence_transformers import SentenceTransformer
    torch.set_num_threads(4)
    torch.manual_seed(SEED)
    model = SentenceTransformer(MODEL, revision=REVISION, device="cpu")
    results = {}
    for name in ("hotpot", "musique"):
        docs = read(CACHE / name / "documents.json")
        queries = read(CACHE / name / "questions.json")
        texts = [doc["title"] + ": " + doc["text"] for doc in docs] + [query["question"] for query in queries]
        start = time.perf_counter()
        vectors = model.encode(texts, batch_size=64, normalize_embeddings=True, show_progress_bar=True)
        elapsed = time.perf_counter() - start
        repeated = model.encode(texts[:8], batch_size=8, normalize_embeddings=True)
        error = float(np.max(np.abs(repeated - vectors[:8])))
        assert error < 1e-5
        np.save(CACHE / name / "documents.npy", vectors[:len(docs)])
        np.save(CACHE / name / "queries.npy", vectors[len(docs):])
        results[name] = {"documents": len(docs), "queries": len(queries), "wall_seconds": elapsed,
                         "texts_per_second": len(texts) / elapsed, "reencode_max_abs_error": error,
                         "files": {filename: digest(CACHE / name / filename) for filename in
                                   ("documents.npy", "queries.npy", "documents.json", "questions.json")}}
    info.update(model=MODEL, revision=REVISION, dimensions=384, batch_size=64, threads=4,
                max_sequence_length=model.max_seq_length, chunking=False, results=results)
    write(OUT / "embed-manifest.json", info)
