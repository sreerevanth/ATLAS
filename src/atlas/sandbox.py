"""Capability-minimal Wasmtime execution for signed research modules."""

import struct

import wasmtime
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


def execute(module_bytes: bytes, signature: bytes, trusted_key: bytes, region: bytes,
            fuel: int = 10000, memory_bytes: int = 2 * 65536) -> bytes:
    if len(module_bytes) > 65536 or fuel <= 0 or len(region) > memory_bytes:
        raise ValueError("Invalid execution limits or input")
    Ed25519PublicKey.from_public_bytes(trusted_key).verify(signature, module_bytes)
    configuration = wasmtime.Config()
    configuration.consume_fuel = True
    with wasmtime.Engine(configuration) as engine:
        with wasmtime.Store(engine) as store:
            store.set_fuel(fuel)
            store.set_limits(memory_size=memory_bytes, table_elements=1000, instances=1, tables=1, memories=1)
            with wasmtime.Module(engine, module_bytes) as module:
                if len(module.imports) != 0:
                    raise ValueError("No imports, WASI, filesystem or network capabilities allowed")
                instance = wasmtime.Instance(store, module, [])
                exports = instance.exports(store)
                memory = exports.get("memory")
                if not isinstance(memory, wasmtime.Memory):
                    raise ValueError("Module must export linear memory")
                run = instance.exports(store)["run"]
                function_type = run.type(store)
                if [str(value) for value in function_type.params] != ["i32", "i32"] or [str(value) for value in function_type.results] != ["i32"]:
                    raise ValueError("Expected run(pointer, length) -> i32")
                memory.write(store, region, 0)
                result = run(store, 0, len(region))
                return struct.pack("<i", result)


def count_module() -> bytes:
    wat = """(module
      (memory (export "memory") 1 2)
      (func (export "run") (param $ptr i32) (param $len i32) (result i32)
        (local $i i32) (local $sum i32)
        (block $done
          (loop $again
            (br_if $done (i32.ge_u (local.get $i) (local.get $len)))
            (local.set $sum
              (i32.add (local.get $sum)
                (i32.load8_u (i32.add (local.get $ptr) (local.get $i)))))
            (local.set $i (i32.add (local.get $i) (i32.const 1)))
            (br $again)))
        (local.get $sum)))"""
    return bytes(wasmtime.wat2wasm(wat))
