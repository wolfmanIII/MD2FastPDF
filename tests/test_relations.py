"""Unit tests for logic/relations.py — vocabulary, normalization, frontmatter parsing."""
from pathlib import Path

from logic.relations import (
    VOCABULARY,
    VOCABULARY_BY_NAME,
    Edge,
    FrontmatterRelationParser,
    ParseWarning,
    canonical_key,
    extract_frontmatter,
    strip_frontmatter,
    strip_wikilink,
)


# ---------------------------------------------------------------------------
# VOCABULARY
# ---------------------------------------------------------------------------

class TestVocabulary:
    def test_expected_relation_names_present(self):
        assert set(VOCABULARY_BY_NAME) == {
            "crew", "member_of", "located_in", "hostile_to", "owns",
            "owes_debt_to", "reports_to", "allied_with", "mentor_of", "npcs",
        }

    def test_npcs_inverse_is_scenes(self):
        assert VOCABULARY_BY_NAME["npcs"].inverse == "scenes"

    def test_hostile_to_is_symmetric(self):
        assert VOCABULARY_BY_NAME["hostile_to"].inverse == "hostile_to"

    def test_allied_with_is_symmetric(self):
        assert VOCABULARY_BY_NAME["allied_with"].inverse == "allied_with"

    def test_crew_inverse_is_serves_on(self):
        assert VOCABULARY_BY_NAME["crew"].inverse == "serves_on"

    def test_owes_debt_to_inverse_is_creditor_of(self):
        assert VOCABULARY_BY_NAME["owes_debt_to"].inverse == "creditor_of"

    def test_reports_to_inverse_is_has_subordinate(self):
        assert VOCABULARY_BY_NAME["reports_to"].inverse == "has_subordinate"

    def test_mentor_of_inverse_is_student_of(self):
        assert VOCABULARY_BY_NAME["mentor_of"].inverse == "student_of"

    def test_every_relation_has_a_distinct_inverse_label(self):
        # The reverse-direction UI label must say something different from the
        # forward one for asymmetric relations — "Equipaggio di" reads correctly
        # on the target's page, "Equipaggio" (the forward label) would not.
        for r in VOCABULARY:
            if r.inverse != r.name:
                assert r.inverse_label != r.label, r.name

    def test_symmetric_relations_have_matching_inverse_label(self):
        for r in VOCABULARY:
            if r.inverse == r.name:
                assert r.inverse_label == r.label, r.name

    def test_inverse_names_are_not_frontmatter_keys(self):
        names = {r.name for r in VOCABULARY}
        inverses = {r.inverse for r in VOCABULARY}
        # symmetric relations legitimately appear in both sets
        asymmetric_inverses = inverses - names
        assert asymmetric_inverses.isdisjoint(names)

    def test_domain_range_match_real_campaign_usage(self):
        # Values derived from the source/target entity types actually observed
        # in a real archive (RF-9) — not a designed-up-front ontology. Relations
        # left unconstrained here (located_in) are deliberately too generic to
        # constrain on today's observed types alone (see logic/relations.py).
        expected = {
            "crew": (("ship",), ("npc",)),
            "hostile_to": (("npc",), ("npc",)),
            "allied_with": (("npc",), ("npc",)),
            "mentor_of": (("npc",), ("npc",)),
            "reports_to": (("npc",), ("npc",)),
            "owes_debt_to": (("npc", "organization"), ("npc", "organization")),
            "member_of": (("npc", "organization"), ("organization",)),
            "owns": (("npc",), ("ship", "location", "drone", "item")),
            "located_in": (None, None),
            "npcs": (("scene",), ("npc",)),
        }
        for name, (domain, range_) in expected.items():
            r = VOCABULARY_BY_NAME[name]
            assert r.domain == domain, name
            assert r.range == range_, name


# ---------------------------------------------------------------------------
# strip_wikilink / canonical_key
# ---------------------------------------------------------------------------

class TestStripWikilink:
    def test_strips_double_brackets(self):
        assert strip_wikilink("[[Kira Venn]]") == "Kira Venn"

    def test_leaves_plain_string_untouched(self):
        assert strip_wikilink("Kira Venn") == "Kira Venn"

    def test_strips_surrounding_whitespace_first(self):
        assert strip_wikilink("  [[Kira Venn]]  ") == "Kira Venn"


class TestCanonicalKey:
    def test_casefolds(self):
        assert canonical_key("Kira Venn") == "kira venn"

    def test_collapses_multiple_spaces(self):
        assert canonical_key("Kira   Venn") == "kira venn"

    def test_strips_wikilink_before_normalizing(self):
        assert canonical_key("[[Kira Venn]]") == "kira venn"

    def test_handles_accents_as_plain_unicode_casefold(self):
        assert canonical_key("Tarn Mékel") == "tarn mékel".casefold()

    def test_empty_string(self):
        assert canonical_key("") == ""

    def test_empty_string_after_stripping_whitespace(self):
        assert canonical_key("   ") == ""


# ---------------------------------------------------------------------------
# extract_frontmatter
# ---------------------------------------------------------------------------

class TestExtractFrontmatter:
    def test_absent_frontmatter_returns_none(self):
        assert extract_frontmatter("Just a paragraph, no frontmatter.") is None

    def test_valid_mapping_with_list_value(self):
        content = "---\ntype: ship\ncrew: [Kira Venn, Tarn Mekel]\n---\n\nBody text.\n"
        meta = extract_frontmatter(content)
        assert meta == {"type": "ship", "crew": ["Kira Venn", "Tarn Mekel"]}

    def test_malformed_yaml_returns_none(self):
        content = "---\ncrew: [Kira Venn\n---\n\nBody.\n"
        assert extract_frontmatter(content) is None

    def test_non_mapping_frontmatter_returns_none(self):
        content = "---\n- just\n- a\n- list\n---\n\nBody.\n"
        assert extract_frontmatter(content) is None

    def test_unterminated_frontmatter_block_returns_none(self):
        content = "---\ntype: ship\ncrew: [Kira Venn]\n\nNo closing delimiter.\n"
        assert extract_frontmatter(content) is None

    def test_empty_frontmatter_block_returns_none(self):
        # yaml.safe_load("") -> None, which is not a mapping
        content = "---\n---\n\nBody.\n"
        assert extract_frontmatter(content) is None

    def test_null_value_key_is_preserved(self):
        content = "---\ncrew: null\n---\n\nBody.\n"
        meta = extract_frontmatter(content)
        assert meta == {"crew": None}


class TestStripFrontmatter:
    def test_removes_leading_frontmatter_block(self):
        # The blank line that follows the closing delimiter is part of the
        # body, not the frontmatter block itself, and is left in place.
        content = "---\ntype: ship\ncrew: [Kira Venn]\n---\n\n## Heading\n\nBody text.\n"
        assert strip_frontmatter(content) == "\n## Heading\n\nBody text.\n"

    def test_no_frontmatter_returns_content_unchanged(self):
        content = "## Heading\n\nJust a normal document.\n"
        assert strip_frontmatter(content) == content

    def test_strips_even_when_yaml_is_malformed(self):
        # Rendering shouldn't care whether the metadata itself parses — the
        # delimited block is never prose, valid or not.
        content = "---\ncrew: [unterminated\n---\n\nBody.\n"
        assert strip_frontmatter(content) == "\nBody.\n"

    def test_unterminated_block_is_left_untouched(self):
        # No closing delimiter: not a well-formed frontmatter block, so
        # nothing is stripped — this text is presumably meant as prose
        # (e.g. a document that starts with a genuine <hr>).
        content = "---\ntype: ship\n\nNo closing delimiter, this is just body text.\n"
        assert strip_frontmatter(content) == content

    def test_two_adjacent_delimiters_with_nothing_between_are_not_frontmatter(self):
        # Mirrors extract_frontmatter's own test_empty_frontmatter_block_returns_none:
        # the regex needs at least one line between the delimiters to recognize a
        # block at all, so this reads as two consecutive literal <hr>s, untouched.
        content = "---\n---\n\nBody.\n"
        assert strip_frontmatter(content) == content


# ---------------------------------------------------------------------------
# FrontmatterRelationParser
# ---------------------------------------------------------------------------

class TestFrontmatterRelationParser:
    def setup_method(self):
        self.parser = FrontmatterRelationParser()
        self.path = Path("ships/Beowulf.md")

    def test_list_value_produces_one_edge_per_item(self):
        edges = self.parser.parse(self.path, {"crew": ["Kira Venn", "Tarn Mekel"]})
        assert edges == [
            Edge(source="beowulf", target="kira venn", relation="crew", origin_path=self.path),
            Edge(source="beowulf", target="tarn mekel", relation="crew", origin_path=self.path),
        ]

    def test_scalar_string_value_is_treated_as_single_element_list(self):
        edges = self.parser.parse(self.path, {"crew": "Kira Venn"})
        assert edges == [Edge(source="beowulf", target="kira venn", relation="crew", origin_path=self.path)]

    def test_wikilink_values_are_stripped(self):
        edges = self.parser.parse(self.path, {"crew": ["[[Kira Venn]]"]})
        assert edges[0].target == "kira venn"

    def test_key_outside_vocabulary_is_ignored(self):
        edges = self.parser.parse(self.path, {"tags": ["misc"], "crew": ["Kira Venn"]})
        assert len(edges) == 1
        assert edges[0].relation == "crew"

    def test_no_vocabulary_keys_produces_no_edges(self):
        assert self.parser.parse(self.path, {"title": "The Beowulf"}) == []

    def test_empty_frontmatter_dict_produces_no_edges(self):
        assert self.parser.parse(self.path, {}) == []

    def test_empty_list_value_produces_no_edges(self):
        assert self.parser.parse(self.path, {"crew": []}) == []

    def test_null_value_is_ignored_with_no_edges(self):
        assert self.parser.parse(self.path, {"crew": None}) == []

    def test_non_string_scalar_value_is_ignored_with_no_edges(self):
        assert self.parser.parse(self.path, {"crew": 42}) == []

    def test_list_with_non_string_items_skips_only_those_items(self):
        edges = self.parser.parse(self.path, {"crew": ["Kira Venn", 42, None, "Tarn Mekel"]})
        assert [e.target for e in edges] == ["kira venn", "tarn mekel"]

    def test_symmetric_relation_produces_a_single_edge_not_duplicated(self):
        edges = self.parser.parse(self.path, {"hostile_to": ["Tarn Mekel"]})
        assert edges == [Edge(source="beowulf", target="tarn mekel", relation="hostile_to", origin_path=self.path)]

    def test_multiple_relation_keys_on_same_file(self):
        edges = self.parser.parse(self.path, {"crew": ["Kira Venn"], "owns": ["Cargo Manifest"]})
        relations = {e.relation for e in edges}
        assert relations == {"crew", "owns"}

    def test_source_key_derived_from_file_stem(self):
        path = Path("ships/The Beowulf.md")
        edges = self.parser.parse(path, {"crew": ["Kira Venn"]})
        assert edges[0].source == "the beowulf"

    def test_warnings_param_omitted_behaves_as_before(self):
        # Backward-compat: existing callers passing only (path, frontmatter) must
        # keep working unchanged (no warnings collection, log-only).
        edges = self.parser.parse(self.path, {"crew": 42})
        assert edges == []

    def test_unsupported_value_type_appends_a_parse_warning(self):
        warnings: list[ParseWarning] = []
        self.parser.parse(self.path, {"crew": 42}, warnings)
        assert len(warnings) == 1
        assert warnings[0].origin_path == self.path
        assert warnings[0].relation == "crew"

    def test_non_string_list_item_appends_a_parse_warning(self):
        warnings: list[ParseWarning] = []
        self.parser.parse(self.path, {"crew": ["Kira Venn", 42]}, warnings)
        assert len(warnings) == 1
        assert warnings[0].relation == "crew"

    def test_valid_values_append_no_warnings(self):
        warnings: list[ParseWarning] = []
        self.parser.parse(self.path, {"crew": ["Kira Venn"]}, warnings)
        assert warnings == []
