# This file is part of Feren Solstice.
#
# Copyright 2020-2023 Dominic Hayes

from . import utils
import os
import subprocess
import gettext
gettext.install("solstice-python", "/usr/share/locale", names="ngettext")
import json
import shutil
from datetime import datetime
import ast
import signal
import time

class variables:
    #Developer options
    applications_directory = os.path.expanduser("~") + "/.local/share/applications"
    default_ice_directory = os.path.expanduser("~") + "/.local/share/solstice"
    icevivaldiprefix = "vivaldisolstice:"

class SolsticeModuleException(Exception):
    pass

class main:
    def __init__(self):
        self.refresh_memory()

    def refresh_memory(self): # Function to refresh some memory values
        self.sources_storage = {}

        with open("/usr/share/solstice/sources-info/data.json", 'r') as fp:
            self.sources_storage = json.loads(fp.read())

    #### PROFILE EXECUTION
    def run_profile(self, itemid, profileid, browser, browsertype, website, wmclass, nohistory=False, forcedark=False, closecallback=None):
        #string, string, string, string, bool
        profiledir = "{0}/{1}/{2}".format(default_ice_directory, itemid, profileid)

        if browser in self.sources_storage["browsers"]:
            commandtorun = self.sources_storage["browsers"][browser]["command"]
            if forcedark == True: #TODO: Check FreeDesktop preference as well
                try:
                    commandtorun = self.sources_storage["browsers"][browser]["commanddarkmode"]
                except:
                    print(_("Failed to start browser in dark mode, starting the browser normally..."))
            piececount = 0 #for loop right below
            while piececount < len(commandtorun):
                #Translate arguments
                commandtorun[piececount] = commandtorun[piececount].replace(
                    "%WEBSITEURL%", website).replace(
                    "%WINCLASS%", wmclass).replace(
                    "%PROFILEDIR%", profiledir)
                piececount += 1

            ssbproc = subprocess.Popen(commandtorun, close_fds=True)
        else:
            raise SolsticeModuleException(_("Cannot find information about the specified browser to launch"))

        #Check there's a note about a process having ran, and if so if the process is running
        if os.path.isfile(profiledir + "/.storium-active-pid"):
            with open(profiledir + "/.storium-active-pid", 'r') as pidfile:
                lastpid = pidfile.readline()
            try:
                lastpid = int(lastpid)
                try:
                    os.kill(lastpid, 0) #Send a You There? to the PID identified
                except:
                    os.remove(profiledir + "/.storium-active-pid") #The PID doesn't exist
            except:
                os.remove(profiledir + "/.storium-active-pid")
        #Tell Storium that the process's running (prevents updates while running, and prevents uninstallation leftovers with Storium module)
        if not os.path.isfile(profiledir + "/.storium-active-pid"):
            with open(profiledir + "/.storium-active-pid", 'w') as pidfile:
                pidfile.write(str(ssbproc.pid))

        if nohistory == True:
            if not closecallback == None:
                closecallback()

            #FIXME: We need a better way of doing this.
            time.sleep(16)
            if browsertype == "chromium":
                if os.path.isfile(profiledir + "/Default/History"):
                    os.remove(profiledir + "/Default/History")
                if os.path.isfile(profiledir + "/Default/History-journal"):
                    os.remove(profiledir + "/Default/History-journal")
                if os.path.isdir(profiledir + "/Default/Sessions"):
                    shutil.rmtree(profiledir + "/Default/Sessions")
            elif browsertype == "firefox":
                pass #TODO

    #### PROFILE CREATION / UPDATING
    def update_profile(self, iteminfo, profilename, profileid, darkmode, nocache):
        #NOTE: Also used to generate a new profile
        profilepath = "{0}/{1}/{2}".format(variables.default_ice_directory, iteminfo["id"], profileid)

        #Generate profile directory if it does not exist yet
        if not os.path.isdir(profilepath):
            utils.create_profile_folder(iteminfo["id"], profileid)

        if iteminfo["browsertype"] == "chromium":
            from . import chromium
            chromium.update_profile(iteminfo, profilename, profilepath, darkmode, nocache)
        elif iteminfo["browsertype"] == "firefox":
            from . import firefox
            firefox.update_profile(iteminfo, profilename, profilepath, darkmode, nocache)
        #If Flatpak, grant access to the profile's directory
        if "flatpak" in self.sources_storage["browsers"][iteminfo["browser"]]:
            os.system("/usr/bin/flatpak override --user {0} --filesystem={1}/{2}".format(self.sources_storage["browsers"][iteminfo["browser"]]["flatpak"], variables.default_ice_directory, iteminfo["id"]))
            #NOTE: Flatpak permissions are granted to the profiles folder per application so that the browser cannot read profiles it is not assigned to
            #TODO: Move this elsewhere when adding in browser reselection?

        #Make note of the profile name and last updated configs
        profileconfs = {}
        if os.path.isfile("%s/.solstice-settings" % profilepath):
            with open("%s/.solstice-settings" % profilepath, 'r') as fp:
                profileconfs = json.loads(fp.read())

        #Set user's human-readable name,
        profileconfs["readablename"] = profilename
        #...no-cache preference,
        profileconfs["nocache"] = nocache
        #...and dark-mode preference,
        profileconfs["darkmode"] = darkmode
        #...and note the current date and save .solstice-settings
        profileconfs["lastupdated"] = datetime.today().strftime('%Y%m%d')

        try:
            with open("{0}/{1}/{2}/.solstice-settings".format(default_ice_directory, iteminfo["id"], profileid), 'w') as fp:
                fp.write(json.dumps(profileconfs, separators=(',', ':')))
        except Exception as exceptionstr:
            raise ICESharedModuleException(_("Failed to write to .solstice-settings"))

