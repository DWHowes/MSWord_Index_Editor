r"""
Where a heading's language comes from, and where it goes when it is stated.

Three sources, most specific first, and the order is the design: **this
project's own record**, because a book is entitled to read a name differently
from the last one; **the shared name database**, which outlives any one
project so that classifying a name is work done once; and the project default,
which the cascade applies itself.

Writing goes to the first two **together**. An indexer classifying a name has
answered both questions at once, and writing only one of them is how the two
come to disagree -- a defect the LaTeX editor had and fixed, and the reason
this test exists here before anybody has had the chance to repeat it.
"""

import pytest

from bookindexcore.style.languages import UNSTATED

from wordindex import profiles
from wordindex.names import NameDesk


@pytest.fixture(autouse=True)
def store(tmp_path, monkeypatch):
    """The profile store, isolated. It holds the per-project languages."""
    monkeypatch.setenv(profiles.STORE_ENV,
                       str(tmp_path / "style_profiles.json"))
    return tmp_path


class FakeService:
    """The name database half, without one."""

    def __init__(self):
        self.languages = {}
        self.closed = False

    def remembered_language(self, name):
        return self.languages.get(name, UNSTATED)

    def remember_language(self, name, language):
        self.languages[name] = language

    def close(self):
        self.closed = True


@pytest.fixture
def desk():
    service = FakeService()
    made = NameDesk(project_key=lambda: "project:Sample", service=service)
    return made, service


class TestWhereTheLanguageComesFrom:

    def test_nobody_has_said(self, desk):
        made, _service = desk
        assert made.heading_language("Nur al-Din Zangi") == UNSTATED

    def test_the_name_database_answers_when_the_project_has_not(self, desk):
        made, service = desk
        service.languages["Hugo Claus"] = "nl"
        assert made.heading_language("Hugo Claus") == "nl"

    def test_this_project_overrules_the_name_database(self, desk):
        """
        The same word can be a different person in a different book, which is
        why the project comes first rather than the store that outlives it.
        """
        made, service = desk
        service.languages["Claus"] = "nl"
        profiles.set_heading_language("project:Sample", "Claus", "de")

        assert made.heading_language("Claus") == "de"

    def test_another_project_is_not_this_one(self, desk):
        made, _service = desk
        profiles.set_heading_language("project:Other", "Claus", "de")
        assert made.heading_language("Claus") == UNSTATED

    def test_a_failure_is_not_an_answer(self, desk, monkeypatch):
        """
        A language nobody can look up is no reason to refuse to invert a name.
        """
        made, _service = desk

        def _explode(*_args, **_kwargs):
            raise RuntimeError("the store is gone")

        monkeypatch.setattr(profiles, "heading_language", _explode)
        assert made.heading_language("Claus") == UNSTATED


class TestStatingIt:

    def test_it_reaches_both_stores(self, desk):
        made, service = desk
        made.set_heading_language("Nur al-Din Zangi", "ar")

        assert service.languages["Nur al-Din Zangi"] == "ar"
        assert profiles.heading_language(
            "project:Sample", "Nur al-Din Zangi") == "ar"

    def test_the_two_writes_do_not_depend_on_each_other(self, desk, monkeypatch):
        """
        The stores fail for unrelated reasons -- no project open, no name
        database -- and one being unavailable is no reason to withhold the
        decision from the other.
        """
        made, service = desk

        def _explode(*_args, **_kwargs):
            raise RuntimeError("no project is open")

        monkeypatch.setattr(profiles, "set_heading_language", _explode)
        made.set_heading_language("Nur al-Din Zangi", "ar")

        assert service.languages["Nur al-Din Zangi"] == "ar"

    def test_clearing_it_removes_the_record(self, desk):
        """
        Three states, not four: *this book says X*, *this book has not said*,
        and the database's answer. A stored empty string would read as the
        second and behave as a decision.
        """
        made, _service = desk
        made.set_heading_language("Claus", "nl")
        made.set_heading_language("Claus", UNSTATED)

        assert profiles.project_languages("project:Sample") == {}

    def test_the_heading_is_matched_the_way_the_tables_match(self, desk):
        """
        Folded, so a heading recorded once is found again whatever the case.
        """
        made, _service = desk
        made.set_heading_language("Nur al-Din Zangi", "ar")
        assert made.heading_language("nur al-din zangi") == "ar"


class TestTheProjectKeyIsRead(object):

    def test_it_follows_the_open_project(self):
        """
        A key read once at construction files the second book's decisions
        under the first book's name, which is why it is a callable.
        """
        current = {"key": "project:One"}
        made = NameDesk(project_key=lambda: current["key"],
                        service=FakeService())

        made.set_heading_language("Claus", "nl")
        current["key"] = "project:Two"

        # The project record went to the book that was open, and the second
        # book has none of its own. What it still has is the name database,
        # which is the whole point of writing both: a classification made once
        # arrives in the next volume.
        assert profiles.project_languages("project:One") != {}
        assert profiles.project_languages("project:Two") == {}
        assert made.heading_language("Claus") == "nl"
