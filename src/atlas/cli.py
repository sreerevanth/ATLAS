"""Research commands with explicit configuration and evidence outputs."""

import argparse
import json
import logging
from pathlib import Path

import numpy as np

from atlas.evidence import manifest, write_json
from atlas.topology import ground_truth


def main():
    parser = argparse.ArgumentParser(description="ATLAS reproducible research")
    subcommands = parser.add_subparsers(dest="command", required=True)
    for name in ("validate", "corpus", "ann", "scaling", "retrieval", "handcrafted", "tip", "integration", "anomaly"):
        command = subcommands.add_parser(name)
        command.add_argument("--config", type=Path, default=Path("configs/research.json"))
        command.add_argument("--output", type=Path, default=Path("artifacts/local/research"))
    worker_parser = subcommands.add_parser("topology-worker")
    worker_parser.add_argument("source", type=Path)
    worker_parser.add_argument("count", type=int)
    worker_parser.add_argument("landmarks", type=int)
    worker_parser.add_argument("destination", type=Path)
    worker_parser.add_argument("--config", type=Path, default=Path("configs/research.json"))
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    if args.command == "topology-worker":
        from atlas.scaling import worker
        config = json.loads(args.config.read_text())
        worker(args.source, args.count, args.landmarks, args.destination, config)
        return
    if args.command == "handcrafted":
        from atlas.handcrafted import require_all_chains
        result = require_all_chains(42)
        args.output.mkdir(parents=True, exist_ok=True)
        write_json(args.output / "handcrafted_retrieval_gate.json", result)
        logging.info(json.dumps({"event": "completed", "command": args.command,
                                 "all_pass": result["all_pass"]}))
        return
    config = json.loads(args.config.read_text())
    output = args.output
    output.mkdir(parents=True, exist_ok=True)
    write_json(output / f"{args.command}-manifest.json", manifest(Path.cwd(), config))
    logging.info(json.dumps({"event": "started", "command": args.command}))
    gates = ground_truth(config["seed"])
    write_json(output / "topology_gate.json", gates)
    if args.command == "corpus":
        from atlas.corpus import acquire, embed, prepare
        raw = acquire(Path("data/raw"))
        documents, questions, quality = prepare(raw, config["questions"], config["seed"])
        quality["license"] = "CC BY-SA 4.0"
        write_json(output / "data_quality.json", quality)
        write_json(output / "documents.json", documents)
        write_json(output / "questions.json", questions)
        embed(documents, questions, output, config["batch_size"])
    elif args.command in ("ann", "retrieval"):
        from atlas.retrieval import ann_benchmark, evaluate
        vectors = np.load(output / "documents.npy")
        queries = np.load(output / "queries.npy")[:config["evaluation_questions"]]
        if args.command == "ann":
            result = ann_benchmark(vectors, queries, output)
        else:
            documents = json.loads((output / "documents.json").read_text(encoding="utf-8"))
            questions = json.loads((output / "questions.json").read_text(encoding="utf-8"))[:len(queries)]
            result = evaluate(documents, questions, vectors, queries, config)
        write_json(output / f"{args.command}.json", result)
    elif args.command == "scaling":
        from atlas.scaling import run_scaling
        write_json(output / "scaling.json", run_scaling(output / "documents.npy", output, config))
    elif args.command == "tip":
        from atlas.tip_experiment import experiment
        write_json(output / "tip.json", experiment(config))
    elif args.command == "integration":
        import asyncio
        from atlas.transport import demonstration
        write_json(output / "integration.json", asyncio.run(demonstration(output)))
    elif args.command == "anomaly":
        from atlas.anomaly import experiment
        write_json(output / "anomaly.json", experiment(config))
    logging.info(json.dumps({"event": "completed", "command": args.command}))


if __name__ == "__main__":
    main()
