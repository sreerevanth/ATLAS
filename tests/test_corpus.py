import pyarrow as pa
import pyarrow.parquet as parquet

from atlas.corpus import prepare


def test_cleaning_counts_duplicates_short_records_and_support(tmp_path):
    rows = [
        {"id": "q1", "question": "Question one?", "type": "bridge", "level": "easy",
         "context": {"title": ["Alpha", "Shared"],
                     "sentences": [["Alpha has a sufficiently long sentence."],
                                   ["Shared text is long enough for this fixture."]]},
         "supporting_facts": {"title": ["Alpha"]}},
        {"id": "q2", "question": "Question two?", "type": "comparison", "level": "medium",
         "context": {"title": ["Shared", "Tiny"],
                     "sentences": [["Shared text is long enough for this fixture."], ["short"]]},
         "supporting_facts": {"title": ["Shared"]}},
    ]
    source = tmp_path / "tiny.parquet"
    parquet.write_table(pa.Table.from_pylist(rows), source)

    documents, questions, quality = prepare(source, count=2, seed=42)

    assert len(questions) == 2
    assert len(documents) == 2
    assert quality["original_document_occurrences"] == 4
    assert quality["duplicates"] == 1
    assert quality["near_empty_documents"] == 1
    assert quality["missing_support_queries"] == []
