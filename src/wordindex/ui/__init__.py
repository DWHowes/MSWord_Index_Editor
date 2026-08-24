r"""
The Word editor's own windows.

**Word-specific only.** The entry table, the index tree, search, preferences,
the help viewer, the theme and the About box all come from
`bookindexcore.ui`; what lives here is what a Word manuscript needs and no
other host does.

This directory exists because step 2 produced two modules at once -- a window
and the view inside it -- and the scope's rule is that a concern is promoted
when it has two, not before.
"""
