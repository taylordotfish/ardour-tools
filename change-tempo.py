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

import math
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


def get_midi_routes(session):
    return session.findall(".//Route[@default-type='midi']")


def get_automation_lists(route):
    return route.findall(".//AutomationList")


def shift_events(automation_list, multiplier):
    events_elem = automation_list.find("events")
    if events_elem is None:
        return

    events = parse_events(events_elem.text)
    for i, (samples, value) in enumerate(events):
        samples = int(round(samples * multiplier))
        events[i] = (samples, value)

    events_elem.text = "".join(
        "{} {}\n".format(samples, value) for samples, value in events
    )


def parse_events(events_text):
    events = []
    for line in events_text.splitlines():
        if not line:
            continue
        try:
            samples, value = line.split()
            samples = int(samples)
        except ValueError as e:
            raise ExitError(
                "Could not parse automation event line: {}".format(line),
            ) from e
        events.append((samples, value))
    return events


def parse_bpm(bpm_str):
    try:
        bpm = float(bpm_str)
    except ValueError as e:
        raise ExitError("Invalid BPM: '{}'".format(bpm_str)) from e
    if bpm <= 0 or not math.isfinite(bpm):
        raise ExitError(
            "BPM must be a positive number: '{}'".format(bpm_str),
        )
    return bpm


def run(argv):
    if len(argv) != 4:
        sys.exit(
            "Usage: change-tempo.py <ardour-project-file> <old-bpm> <new-bpm>",
        )

    path, old_bpm, new_bpm = argv[1:]
    old_bpm = parse_bpm(old_bpm)
    new_bpm = parse_bpm(new_bpm)

    tree = read_xml(path)
    session = get_session(tree)
    enforce_version(session)

    multiplier = old_bpm / new_bpm
    for route in get_midi_routes(session):
        for automation_list in get_automation_lists(route):
            shift_events(automation_list, multiplier)
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
