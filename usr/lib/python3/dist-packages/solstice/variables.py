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
#cssOptions = ["connectedtabs"]
cssPath = "%s/.config/solstice" % os.path.expanduser("~")
#Developer options
applicationsDirectory = os.path.expanduser("~") + "/.local/share/applications"
solsticeProfilesDirectory = os.path.expanduser("~") + "/.local/share/solstice"
solsticeLastUpdated = 20241211
