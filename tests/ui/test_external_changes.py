r"""
A manuscript changed underneath us, and the session log. Step 11e.

**This is the one guard on scope §2's promise.** A manuscript open here can be
edited in Word at the same time, and the anchors this application holds point
into the version it read. Writing our entries over somebody else's edit would
hand the publisher back a file differing from theirs by more than the added
fields, which is the one thing the whole application is built not to do.

D7's rule, in three parts: a **named notice**, a **refusal to save that
document**, and an offer to reopen that says **what reopening costs**.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from docx_fixtures import sample_document                      # noqa: E402


@pytest.fixture
def window(qt_app):
    from wordindex.ui.main_window import MainWindow

    return MainWindow()


@pytest.fixture
def project(window, tmp_path):
    from wordindex.project import Project

    paths = [sample_document(tmp_path / f"{n:02d}_Chapter {n}.docx")
             for n in (1, 2)]
    window.open_project(Project(name="Book", documents=tuple(paths)))
    return window, paths


def edit_something(window, document, which=0):
    """
    Stage one real change against a document.

    ``which`` picks a different entry each time, because editing the same one
    twice is a refused edit: the second edit carries the instruction the first
    one has already replaced.

    **Entries whose id appears twice in the project are skipped**, and the
    reason is the fixture rather than the application: `sample_document`
    writes one field with a hard-coded `wim_` bookmark, so two documents built
    from it share that entry's id. `OpenProject` maps an id to one document,
    so an edit aimed at the second lands on the first's record and is refused
    by the backend's own before-guard. Two real manuscripts can collide the
    same way if one was copied from the other after this application had
    written anchors into it, and the failure is a refusal with a message
    rather than a wrong write; see the changelog for step 11e.
    """
    ids = [r.entry_id for r in window._references]
    entries = [r for r in window._references
               if window.session.document_of(r.entry_id) == document
               and ids.count(r.entry_id) == 1]
    entry = entries[which]
    window._edit_entry(entry.entry_id, f'XE "Changed here {which}"')
    return entry


class TestWatching:
    def test_every_document_of_the_project_is_watched(self, project):
        window, paths = project
        watched = {Path(p) for p in window.watcher.watched_paths()}
        assert watched == {Path(p) for p in paths}

    def test_closing_the_project_stops_watching(self, project):
        window, _paths = project
        window.close_project()
        assert window.watcher.watched_paths() == []


class TestWhenOneChanges:
    def test_it_is_named_rather_than_swallowed(self, project):
        window, paths = project
        window._document_changed_on_disk(str(paths[1]))
        assert paths[1].name in window.notice.text()
        assert paths[1].name in window.statusBar().currentMessage()

    def test_the_notice_says_what_is_at_stake(self, project):
        """
        A count, not "some changes". An indexer who has marked thirty entries
        in that chapter is being asked a different question from one who has
        marked none.
        """
        window, paths = project
        edit_something(window, paths[1])
        window._document_changed_on_disk(str(paths[1]))
        assert "1 change" in window.notice.text()

    def test_the_tab_says_so_too(self, project):
        window, paths = project
        window.show_document(paths[1])
        window._document_changed_on_disk(str(paths[1]))
        index = window.tabs.indexOf(window.tabs.view_for(paths[1]))
        assert "changed on disk" in window.tabs.tabText(index)

    def test_a_file_that_is_not_in_the_project_is_ignored(self, project,
                                                          tmp_path):
        window, _paths = project
        window._document_changed_on_disk(str(tmp_path / "somebody_elses.docx"))
        assert window._changed_on_disk == set()


class TestSavingRefuses:
    def test_the_changed_document_is_not_written(self, project, monkeypatch):
        window, paths = project
        edit_something(window, paths[0])
        edit_something(window, paths[1])
        window._document_changed_on_disk(str(paths[1]))

        said = {}
        monkeypatch.setattr("PySide6.QtWidgets.QMessageBox.warning",
                            lambda parent, title, text, *a, **k: said.update(
                                {"title": title, "text": text}))
        written = {}
        real_save = window.session.save

        def watched_save(skip=()):
            written["skipped"] = set(skip)
            return real_save(skip=skip)

        monkeypatch.setattr(window.session, "save", watched_save)
        window.save()

        assert written["skipped"] == {paths[1]}
        assert paths[1].name in said["text"]
        assert "1 change" in said["text"]

    def test_the_others_are_saved(self, project, monkeypatch):
        window, paths = project
        edit_something(window, paths[0])
        window._document_changed_on_disk(str(paths[1]))
        monkeypatch.setattr("PySide6.QtWidgets.QMessageBox.warning",
                            lambda *a, **k: None)

        window.save()

        assert paths[0] not in window._unsaved

    def test_our_own_save_does_not_report_itself(self, project, monkeypatch):
        """
        Saving writes a temporary file and moves it into place, which is
        exactly what an external editor's save looks like. Without the pause,
        every document we wrote would report itself as changed by somebody
        else and the next save would be refused for the whole book.
        """
        window, paths = project
        edit_something(window, paths[0])
        paused = []
        monkeypatch.setattr(window.watcher, "pause_watching",
                            lambda: paused.append("paused"))
        monkeypatch.setattr(window.watcher, "resume_watching",
                            lambda: paused.append("resumed"))

        window.save()

        assert paused == ["paused", "resumed"]


class TestReopening:
    def test_it_reads_the_file_as_it_now_is(self, project, monkeypatch):
        window, paths = project
        edit_something(window, paths[1])
        window._document_changed_on_disk(str(paths[1]))

        # Somebody else's version, with a different entry in it.
        sample_document(paths[1])

        window._reopen(paths[1])

        assert paths[1] not in window._changed_on_disk
        assert paths[1] not in window._unsaved
        assert not any(r.heading_raw.startswith("Changed here")
                       for r in window._references)

    def test_only_that_document_loses_anything(self, project):
        """
        Every document has its own backend, so reopening one is a decision an
        indexer can take a chapter at a time.
        """
        window, paths = project
        edit_something(window, paths[0])
        edit_something(window, paths[1])
        window._document_changed_on_disk(str(paths[1]))

        window._reopen(paths[1])

        assert paths[0] in window._unsaved
        assert any(r.heading_raw.startswith("Changed here")
                   for r in window._references
                   if window.session.document_of(r.entry_id) == paths[0])

    def test_the_gesture_is_dead_until_something_changes(self, project):
        window, paths = project
        assert not window.reopen_action.isEnabled()
        window._document_changed_on_disk(str(paths[1]))
        assert window.reopen_action.isEnabled()

    def test_cancelling_keeps_the_document_and_its_changes(self, project,
                                                           monkeypatch):
        window, paths = project
        edit_something(window, paths[1])
        window._document_changed_on_disk(str(paths[1]))

        from PySide6.QtWidgets import QMessageBox

        monkeypatch.setattr(QMessageBox, "question",
                            lambda *a, **k: QMessageBox.StandardButton.Cancel)
        window.reopen_changed_documents()

        assert paths[1] in window._changed_on_disk
        assert paths[1] in window._unsaved

    def test_the_question_says_what_it_costs(self, project, monkeypatch):
        window, paths = project
        edit_something(window, paths[1], 0)
        edit_something(window, paths[1], 1)
        window._document_changed_on_disk(str(paths[1]))

        asked = {}

        from PySide6.QtWidgets import QMessageBox

        def question(parent, title, text, buttons):
            asked["text"] = text
            return QMessageBox.StandardButton.Cancel

        monkeypatch.setattr(QMessageBox, "question", question)
        window.reopen_changed_documents()

        assert "2 changes" in asked["text"] and "lost" in asked["text"]


class TestTheSessionLog:
    def test_it_goes_beside_this_application_s_own_data(self, tmp_path,
                                                        monkeypatch):
        """
        **Not under the project**, which is the rule in the LaTeX editor and
        the wrong one here: a Word project folder is the publisher's, and what
        goes back to them should differ from what they sent by the added
        fields alone.
        """
        from wordindex import session_log

        monkeypatch.delenv(session_log.LOG_ENV, raising=False)
        monkeypatch.setattr("wordindex.profiles.store_path",
                            lambda: tmp_path / "data" / "style_profiles.json")

        assert session_log.log_root() == tmp_path / "data" / "session_logs"

    def test_it_can_be_pointed_somewhere_else(self, tmp_path, monkeypatch):
        from wordindex import session_log

        monkeypatch.setenv(session_log.LOG_ENV, str(tmp_path / "logs"))
        assert session_log.log_root() == tmp_path / "logs"

    def test_a_log_that_cannot_be_written_does_not_stop_the_session(
            self, monkeypatch, capsys):
        """
        An installed copy can find its data directory read-only. An indexer
        meeting a dead application with no window and no message has no way to
        find out why.
        """
        from wordindex import session_log

        def unwritable():
            raise OSError("the data directory is read-only")

        monkeypatch.setattr(session_log, "log_root", unwritable)
        assert session_log.start_logging() is None
        assert "Not logging this session" in capsys.readouterr().out

    def test_it_writes_a_file_when_it_can(self, tmp_path, monkeypatch):
        from wordindex import session_log

        monkeypatch.setenv(session_log.LOG_ENV, str(tmp_path / "logs"))
        logger = session_log.start_logging()
        try:
            assert logger is not None
            print("something worth keeping")
        finally:
            logger.stop_intercept()

        written = list((tmp_path / "logs").glob("session_*.log"))
        assert written and "something worth keeping" in \
            written[0].read_text(encoding="utf-8", errors="replace")
