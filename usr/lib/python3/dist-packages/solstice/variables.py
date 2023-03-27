# This file is part of Feren Solstice.
#
# Copyright 2020-2023 Dominic Hayes

import json
import os

sources = {}
with open("/usr/share/solstice/sources-info/data.json", 'r') as fp:
    sources = json.loads(fp.read())
#Developer options
applications_directory = os.path.expanduser("~") + "/.local/share/applications"
solstice_profiles_directory = os.path.expanduser("~") + "/.local/share/solstice"
