"""Tests for the VariablePool primitive (canvas data-flow resolver)."""

from __future__ import annotations

from app.shared_kernel.variable_pool import VariablePool


def test_typed_exact_replacement_preserves_type():
    pool = VariablePool()
    pool.set("node", {"count": 5, "items": [{"name": "a"}, {"name": "b"}]})
    # A lone {{ ref }} returns the underlying value, not a string.
    assert pool.resolve("{{node.count}}") == 5
    assert pool.resolve("{{node.items}}") == [{"name": "a"}, {"name": "b"}]
    assert pool.resolve("{{node.items[1].name}}") == "b"


def test_expression_evaluation():
    pool = VariablePool()
    pool.set("counter", {"value": 7})
    assert pool.resolve("{{counter.value + 1}}") == 8
    assert pool.resolve("{{counter.value > 5}}") is True
    assert pool.resolve("{{len(counter)}}") == 1


def test_jinja_template_rendering_with_surrounding_text():
    pool = VariablePool()
    pool.set("user", {"name": "Ada"})
    assert pool.resolve("Hello {{ user.name }}!") == "Hello Ada!"


def test_nested_dict_and_list_resolution():
    pool = VariablePool()
    pool.set("start", {"env": "prod"})
    resolved = pool.resolve({"target": "{{start.env}}", "tags": ["{{start.env}}", "static"]})
    assert resolved == {"target": "prod", "tags": ["prod", "static"]}


def test_flat_dotnotation_keys_expand():
    pool = VariablePool()
    pool.set("a.b.c", 42)
    assert pool.resolve("{{a.b.c}}") == 42


def test_unresolvable_reference_falls_back_to_literal_text():
    pool = VariablePool()
    # Missing reference renders to empty (Jinja) rather than raising.
    assert pool.resolve("value={{missing.key}}") == "value="


def test_get_with_default():
    pool = VariablePool()
    pool.set("x", {"y": 1})
    assert pool.get("x.y") == 1
    assert pool.get("nope", default="d") == "d"
