r"""
A style profile that survives closing the window. Step 4.

The store is a JSON file and there is not much to it, so what is worth pinning
is the handful of places where it could be wrong **quietly**: a partial write
losing every profile the indexer has authored, a kind from a later version
being silently renamed to something they never said, and an undecided style
being written in as though it were a decision.
"""

import json
import os
import sys
from pathlib import Path

import pytest

from wordindex import profiles
from wordindex.profiles import (
    APP_DIRECTORY, STORE_ENV, STORE_VERSION, forget_profile, forget_project,
    from_dict, known_documents, known_projects, legacy_store_paths,
    load_profile, load_project, save_profile, save_project, store_path,
    to_dict,
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
    r"""
    ***Where this file lives was wrong twice over until 10 September 2026.***

    It resolved Qt's `AppDataLocation`, which is **Roaming** on Windows while
    the suite's shared store is deliberately Local; and Qt builds that path
    out of the organisation and application names, *which this application
    never set*, so it resolved to the running executable's basename. A source
    run wrote to a folder named after the interpreter and a frozen build would
    have written to one named after the exe, with no vendor folder and no
    agreement between them. The indexer's own profiles were found in the
    first.
    """

    def test_the_override_wins(self, store):
        assert store_path() == store

    def test_there_is_a_default_without_qt_or_an_override(self, monkeypatch):
        monkeypatch.delenv(STORE_ENV, raising=False)
        assert store_path().name == "style_profiles.json"

    def test_it_sits_in_the_suite_folder_under_this_application_name(self, monkeypatch):
        monkeypatch.delenv(STORE_ENV, raising=False)

        assert store_path().parent.name == APP_DIRECTORY
        assert store_path().parent.parent.name == "DH Indexing"

    def test_it_is_local_rather_than_roaming(self, monkeypatch):
        monkeypatch.delenv(STORE_ENV, raising=False)
        if os.name != "nt":
            pytest.skip("Roaming and Local are a Windows distinction")

        assert "Roaming" not in str(store_path())
        assert str(store_path()).startswith(os.environ["LOCALAPPDATA"])

    def test_it_does_not_depend_on_the_application_having_a_name(self, monkeypatch):
        """
        The defect's mechanism, closed at the source rather than only at the
        call that set the names: a store that asks Qt where it lives is a
        store whose location depends on a startup sequence completing.
        """
        monkeypatch.delenv(STORE_ENV, raising=False)
        resolved = str(store_path())

        assert "python" not in resolved.lower().rsplit("dh indexing", 1)[-1]
        assert Path(sys.executable).stem not in resolved


class TestAdoptingAnOlderStore:
    def test_profiles_written_to_the_old_place_are_still_found(
            self, tmp_path, monkeypatch, profile):
        """
        The move must not lose a publisher's vocabulary. An installed copy has
        been writing to one of the previous locations since this application
        shipped, and 1,910 bytes of the indexer's own were in one of them on
        the day this changed.
        """
        previous = tmp_path / "old_place" / "style_profiles.json"
        current = tmp_path / "new_place" / "style_profiles.json"
        monkeypatch.delenv(STORE_ENV, raising=False)

        monkeypatch.setattr(profiles, "store_path", lambda: previous)
        monkeypatch.setattr(profiles, "legacy_store_paths", lambda: ())
        save_profile("C:/book.docx", profile)

        monkeypatch.setattr(profiles, "store_path", lambda: current)
        monkeypatch.setattr(profiles, "legacy_store_paths", lambda: (previous,))

        assert load_profile("C:/book.docx") is not None

    def test_the_current_store_wins_when_both_exist(self, tmp_path, monkeypatch, profile):
        previous = tmp_path / "old_place" / "style_profiles.json"
        current = tmp_path / "new_place" / "style_profiles.json"
        monkeypatch.delenv(STORE_ENV, raising=False)
        monkeypatch.setattr(profiles, "legacy_store_paths", lambda: ())

        monkeypatch.setattr(profiles, "store_path", lambda: previous)
        save_profile("C:/old.docx", profile)
        monkeypatch.setattr(profiles, "store_path", lambda: current)
        save_profile("C:/new.docx", profile)

        monkeypatch.setattr(profiles, "legacy_store_paths", lambda: (previous,))

        assert load_profile("C:/new.docx") is not None
        assert load_profile("C:/old.docx") is None

    def test_the_old_file_is_read_and_not_removed(self, tmp_path, monkeypatch, profile):
        previous = tmp_path / "old_place" / "style_profiles.json"
        current = tmp_path / "new_place" / "style_profiles.json"
        monkeypatch.delenv(STORE_ENV, raising=False)

        monkeypatch.setattr(profiles, "store_path", lambda: previous)
        monkeypatch.setattr(profiles, "legacy_store_paths", lambda: ())
        save_profile("C:/book.docx", profile)

        monkeypatch.setattr(profiles, "store_path", lambda: current)
        monkeypatch.setattr(profiles, "legacy_store_paths", lambda: (previous,))
        load_profile("C:/book.docx")

        assert previous.exists()

    def test_an_explicit_store_adopts_nothing(self, store):
        """
        An explicit path is an explicit answer. Reading somewhere the caller
        did not name into it would be the opposite of what they asked for, and
        it is what would put the indexer's real profiles into a test run.
        """
        assert legacy_store_paths() == ()


class TestEncoding:
    def test_levels_survive_as_integers(self, profile):
        assert to_dict(profile)["levels"] == {"0201A": 2}

    def test_a_level_that_is_not_a_number_is_dropped(self):
        back = from_dict({"kinds": {"A": HEADING}, "levels": {"A": "deep"}})
        assert back.kinds == {"A": HEADING} and back.levels == {}

    def test_something_that_is_not_a_profile_at_all(self):
        assert from_dict(None) is None
        assert from_dict({"name": "no kinds here"}) is None


class TestProjects:
    """
    Projects live in the same store as profiles, for the same reason: **the
    manuscript's folder is the publisher's**, and a project file dropped in
    there would be one more thing for editorial staff to wonder about.
    """

    def test_a_project_round_trips_in_order(self, tmp_path):
        documents = [tmp_path / "c.docx", tmp_path / "a.docx",
                     tmp_path / "b.docx"]
        save_project("Collection", documents)
        assert list(load_project("Collection")) == documents

    def test_an_unknown_project_is_none(self):
        assert load_project("never named") is None

    def test_projects_and_profiles_share_one_file(self, tmp_path, profile):
        """
        The bug this guards: a writer that read only its own half of the store
        would drop the other every time it saved.
        """
        save_profile(tmp_path / "book.docx", profile)
        save_project("Collection", [tmp_path / "book.docx"])
        assert load_profile(tmp_path / "book.docx") == profile
        assert load_project("Collection") is not None

    def test_saving_a_profile_does_not_lose_the_projects(self, tmp_path,
                                                         profile):
        save_project("Collection", [tmp_path / "one.docx"])
        save_profile(tmp_path / "other.docx", profile)
        assert load_project("Collection") is not None

    def test_a_project_key_is_not_resolved_as_a_path(self, profile):
        """
        `Project.key` is `project:Some Book` for anything larger than one
        document. Resolving that would file every project under whatever
        folder the application happened to start in.
        """
        save_profile("project:the Palgrave collection", profile)
        assert load_profile("project:the Palgrave collection") == profile

    def test_documents_that_have_moved_are_still_returned(self, tmp_path):
        """
        Dropping them here would leave the indexer with a project that quietly
        shrank. The caller opens what it can and reports what it could not.
        """
        gone = tmp_path / "not here.docx"
        save_project("Collection", [gone])
        assert list(load_project("Collection")) == [gone]

    def test_forgetting_one(self, tmp_path):
        save_project("Collection", [tmp_path / "a.docx"])
        forget_project("Collection")
        assert load_project("Collection") is None
        assert known_projects() == ()
