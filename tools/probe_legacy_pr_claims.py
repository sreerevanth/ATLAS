"""Safely reproduce legacy claims in temporary storage without importing servers."""

import ast
import json
import sqlite3
import sys
import tempfile
import time
from pathlib import Path

from capture_pr_triage import command, save


def extract(path, names):
    source = command("git", "show", f"HEAD:{path}")
    tree = ast.parse(source)
    nodes = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in names]
    for node in nodes:
        node.decorator_list = []
    return compile(ast.Module(body=nodes, type_ignores=[]), path, "exec")


def main():
    with tempfile.TemporaryDirectory(prefix="atlas-pr-triage-") as directory:
        database = Path(directory) / "fixture.db"
        with sqlite3.connect(database) as connection:
            connection.execute("CREATE TABLE topologies (node_name TEXT, commitment TEXT, lsh_hash TEXT)")
            connection.execute("INSERT INTO topologies VALUES (?, ?, ?)", ("synthetic-node", "client-string", "0" * 128))
        connection.close()

        class FixtureSQLite:
            @staticmethod
            def connect(unused_path):
                return sqlite3.connect(database)

        namespace = {"sqlite3": FixtureSQLite, "Depends": lambda function: None, "get_api_key": lambda: None}
        exec(extract("atlas-core/atlas_server.py", {"query_matches"}), namespace)
        empty = namespace["query_matches"]("", "client-string")
        copied = namespace["query_matches"]("0" * 128, "client-string")
        different = namespace["query_matches"]("0" * 128, "different")
        assert empty["matches"][0]["similarity"] == 1.0
        assert copied["matches"] and not different["matches"]

    namespace = {"OutOfFuelException": RuntimeError}
    exec(extract("atlas-core/advanced_enclave.py", {"InstructionFuelMeter"}), namespace)
    meter = namespace["InstructionFuelMeter"](1000)

    def native_wait():
        time.sleep(0.05)

    started = time.perf_counter()
    sys.settrace(meter.trace_execution)
    try:
        native_wait()
    finally:
        sys.settrace(None)
    elapsed = time.perf_counter() - started
    assert meter.consumed_fuel < 1000
    result = {"source_commit": command("git", "rev-parse", "HEAD").strip(),
              "scope": "Selected existing main function bodies via AST; no PR introduces these functions; no FastAPI auth/HTTP exercised",
              "empty_hash_with_copied_commitment": empty,
              "copied_string_accepted": bool(copied["matches"]),
              "different_string_returns_empty_matches": not different["matches"],
              "native_sleep_requested_seconds": 0.05, "native_sleep_observed_seconds": elapsed,
              "python_opcodes_consumed": meter.consumed_fuel,
              "fuel_budget": 1000, "temporary_db_removed": not database.exists()}
    save("legacy-probes.json", json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
