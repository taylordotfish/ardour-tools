ardour-tools
============

Various tools for working with Ardour session files.

Before running any of these scripts, it is highly recommended that you back up
your project files. These scripts operate directly on session files and do not
create any copies.

Scripts
-------

### change-tempo.py

When a project’s tempo is changed, MIDI automation doesn’t scale with the new
tempo. This script fixes that by scaling all automation in MIDI tracks.

### fix-unused-playlists.py

As of commit 2018-02-02 (commit ``3aacdd79ae7537f507e6ee86ad6ffb85bc55bdfc``),
unused playlists aren’t completely removed when the “Clean-up Unused Sources”
feature is run. This script removes those unused playlists.

License
-------

This project is licensed under the GNU General Public License, version 3 or
any later version. See [LICENSE].

This README file has been released to the public domain using [CC0].

[LICENSE]: LICENSE
[CC0]: https://creativecommons.org/publicdomain/zero/1.0/
