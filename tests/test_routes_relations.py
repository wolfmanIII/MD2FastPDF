"""Unit tests for routes/relations.py — _LABELS construction.

Regression coverage for a real bug: the entity relations panel showed the
same label on both directions (e.g. "Equipaggio" instead of "Equipaggio di"
on the target's page), because _LABELS mapped every inverse name back to the
forward RelationDef.label instead of its own inverse_label.
"""
from routes.relations import _LABELS


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
