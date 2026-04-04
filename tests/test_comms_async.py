"""Async I/O tests for logic/comms.py — CommsManager file operations."""
import pytest
from pathlib import Path

from logic.comms import CommsManager
from logic.exceptions import CommsError, NotFoundError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _setup_user(base: Path, username: str) -> CommsManager:
    """Pre-creates comms folders for a user (sync, as bootstrap does)."""
    mgr = CommsManager()
    mgr.create_comms_folders_sync(username)
    return mgr


# ---------------------------------------------------------------------------
# create_comms_folders
# ---------------------------------------------------------------------------

class TestCreateCommsFolders:
    @pytest.mark.anyio
    async def test_creates_all_subfolders(self, patch_comms_base: Path):
        mgr = CommsManager()
        await mgr.create_comms_folders("alice")
        user_comms = patch_comms_base / "alice" / "comms"
        assert (user_comms / "inbound").is_dir()
        assert (user_comms / "outbound").is_dir()
        assert (user_comms / "staging").is_dir()

    @pytest.mark.anyio
    async def test_idempotent(self, patch_comms_base: Path):
        mgr = CommsManager()
        await mgr.create_comms_folders("alice")
        await mgr.create_comms_folders("alice")  # must not raise
        assert (patch_comms_base / "alice" / "comms" / "inbound").is_dir()


# ---------------------------------------------------------------------------
# list_folder
# ---------------------------------------------------------------------------

class TestListFolder:
    @pytest.mark.anyio
    async def test_empty_when_folder_missing(self, patch_comms_base: Path):
        mgr = CommsManager()
        result = await mgr.list_folder("alice", "inbound")
        assert result == []

    @pytest.mark.anyio
    async def test_returns_parsed_records(self, patch_comms_base: Path):
        mgr = _setup_user(patch_comms_base, "alice")
        inbound = patch_comms_base / "alice" / "comms" / "inbound"
        (inbound / "20240101T000000_abc12345_hello.md").write_text(
            "---\nid: abc\nfrom: bob\nto: alice\nsubject: hello\ntimestamp: 2024-01-01T00:00:00+00:00\nread: false\n---\n\nHi!"
        )
        result = await mgr.list_folder("alice", "inbound")
        assert len(result) == 1
        assert result[0].sender == "bob"
        assert result[0].subject == "hello"
        assert result[0].read is False

    @pytest.mark.anyio
    async def test_skips_malformed_files(self, patch_comms_base: Path):
        mgr = _setup_user(patch_comms_base, "alice")
        inbound = patch_comms_base / "alice" / "comms" / "inbound"
        (inbound / "bad.md").write_text("not frontmatter at all")
        result = await mgr.list_folder("alice", "inbound")
        assert result == []

    @pytest.mark.anyio
    async def test_sorted_newest_first(self, patch_comms_base: Path):
        mgr = _setup_user(patch_comms_base, "alice")
        inbound = patch_comms_base / "alice" / "comms" / "inbound"
        fm = "---\nid: x\nfrom: bob\nto: alice\nsubject: s\ntimestamp: t\nread: false\n---\n\n"
        (inbound / "20240102T000000_aaaaaaaa_s.md").write_text(fm)
        (inbound / "20240101T000000_bbbbbbbb_s.md").write_text(fm)
        result = await mgr.list_folder("alice", "inbound")
        assert result[0].filename > result[1].filename


# ---------------------------------------------------------------------------
# send_message
# ---------------------------------------------------------------------------

class TestSendMessage:
    @pytest.mark.anyio
    async def test_creates_outbound_and_inbound(self, patch_comms_base: Path):
        mgr = _setup_user(patch_comms_base, "alice")
        _setup_user(patch_comms_base, "bob")
        rec = await mgr.send_message("alice", "bob", "Greetings", "Hello!", ["bob"])
        assert (patch_comms_base / "alice" / "comms" / "outbound" / rec.filename).exists()
        assert (patch_comms_base / "bob" / "comms" / "inbound" / rec.filename).exists()

    @pytest.mark.anyio
    async def test_creates_recipient_folders_if_missing(self, patch_comms_base: Path):
        mgr = _setup_user(patch_comms_base, "alice")
        # bob has no folders yet — send_message must create them
        rec = await mgr.send_message("alice", "bob", "Subj", "Body", ["bob"])
        assert (patch_comms_base / "bob" / "comms" / "inbound" / rec.filename).exists()

    @pytest.mark.anyio
    async def test_returns_message_record(self, patch_comms_base: Path):
        mgr = _setup_user(patch_comms_base, "alice")
        rec = await mgr.send_message("alice", "bob", "Subj", "Body", ["bob"])
        assert rec.sender == "alice"
        assert rec.subject == "Subj"
        assert rec.read is False

    @pytest.mark.anyio
    async def test_forbidden_recipient_raises(self, patch_comms_base: Path):
        mgr = _setup_user(patch_comms_base, "alice")
        with pytest.raises(CommsError, match="RECIPIENT_NOT_ALLOWED"):
            await mgr.send_message("alice", "mallory", "Subj", "Body", ["bob"])

    @pytest.mark.anyio
    async def test_all_expands_and_delivers(self, patch_comms_base: Path):
        mgr = _setup_user(patch_comms_base, "alice")
        rec = await mgr.send_message("alice", "ALL", "Broadcast", "Hi all", ["bob", "carol"])
        assert (patch_comms_base / "bob" / "comms" / "inbound" / rec.filename).exists()
        assert (patch_comms_base / "carol" / "comms" / "inbound" / rec.filename).exists()


# ---------------------------------------------------------------------------
# mark_read
# ---------------------------------------------------------------------------

class TestMarkRead:
    @pytest.mark.anyio
    async def test_toggles_read_flag(self, patch_comms_base: Path):
        mgr = _setup_user(patch_comms_base, "alice")
        inbound = patch_comms_base / "alice" / "comms" / "inbound"
        fname = "20240101T000000_abc12345_hello.md"
        (inbound / fname).write_text(
            "---\nid: abc\nfrom: bob\nto: alice\nsubject: hello\ntimestamp: 2024-01-01T00:00:00+00:00\nread: false\n---\n\nBody"
        )
        await mgr.mark_read("alice", "inbound", fname)
        content = (inbound / fname).read_text()
        assert "read: true" in content

    @pytest.mark.anyio
    async def test_noop_if_already_read(self, patch_comms_base: Path):
        mgr = _setup_user(patch_comms_base, "alice")
        inbound = patch_comms_base / "alice" / "comms" / "inbound"
        fname = "20240101T000000_abc12345_hello.md"
        original = "---\nid: abc\nfrom: bob\nto: alice\nsubject: hello\ntimestamp: 2024-01-01T00:00:00+00:00\nread: true\n---\n\nBody"
        (inbound / fname).write_text(original)
        await mgr.mark_read("alice", "inbound", fname)
        assert (inbound / fname).read_text() == original

    @pytest.mark.anyio
    async def test_noop_if_file_missing(self, patch_comms_base: Path):
        mgr = CommsManager()
        await mgr.mark_read("alice", "inbound", "ghost.md")  # must not raise


# ---------------------------------------------------------------------------
# delete_message
# ---------------------------------------------------------------------------

class TestDeleteMessage:
    @pytest.mark.anyio
    async def test_deletes_file(self, patch_comms_base: Path):
        mgr = _setup_user(patch_comms_base, "alice")
        inbound = patch_comms_base / "alice" / "comms" / "inbound"
        fname = "msg.md"
        (inbound / fname).write_text("---\nid: x\n---\n")
        await mgr.delete_message("alice", "inbound", fname)
        assert not (inbound / fname).exists()

    @pytest.mark.anyio
    async def test_missing_raises(self, patch_comms_base: Path):
        mgr = _setup_user(patch_comms_base, "alice")
        with pytest.raises(NotFoundError, match="MESSAGE_NOT_FOUND"):
            await mgr.delete_message("alice", "inbound", "ghost.md")


# ---------------------------------------------------------------------------
# count_unread
# ---------------------------------------------------------------------------

class TestCountUnread:
    @pytest.mark.anyio
    async def test_counts_only_unread(self, patch_comms_base: Path):
        mgr = _setup_user(patch_comms_base, "alice")
        inbound = patch_comms_base / "alice" / "comms" / "inbound"
        fm_unread = "---\nid: a\nfrom: bob\nto: alice\nsubject: s\ntimestamp: t\nread: false\n---\n\n"
        fm_read = "---\nid: b\nfrom: bob\nto: alice\nsubject: s\ntimestamp: t\nread: true\n---\n\n"
        (inbound / "20240101T000000_aaaaaaaa_s.md").write_text(fm_unread)
        (inbound / "20240102T000000_bbbbbbbb_s.md").write_text(fm_read)
        assert await mgr.count_unread("alice") == 1

    @pytest.mark.anyio
    async def test_zero_when_no_inbound(self, patch_comms_base: Path):
        mgr = CommsManager()
        assert await mgr.count_unread("nobody") == 0


# ---------------------------------------------------------------------------
# save_draft / promote_draft
# ---------------------------------------------------------------------------

class TestSaveDraft:
    @pytest.mark.anyio
    async def test_writes_to_staging(self, patch_comms_base: Path):
        mgr = _setup_user(patch_comms_base, "alice")
        rec = await mgr.save_draft("alice", "bob", "Draft Subj", "Draft body")
        staging = patch_comms_base / "alice" / "comms" / "staging"
        assert (staging / rec.filename).exists()

    @pytest.mark.anyio
    async def test_overwrites_existing_draft(self, patch_comms_base: Path):
        mgr = _setup_user(patch_comms_base, "alice")
        rec1 = await mgr.save_draft("alice", "bob", "Subj", "v1")
        await mgr.save_draft("alice", "bob", "Subj", "v2", draft_filename=rec1.filename)
        staging = patch_comms_base / "alice" / "comms" / "staging"
        content = (staging / rec1.filename).read_text()
        assert "v2" in content


class TestPromoteDraft:
    @pytest.mark.anyio
    async def test_sends_and_deletes_draft(self, patch_comms_base: Path):
        mgr = _setup_user(patch_comms_base, "alice")
        draft = await mgr.save_draft("alice", "bob", "Subj", "Body")
        staging = patch_comms_base / "alice" / "comms" / "staging"
        assert (staging / draft.filename).exists()
        sent = await mgr.promote_draft("alice", draft.filename, ["bob"])
        assert not (staging / draft.filename).exists()
        assert (patch_comms_base / "bob" / "comms" / "inbound" / sent.filename).exists()

    @pytest.mark.anyio
    async def test_missing_draft_raises(self, patch_comms_base: Path):
        mgr = _setup_user(patch_comms_base, "alice")
        with pytest.raises(NotFoundError, match="DRAFT_NOT_FOUND"):
            await mgr.promote_draft("alice", "ghost.md", ["bob"])
