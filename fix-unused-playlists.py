#!/usr/bin/env python3
# Copyright (C) 2018 taylor.fish <contact@taylor.fish>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys

DEBUG = False
FORCE_SECURE = False

try:
    import defusedxml.ElementTree as ElementTree
except ImportError:
    if FORCE_SECURE:
        sys.exit("Error: The 'defusedxml' package must be installed.")
    import xml.etree.ElementTree as ElementTree


class ExitError(Exception):
    def __init__(self, message):
        super().__init__(message)

    @property
    def message(self):
        return self.args[0]


def read_xml(path):
    try:
        return ElementTree.parse(path)
    except FileNotFoundError as e:
        raise ExitError("File not found: '{}'".format(path)) from e


def get_session(tree):
    return tree.getroot()


def enforce_version(session):
    version_elem = session.find("ProgramVersion")
    if version_elem is None:
        raise ExitError("Could not get version from project file.")

    version_str = version_elem.attrib.get("modified-with")
    if version_str is None:
        version_str = version_elem.attrib.get("created-with")
    if version_str is None:
        raise ExitError("Could not get version from project file.")
    if not version_str.startswith("Ardour 6."):
        raise ExitError("Only Ardour 6 project files are supported.")


def is_playlist_used(playlist, session):
    try:
        playlist_id = playlist.attrib["id"]
    except KeyError:
        return True
    if session.find(".//Route[@midi-playlist={!r}]".format(playlist_id)):
        return True
    if session.find(".//Route[@audio-playlist={!r}]".format(playlist_id)):
        return True
    orig_track_id = playlist.attrib.get("orig-track-id")
    if orig_track_id is None:
        return False
    return bool(session.find(".//Route[@id={!r}]".format(orig_track_id)))


def get_playlists(session):
    return session.findall(".//Playlist")


def get_unused_playlists(playlists, session):
    return [p for p in playlists if not is_playlist_used(p, session)]


def remove_unused_playlist(playlist, session):
    orig_track_id = playlist.attrib.get("orig-track-id")
    try:
        playlist_id = playlist.attrib["id"]
    except KeyError as e:
        raise ExitError("Cannot remove playlist without an ID.") from e
    parent = session.find(".//Playlist[@id='{}']/..".format(playlist_id))
    parent.remove(playlist)
    if orig_track_id is None:
        return

    obj_query = "Object[@id={!r}]".format("strip " + orig_track_id)
    obj_parents = session.findall(".//{}/..".format(obj_query))
    for obj_parent in obj_parents:
        objs = obj_parent.findall(obj_query)
        for obj in objs:
            obj_parent.remove(obj)


def run(argv):
    if len(argv) != 2:
        sys.exit(
            "Usage: fix-unused-playlists.py <ardour-project-file>",
        )

    path = argv[1]
    tree = read_xml(path)
    session = get_session(tree)
    enforce_version(session)

    playlists = get_playlists(session)
    unused_playlists = get_unused_playlists(playlists, session)
    for playlist in unused_playlists:
        remove_unused_playlist(playlist, session)
    tree.write(path, xml_declaration=True, encoding="utf-8")


def main(argv):
    try:
        run(argv)
    except ExitError as e:
        print(e.message, file=sys.stderr)
        if DEBUG:
            raise
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
