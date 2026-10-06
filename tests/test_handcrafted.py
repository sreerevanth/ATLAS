from atlas.handcrafted import validate_chains


def test_five_chain_gate_finds_source_bridge_and_answer():
    result = validate_chains(seed=42)
    assert len(result["cases"]) == 5
    assert all(case["traversal_pass"] for case in result["cases"])
    assert all(not case["cosine_pass"] for case in result["cases"])
