# This file is part of Feren Solstice.
#
# Copyright 2020-2023 Dominic Hayes

from . import utils
import os
import subprocess
import gettext
gettext.install("solstice-python", "/usr/share/locale", names="ngettext")
import gi
from gi.repository import GLib
import json
import shutil
from datetime import datetime
import ast
import signal
import time

class variables:
    #Developer options
    applications_directory = os.path.expanduser("~") + "/.local/share/applications"
    solstice_profiles_directory = os.path.expanduser("~") + "/.local/share/solstice"

class SolsticeModuleException(Exception):
    pass
class ProfileInUseException(Exception):
    pass

class main:
    def __init__(self):
        self.refresh_memory()

    def refresh_memory(self): # Function to refresh some memory values
        self.sources_storage = {}

        with open("/usr/share/solstice/sources-info/data.json", 'r') as fp:
            self.sources_storage = json.loads(fp.read())


    #### PROFILE EXECUTION
    def run_profile(self, itemid, profileid, browser, browsertype, website, wmclass, nohistory=False, closecallback=None):
        #string, string, string, string, bool
        profilepath = utils.get_profilepath(itemid, profileid)

        if browsertype not in self.sources_storage:
            raise SolsticeModuleException(_("Corrupt or incompatible data - %s is not a type of supported browser") % browsertype)

        if browser in self.sources_storage[browsertype]:
            commandtorun = self.sources_storage[browsertype][browser]["command"]

            #Check for configs
            darkmode, nocache = False, False
            if os.path.isfile(profilesdir + "/" + profileid + "/.solstice-settings"):
                with open(profilesdir + "/" + profileid + "/.solstice-settings", 'r') as fp:
                    icesettings = json.loads(fp.read())
                    if "darkmode" in icesettings:
                        darkmode = icesettings["darkmode"]
                    if "nocache" in icesettings:
                        nocache = icesettings["nocache"]
            #Append and prepend to command as according to the selected preferences
            if darkmode == True:
                commandtorun.insert(0, self.sources_storage["browsers"][browser]["darkmodeprefix"])
                commandtorun.append(self.sources_storage["browsers"][browser]["darkmodesuffix"])
            if nocache == True:
                commandtorun.insert(0, self.sources_storage["browsers"][browser]["nocacheprefix"])
                commandtorun.append(self.sources_storage["browsers"][browser]["nocachesuffix"])
            piececount = 0 #for loop right below
            while piececount < len(commandtorun):
                #Translate arguments to their context-appropriate values
                commandtorun[piececount] = commandtorun[piececount].replace(
                    "%WEBSITEURL%", website).replace(
                    "%WINCLASS%", wmclass).replace(
                    "%PROFILEDIR%", profilepath)
                piececount += 1

            ssbproc = subprocess.Popen(commandtorun, close_fds=True)
        else:
            raise SolsticeModuleException(_("Corrupt or incompatible data - %s is not a supported browser") % browser)

        #Check there's a note about a process having ran, and if so if the process is running
        if os.path.isfile(profilepath + "/.storium-active-pid"):
            with open(profilepath + "/.storium-active-pid", 'r') as pidfile:
                lastpid = pidfile.readline()
            try:
                lastpid = int(lastpid)
                if not utils.proc_exists(lastpid):
                    os.remove(profilepath + "/.storium-active-pid") #The PID doesn't exist
            except:
                os.remove(profilepath + "/.storium-active-pid")
        #Tell Solstice that the process's running
        if not os.path.isfile(profilepath + "/.storium-active-pid"):
            with open(profilepath + "/.storium-active-pid", 'w') as pidfile:
                pidfile.write(str(ssbproc.pid))

        if not closecallback == None:
            closecallback()
        if nohistory == True and browsertype == "chromium":
            #FIXME: We need a better way of doing this.
            time.sleep(16)
            if os.path.isfile(profilepath + "/Default/History"):
                os.remove(profilepath + "/Default/History")
            if os.path.isfile(profilepath + "/Default/History-journal"):
                os.remove(profilepath + "/Default/History-journal")
            if os.path.isdir(profilepath + "/Default/Sessions"):
                shutil.rmtree(profilepath + "/Default/Sessions")


    #### PROFILE CREATION / UPDATING
    def update_profile(self, iteminfo, profilename, profileid, darkmode, nocache):
        #NOTE: Also used to generate a new profile
        profilepath = utils.get_profilepath(iteminfo["id"], profileid)

        #Generate profile directory if it does not exist yet
        if not os.path.isdir(profilepath):
            utils.create_profile_folder(iteminfo["id"], profileid)
            #If Flatpak, grant access to the profile's directory
            if "flatpak" in self.sources_storage["browsers"][iteminfo["browser"]]:
                os.system("/usr/bin/flatpak override --user {0} --filesystem={1}/{2}".format(self.sources_storage["browsers"][iteminfo["browser"]]["flatpak"], variables.solstice_profiles_directory, iteminfo["id"]))
                #NOTE: Flatpak permissions are granted to the profiles folder per application so that the browser cannot read profiles it is not assigned to
                #...and also let them access their respective Downloads folders
                os.system("/usr/bin/flatpak override --user {0} --filesystem={1}".format(self.sources_storage["browsers"][iteminfo["browser"]]["flatpak"], GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOWNLOAD) + "/" + _("{0} Downloads").format(iteminfo["name"])))
                #TODO: Move this elsewhere when adding in browser reselection?
        else:
            if os.path.isfile(profilepath + "/.storium-active-pid"):
                try:
                    with open(profilepath + "/.storium-active-pid", 'r') as pidfile:
                        lastpid = pidfile.readline()
                    lastpid = int(lastpid)
                    if utils.proc_exists(lastpid):
                        raise ProfileInUseException(_("The profile %s is currently in use, so cannot be updated") % profileid)
                except Exception as e:
                    print(_("WARNING: Could not determine if the profile {0} is in use: {1}").format(profileid, e))

        extrawebsites = [] #TODO
        if iteminfo["browsertype"] == "chromium":
            from . import chromium
            chromium.update_profile(iteminfo, extrawebsites, profilename, profilepath, darkmode, nocache)
        elif iteminfo["browsertype"] == "firefox":
            from . import firefox
            firefox.update_profile(iteminfo, extrawebsites, profilename, profilepath, darkmode, nocache)

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
            with open("%s/.solstice-settings" % profilepath, 'w') as fp:
                fp.write(json.dumps(profileconfs, separators=(',', ':')))
        except Exception as exceptionstr:
            raise SolsticeModuleException(_("Failed to write to .solstice-settings"))

    def delete_profile(self, iteminfo, profileid):
        profilepath = utils.get_profilepath(iteminfo["id"], profileid)

        #Check the profile exists
        if not os.path.isdir(profilepath):
            raise SolsticeModuleException(_("The profile %s does not exist") % profilepath.split("/")[-1])
        else:
            if os.path.isfile(profilepath + "/.storium-active-pid"):
                try:
                    with open(profilepath + "/.storium-active-pid", 'r') as pidfile:
                        lastpid = pidfile.readline()
                    lastpid = int(lastpid)
                    try:
                        os.kill(lastpid, signal.SIGKILL) #Kill the process immediately, so we can remove it
                        time.sleep(0.4)
                    except:
                        pass
                except Exception as e:
                    raise ProfileInUseException(_("Failed to end %s's current session") % profileid)

        try:
            shutil.rmtree(profilepath)
        except Exception as e:
            raise SolsticeModuleException(_("Failed to delete {0}: {1}").format(profilepath.split("/")[-1], e))


    #### PROFILE OPTIONS
    def change_profile_name(self, profilepath, value):
        #string, string

        #Change the profile's name after its initial creation occurred
        profileconfs = {}
        if os.path.isfile("%s/.solstice-settings" % profilepath):
            with open("%s/.solstice-settings" % profilepath, 'r') as fp:
                profileconfs = json.loads(fp.read())
        profileconfs["readablename"] = value
        try:
            with open("%s/.solstice-settings" % profilepath, 'w') as fp:
                fp.write(json.dumps(profileconfs, separators=(',', ':')))
        except Exception as exceptionstr:
            raise SolsticeModuleException(_("Failed to write to .solstice-settings"))

    def set_profile_darkmode(self, browsertype, profilepath, value, outdated=False):
        #string, boolean

        if outdated == False: #If the profile is outdated, the changes made per browser will be made when the profile gets updated on launch,
            #thus, we save a write to disk by just skipping those aforementioned changes in here
            if iteminfo["browsertype"] == "chromium":
                from . import chromium
                chromium.set_profile_darkmode(profilepath, value)
            elif iteminfo["browsertype"] == "firefox":
                from . import firefox
                firefox.set_profile_darkmode(profilepath, value)

        #Update solstice-settings to reaffirm this change
        profileconfs = {}
        if os.path.isfile("%s/.solstice-settings" % profilepath):
            with open("%s/.solstice-settings" % profilepath, 'r') as fp:
                profileconfs = json.loads(fp.read())
        profileconfs["darkmode"] = value
        try:
            with open("%s/.solstice-settings" % profilepath, 'w') as fp:
                fp.write(json.dumps(profileconfs, separators=(',', ':')))
        except Exception as exceptionstr:
            raise SolsticeModuleException(_("Failed to write to .solstice-settings"))

    def set_profile_nocache(self, browsertype, profilepath, value, outdated=False):
        #string, boolean

        if outdated == False:
            if iteminfo["browsertype"] == "chromium":
                from . import chromium
                chromium.set_profile_nocache(profilepath, value)
            elif iteminfo["browsertype"] == "firefox":
                from . import firefox
                firefox.set_profile_nocache(profilepath, value)

        #Update solstice-settings to reaffirm this change
        profileconfs = {}
        if os.path.isfile("%s/.solstice-settings" % profilepath):
            with open("%s/.solstice-settings" % profilepath, 'r') as fp:
                profileconfs = json.loads(fp.read())
        profileconfs["nocache"] = value
        try:
            with open("%s/.solstice-settings" % profilepath, 'w') as fp:
                fp.write(json.dumps(profileconfs, separators=(',', ':')))
        except Exception as exceptionstr:
            raise SolsticeModuleException(_("Failed to write to .solstice-settings"))
