"""Unit tests for routes/relations.py — _LABELS construction.

Regression coverage for a real bug: the entity relations panel showed the
same label on both directions (e.g. "Equipaggio" instead of "Equipaggio di"
on the target's page), because _LABELS mapped every inverse name back to the
forward RelationDef.label instead of its own inverse_label.
"""
from pathlib import Path

from logic.relations import Entity
from routes.relations import _LABELS, _split_scene_references


class TestLabels:
    def test_forward_name_maps_to_forward_label(self):
        assert _LABELS["crew"] == "Equipaggio"

    def test_inverse_name_maps_to_inverse_label_not_forward_label(self):
        assert _LABELS["serves_on"] == "Equipaggio di"
        assert _LABELS["serves_on"] != _LABELS["crew"]

    def test_asymmetric_relation_labels_differ_in_both_directions(self):
        assert _LABELS["reports_to"] == "Risponde a"
        assert _LABELS["has_subordinate"] == "Subordinati"

    def test_symmetric_relation_uses_the_same_label_both_ways(self):
        assert _LABELS["hostile_to"] == "Ostile a"

    def test_scenes_bucket_maps_to_scene_label(self):
        assert _LABELS["_scenes"] == "Scene"


def _make_entity(name: str, entity_type: str | None) -> Entity:
    return Entity(key=name.lower(), display_name=name, path=Path(f"{name}.md"), entity_type=entity_type, mtime=0.0)


class TestSplitSceneReferences:
    def test_scene_sources_move_to_scenes_bucket(self):
        scene = _make_entity("Scena-0001", "scene")
        relations = {"scenes_org": [scene]}

        result = _split_scene_references(relations)

        assert "scenes_org" not in result
        assert result["_scenes"] == [scene]

    def test_non_scene_sources_stay_under_original_key(self):
        npc = _make_entity("Dorel-Varr", "npc")
        relations = {"scenes_org": [npc]}

        result = _split_scene_references(relations)

        assert result["scenes_org"] == [npc]
        assert "_scenes" not in result

    def test_mixed_sources_split_between_both_buckets(self):
        scene = _make_entity("Scena-0001", "scene")
        npc = _make_entity("Dorel-Varr", "npc")
        relations = {"scenes_org": [scene, npc], "scenes": [scene]}

        result = _split_scene_references(relations)

        assert result["scenes_org"] == [npc]
        assert result["_scenes"] == [scene, scene]

    def test_untyped_source_is_not_treated_as_scene(self):
        untyped = _make_entity("Archivio-Lysander", None)
        relations = {"scenes_org": [untyped]}

        result = _split_scene_references(relations)

        assert result["scenes_org"] == [untyped]
        assert "_scenes" not in result

    def test_unrelated_relations_pass_through_untouched(self):
        npc = _make_entity("Malen-Trast", "npc")
        relations = {"npcs": [npc]}

        result = _split_scene_references(relations)

        assert result == {"npcs": [npc]}

    def test_no_scene_keys_returns_equivalent_dict(self):
        assert _split_scene_references({}) == {}
