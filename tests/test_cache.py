from morph_studio.cache import cache_key


def test_cache_is_deterministic_and_changes_with_model():
    fields = dict(task={"seed": 1}, dependencies={"anchor": "abc"},
                  workflow_sha256="workflow", model_sha256={"wan": "a"},
                  code_revision="commit1")
    assert cache_key(**fields) == cache_key(**fields)
    changed = dict(fields, model_sha256={"wan": "b"})
    assert cache_key(**fields) != cache_key(**changed)
