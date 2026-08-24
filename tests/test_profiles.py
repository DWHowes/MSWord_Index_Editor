r"""
A style profile that survives closing the window. Step 4.

The store is a JSON file and there is not much to it, so what is worth pinning
is the handful of places where it could be wrong **quietly**: a partial write
losing every profile the indexer has authored, a kind from a later version
being silently renamed to something they never said, and an undecided style
being written in as though it were a decision.
"""

import json

import pytest

from wordindex.profiles import (
    STORE_ENV, STORE_VERSION, forget_profile, from_dict, known_documents,
    load_profile, save_profile, store_path, to_dict,
)
from wordindex.reader import BODY, HEADING, StyleProfile


@pytest.fixture(autouse=True)
def store(tmp_path, monkeypatch):
    """Never the real one: a test must not touch the indexer's own profiles."""
    path = tmp_path / "profiles.json"
    monkeypatch.setenv(STORE_ENV, str(path))
    return path


@pytest.fixture
def profile():
    return StyleProfile(name="a book",
                        kinds={"0101Para": BODY, "0201A": HEADING},
                        levels={"0201A": 2})


class TestARoundTrip:
    def test_a_profile_comes_back_as_it_went_in(self, tmp_path, profile):
        book = tmp_path / "book.docx"
        save_profile(book, profile)
        assert load_profile(book) == profile

    def test_an_unprofiled_document_is_none_not_empty(self, tmp_path):
        """
        None and an empty profile are different answers. None means nobody has
        decided; empty would mean somebody decided nothing means anything.
        """
        assert load_profile(tmp_path / "never seen.docx") is None

    def test_two_documents_keep_their_own(self, tmp_path, profile):
        one, two = tmp_path / "one.docx", tmp_path / "two.docx"
        save_profile(one, profile)
        save_profile(two, StyleProfile(name="other", kinds={"X": BODY}))
        assert load_profile(one).name == "a book"
        assert load_profile(two).name == "other"

    def test_saving_again_replaces(self, tmp_path, profile):
        book = tmp_path / "book.docx"
        save_profile(book, profile)
        save_profile(book, StyleProfile(name="second thoughts",
                                        kinds={"0101Para": HEADING}))
        assert load_profile(book).kinds == {"0101Para": HEADING}
        assert len(known_documents()) == 1

    def test_forgetting(self, tmp_path, profile):
        book = tmp_path / "book.docx"
        save_profile(book, profile)
        forget_profile(book)
        assert load_profile(book) is None

    def test_forgetting_what_was_never_there(self, tmp_path):
        forget_profile(tmp_path / "nothing.docx")          # must not raise


class TestTheStoreIsNotGuessedAt:
    def test_a_missing_store_is_not_an_error(self, tmp_path):
        assert load_profile(tmp_path / "book.docx") is None
        assert known_documents() == ()

    def test_a_corrupt_store_is_not_an_error(self, store, tmp_path):
        store.write_text("{not json at all", encoding="utf-8")
        assert load_profile(tmp_path / "book.docx") is None

    def test_a_store_from_a_later_version_is_left_alone(self, store, tmp_path):
        """
        Reading half a profile the indexer cannot see would be a wrong answer.
        Reading none of it is only a nuisance.
        """
        store.write_text(json.dumps({
            "version": STORE_VERSION + 1,
            "profiles": {str(tmp_path / "book.docx"): {"kinds": {"A": BODY}}},
        }), encoding="utf-8")
        assert load_profile(tmp_path / "book.docx") is None

    def test_a_kind_this_version_does_not_have_is_dropped(self):
        """
        Dropped, never renamed. A style left out reads as UNKNOWN and is
        reported unplaced, which is true; mapping it to body text would be
        inventing an answer the indexer never gave.
        """
        back = from_dict({"name": "x",
                          "kinds": {"A": BODY, "B": "sidebar_from_2027"}})
        assert back.kinds == {"A": BODY}

    def test_a_write_leaves_no_partial_file_behind(self, store, tmp_path,
                                                   profile):
        save_profile(tmp_path / "book.docx", profile)
        assert store.exists()
        assert not list(store.parent.glob("*.partial"))

    def test_the_version_is_stamped(self, store, tmp_path, profile):
        save_profile(tmp_path / "book.docx", profile)
        assert json.loads(store.read_text(encoding="utf-8"))["version"] == \
            STORE_VERSION


class TestTheStoreLocation:
    def test_the_override_wins(self, store):
        assert store_path() == store

    def test_there_is_a_default_without_qt_or_an_override(self, monkeypatch):
        monkeypatch.delenv(STORE_ENV, raising=False)
        assert store_path().name == "style_profiles.json"


class TestEncoding:
    def test_levels_survive_as_integers(self, profile):
        assert to_dict(profile)["levels"] == {"0201A": 2}

    def test_a_level_that_is_not_a_number_is_dropped(self):
        back = from_dict({"kinds": {"A": HEADING}, "levels": {"A": "deep"}})
        assert back.kinds == {"A": HEADING} and back.levels == {}

    def test_something_that_is_not_a_profile_at_all(self):
        assert from_dict(None) is None
        assert from_dict({"name": "no kinds here"}) is None
