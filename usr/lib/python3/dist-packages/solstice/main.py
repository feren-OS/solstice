# This file is part of Feren Solstice.
#
# Copyright 2020-2023 Dominic Hayes

from . import utils, variables
import os
import subprocess
import gettext
gettext.install("solstice-python", "/usr/share/locale", names="ngettext")
import gi
from gi.repository import GLib
import json
from datetime import datetime
import ast
import time
import shutil

class SolsticeModuleException(Exception):
    pass
class ProfileInUseException(Exception):
    pass

class main:
    def __init__(self):
        pass

    #### PROFILE EXECUTION
    def run_profile(self, itemid, profileid, browser, browsertype, website, wmclass, nohistory=False, closecallback=None):
        #string, string, string, string, bool
        profilepath = utils.get_profilepath(itemid, profileid)

        if browsertype not in variables.sources:
            raise SolsticeModuleException(_("Corrupt or incompatible data - %s is not a type of supported browser") % browsertype)

        if browser in variables.sources[browsertype]:
            commandtorun = variables.sources[browsertype][browser]["command"]
            #Check for configs
            darkmode, nocache = False, False
            if os.path.isfile(profilepath + "/.solstice-settings"):
                with open(profilepath + "/.solstice-settings", 'r') as fp:
                    solsettings = json.loads(fp.read())
                    if "darkmode" in solsettings:
                        darkmode = solsettings["darkmode"]
                    if "nocache" in solsettings:
                        nocache = solsettings["nocache"]
            #Append and prepend to command as according to the selected preferences
            if darkmode == True:
                commandtorun = variables.sources[browsertype][browser]["darkmodeprefix"] + commandtorun
                commandtorun = commandtorun + variables.sources[browsertype][browser]["darkmodesuffix"]
            if nocache == True:
                commandtorun = variables.sources[browsertype][browser]["nocacheprefix"] + commandtorun
                commandtorun = commandtorun + variables.sources[browsertype][browser]["nocachesuffix"]
            piececount = 0 #for loop right below
            for piece in commandtorun:
                #Translate arguments to their context-appropriate values
                commandtorun[piececount] = piece.replace(
                    "%WEBSITEURL%", website).replace(
                    "%WINCLASS%", wmclass).replace(
                    "%PROFILEDIR%", profilepath)
                piececount += 1

            ssbproc = subprocess.Popen(commandtorun, close_fds=True)
        else:
            raise SolsticeModuleException(_("Corrupt or incompatible data - %s is not a supported browser") % browser)

        #Check there's a note about a process having ran, and if so if the process is running
        if os.path.isfile(profilepath + "/.solstice-active-pid"):
            with open(profilepath + "/.solstice-active-pid", 'r') as pidfile:
                lastpid = pidfile.readline()
            try:
                lastpid = int(lastpid)
                if not utils.proc_exists(lastpid):
                    os.remove(profilepath + "/.solstice-active-pid") #The PID doesn't exist
            except:
                os.remove(profilepath + "/.solstice-active-pid")
        #Tell Solstice that the process's running
        if not os.path.isfile(profilepath + "/.solstice-active-pid"):
            with open(profilepath + "/.solstice-active-pid", 'w') as pidfile:
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


    def update_item_settings(self, iteminfo):
        if not os.path.isdir(variables.solstice_profiles_directory): #Make sure the profiles directory even exists
            try:
                os.mkdir(variables.solstice_profiles_directory)
            except Exception as e:
                raise SolsticeModuleException(_("Failed to create the user's Solstice Profiles folder: %s") % e)

        if not os.path.isdir(variables.solstice_profiles_directory + "/%s" % iteminfo["id"]): #Now create the directory for this website application's profiles to go
            try:
                os.mkdir(variables.solstice_profiles_directory + "/%s" % iteminfo["id"])
                #If Flatpak, grant access to the profiles directory
                if "flatpak" in variables.sources[iteminfo["browsertype"]][iteminfo["browser"]]:
                    utils.set_flatpak_permissions(iteminfo["id"], iteminfo["name"], iteminfo["browsertype"], iteminfo["browser"])
            except Exception as e:
                raise SolsticeModuleException(_("Failed to create the application's Solstice Profiles folder: %s") % e)

        #Update the item's .solstice-settings
        itemconfs = {}
        changesmade = False
        itemprofilesfldr = variables.solstice_profiles_directory + "/" + iteminfo["id"]
        if os.path.isfile("%s/.solstice-settings" % itemprofilesfldr):
            with open("%s/.solstice-settings" % itemprofilesfldr, 'r') as fp:
                itemconfs = json.loads(fp.read())

        targetdir = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOWNLOAD)
        if "lastdownloadsdir" in itemconfs:
            olddir = itemconfs["lastdownloadsdir"]
            if itemconfs["lastdownloadsdir"] != targetdir:
                itemconfs["lastdownloadsdir"] = targetdir
                changesmade = True
        else:
            olddir = None
            itemconfs["lastdownloadsdir"] = targetdir
            changesmade = True
        if "downloadsname" not in itemconfs:
            #downloadsname can only be set once and never changed after unless uninstalled
            itemconfs["downloadsname"] = _("{0} Downloads").format(iteminfo["name"])
            changesmade = True

        if changesmade == True: #Save changes if changes were made
            try:
                with open("%s/.solstice-settings" % itemprofilesfldr, 'w') as fp:
                    fp.write(json.dumps(itemconfs, separators=(',', ':')))
            except Exception as exceptionstr:
                raise SolsticeModuleException(_("Failed to write to .solstice-settings"))

            #Check if this config is for a Flatpak, and if so update the permissions on it
            if "flatpak" in variables.sources[iteminfo["browsertype"]][iteminfo["browser"]]:
                #Remove old Downloads directory permissions
                targetfile = os.path.expanduser("~") + "/.local/share/flatpak/overrides/" + variables.sources[iteminfo["browsertype"]][iteminfo["browser"]]["flatpak"]
                if not os.path.isfile(targetfile):
                    return #No file means no permissions set
                with open(targetfile, "rt") as fp:
                    newcontents = fp.readlines()
                if olddir != None: #Skip if there's no old downloads directory
                    i = 0
                    for line in newcontents:
                        if line.startswith("filesystems="):
                            if olddir + "/" + itemconfs["downloadsname"] + ";" not in line:
                                return #If the Flatpak doesn't have those permissions, don't bother writing to file
                            newcontents[i] = newcontents[i].replace("!{0}/{1};".format(olddir, itemconfs["downloadsname"]), "")
                            newcontents[i] = newcontents[i].replace("{0}/{1};".format(olddir, itemconfs["downloadsname"]), "")
                        i += 1
                    with open(targetfile, "w") as fp:
                        fp.write("".join(newcontents))
                #Then add in the new directory permissions
                os.system('/usr/bin/flatpak override --user {0} --filesystem="{1}/{2}"'.format(variables.sources[iteminfo["browsertype"]][iteminfo["browser"]]["flatpak"], targetdir, itemconfs["downloadsname"]))


    #### PROFILE CREATION / UPDATING
    def update_profile(self, iteminfo, profilename, profileid, darkmode, nocache, downloadsdir, downloadsname):
        #NOTE: Also used to generate a new profile
        profilepath = utils.get_profilepath(iteminfo["id"], profileid)

        #Generate profile directory if it does not exist yet
        if not os.path.isdir(profilepath):
            utils.create_profile_folder(iteminfo["id"], profileid)
        else:
            if os.path.isfile(profilepath + "/.solstice-active-pid"):
                try:
                    with open(profilepath + "/.solstice-active-pid", 'r') as pidfile:
                        lastpid = pidfile.readline()
                    lastpid = int(lastpid)
                    if utils.proc_exists(lastpid):
                        raise ProfileInUseException(_("The profile %s is currently in use, so cannot be updated") % profileid)
                except Exception as e:
                    if e.__class__.__name__ != "ProfileInUseException":
                        print(_("WARNING: Could not determine if the profile {0} is in use: {1}").format(profileid, e))
                    else:
                        raise ProfileInUseException(e)

        if iteminfo["browsertype"] == "chromium":
            from . import chromium
            chromium.update_profile(iteminfo, iteminfo["extrawebsites"], profilename, profilepath, darkmode, nocache, downloadsdir, downloadsname)
        elif iteminfo["browsertype"] == "firefox":
            from . import firefox
            firefox.update_profile(iteminfo, iteminfo["extrawebsites"], profilename, profilepath, darkmode, nocache, downloadsdir, downloadsname)

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
        #...and update lastupdated values, and save .solstice-settings.
        profileconfs["lastupdatedshortcut"] = int(iteminfo["lastupdated"])
        profileconfs["lastupdatedsolstice"] = int(variables.solstice_lastupdated)
        profileconfs["lastbrowser"] = iteminfo["browser"]
        profileconfs["lastdownloadsdir"] = downloadsdir

        try:
            with open("%s/.solstice-settings" % profilepath, 'w') as fp:
                fp.write(json.dumps(profileconfs, separators=(',', ':')))
        except Exception as exceptionstr:
            raise SolsticeModuleException(_("Failed to write to .solstice-settings"))

    def delete_profile(self, iteminfo, profileid):
        profilepath = utils.get_profilepath(iteminfo["id"], profileid)
        utils.delete_profilefolder(profilepath)


    #### PROFILE OPTIONS
    def change_profile_name(self, browsertype, profilepath, itemname, value, outdated=False, returnonly=False):
        #string, string

        if outdated == False: #If the profile is outdated, the changes made per browser will be made when the profile gets updated on launch,
            #thus, we save a write to disk by just skipping those aforementioned changes in here
            if browsertype == "chromium":
                from . import chromium
                chromium.change_profile_name(profilepath, itemname, value)
            elif browsertype == "firefox":
                from . import firefox
                firefox.change_profile_name(profilepath, itemname, value)

        if returnonly:
            return

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

    def set_profile_darkmode(self, browsertype, profilepath, value, outdated=False, returnonly=False):
        #string, boolean

        if outdated == False: #If the profile is outdated, the changes made per browser will be made when the profile gets updated on launch,
            #thus, we save a write to disk by just skipping those aforementioned changes in here
            if browsertype == "chromium":
                from . import chromium
                chromium.set_profile_darkmode(profilepath, value)
            elif browsertype == "firefox":
                pass #Not available in Firefox currently
                #from . import firefox
                #firefox.set_profile_darkmode(profilepath, value)

        if returnonly:
            return

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

    def set_profile_nocache(self, browsertype, profilepath, value, outdated=False, returnonly=False):
        #string, boolean

        if outdated == False:
            if browsertype == "chromium":
                from . import chromium
                chromium.set_profile_nocache(profilepath, value)
            elif browsertype == "firefox":
                from . import firefox
                firefox.set_profile_nocache(profilepath, value)

        if returnonly:
            return

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

    def batch_set_profilesettings(self, browsertype, profilepath, itemname, newname, outdated, darkmode, nocache):
        self.change_profile_name(browsertype, profilepath, itemname, newname, outdated, True)
        self.set_profile_darkmode(browsertype, profilepath, darkmode, outdated, True)
        self.set_profile_nocache(browsertype, profilepath, darkmode, outdated, True)
        #By doing things this way, we prevent 2 extra file writes

        #Update solstice-settings to reaffirm these changes
        profileconfs = {}
        if os.path.isfile("%s/.solstice-settings" % profilepath):
            with open("%s/.solstice-settings" % profilepath, 'r') as fp:
                profileconfs = json.loads(fp.read())
        profileconfs["readablename"] = newname
        profileconfs["darkmode"] = darkmode
        profileconfs["nocache"] = nocache
        try:
            with open("%s/.solstice-settings" % profilepath, 'w') as fp:
                fp.write(json.dumps(profileconfs, separators=(',', ':')))
        except Exception as exceptionstr:
            raise SolsticeModuleException(_("Failed to write to .solstice-settings"))
