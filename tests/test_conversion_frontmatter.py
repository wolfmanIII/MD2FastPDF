"""Regression test: logic/conversion.py::MarkdownRenderer must never leak a
file's YAML frontmatter block into rendered HTML/PDF output — it's metadata
for the typed-relations feature (docs/ANALISI-relazioni-tipizzate.md), not
prose. Without stripping, a leading frontmatter block renders as a stray
<hr> followed by garbled paragraphs/headings in every PDF export and the
oracle summary pipeline (both go through MarkdownRenderer.render())."""
from logic.conversion import MarkdownRenderer


class TestMarkdownRendererStripsFrontmatter:
    def test_frontmatter_block_does_not_appear_in_rendered_html(self):
        content = (
            "---\n"
            "type: npc\n"
            "captain: Maelstrim\n"
            "---\n\n"
            "## KIRA LONN\n\n"
            "Testo normale qui.\n"
        )
        html = MarkdownRenderer().render(content)
        assert "captain" not in html
        assert "Maelstrim" not in html
        assert "<hr" not in html

    def test_body_content_after_frontmatter_renders_normally(self):
        content = "---\ntype: ship\ncrew: [Kira Venn]\n---\n\n## Beowulf\n\nMercantile Type-A.\n"
        html = MarkdownRenderer().render(content)
        assert "<h2" in html and "Beowulf" in html
        assert "Mercantile Type-A." in html

    def test_content_without_frontmatter_is_unaffected(self):
        content = "## No Frontmatter Here\n\nJust a normal document.\n"
        html = MarkdownRenderer().render(content)
        assert "<h2" in html and "No Frontmatter Here" in html
