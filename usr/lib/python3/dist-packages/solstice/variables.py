# This file is part of Feren Solstice.
#
# Copyright 2020-2023 Dominic Hayes

import json
import os

sources = {}
unavailable = {}
with open("/usr/share/solstice/info/data.json", 'r') as fp:
    sources = json.loads(fp.read())
with open("/usr/share/solstice/info/unavailable.json", 'r') as fp:
    unavailable = json.loads(fp.read())
#Developer options
applications_directory = os.path.expanduser("~") + "/.local/share/applications"
solstice_profiles_directory = os.path.expanduser("~") + "/.local/share/solstice"
solstice_lastupdated = 20230929
