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
import filecmp
import copy

class SolsticeModuleException(Exception):
    pass
class ProfileInUseException(Exception):
    pass


def getBrowserModule(browsertype):
    if browsertype == "chromium":
        from . import chromium
        return chromium
    elif browsertype == "firefox":
        from . import firefox
        return firefox


##########################################################
# CSS Modding
##########################################################

def getCSSSettings(browsertype, browser):
    # Check the browser is eligible for CSS modding
    if "cssfolder" in variables.sources[browsertype][browser]:
        csspath = "%s/%s-css" % (variables.cssPath,
                        variables.sources[browsertype][browser]["cssfolder"])
        if os.path.isfile("%s/config.json" % csspath) and os.path.isfile("%s/custom.css" % csspath):
            try:
                with open("%s/config.json" % csspath, 'r') as fp:
                    return json.loads(fp.read())
            except:
                print(_("W: Failed to open custom CSS configs. Custom CSS will be disabled on this profile."))
    
    # Return nothing, therefore disabling mods, if the browser chosen isn't eligible
    #  or the user has no/invalid mods
    return {}


def isCSSOutdated(profiledir, browsertype, browser):    
    profilecss = "%s/%s/custom" % (profiledir,
                                variables.sources[browsertype][browser]["cssroot"])
    csspath = "%s/.config/solstice/%s-css" % (os.path.expanduser("~"),
                            variables.sources[browsertype][browser]["cssfolder"])
    
    # Create the parent CSS folder if it doesn't exist
    if not os.path.exists(profiledir + "/" + variables.sources[browsertype][browser]["cssroot"]):
        try:
            os.mkdir(profiledir + "/" + variables.sources[browsertype][browser]["cssroot"])
            return os.path.exists(csspath) # Skip comparing CSS files given the directory's new
        except:
            raise SolsticeModuleException(_("Failed to create parent CSS folder in the profile"))
    
    # Get files in both global CSS folder and the profile's CSS folder and
    # check for unique files between both folders
    currentfiles = utils.recursiveFileList(profilecss)
    globalfiles = utils.recursiveFileList(csspath)
    if "config.json" in globalfiles:
        globalfiles.remove("config.json")
    for i in currentfiles:
        if i not in globalfiles:
            return True
    for i in globalfiles:
        if i not in currentfiles:
            return True
    #Check that each file matches in both folders
    for i in currentfiles:
        if filecmp.cmp(csspath + "/" + i, profilecss + "/" + i) == False:
            return True
    #All checks passed
    return False


def updateCSSSettings(parentinfo, psettings, profiledir, browsermodule):
    csssettings = getCSSSettings(parentinfo["browsertype"], parentinfo["browser"])

    def isCSSSettingsOutdated(psettings, csssettings):
        #CSS settings changed since profile opened
        if csssettings == {} and "css" in psettings:
            return True # CSS has been disabled since
        elif csssettings != {} and "css" not in psettings:
            return True # CSS has been enabled since
        elif "css" in psettings and type(psettings["css"]) != dict:
            return True # CSS preferences are invalid
        elif csssettings != {}:
            for i in csssettings:
                if i not in psettings["css"] or psettings["css"][i] != csssettings[i]:
                    return True # CSS setting has been added/changed since
            for i in psettings["css"]:
                if i not in csssettings:
                    return True # CSS setting has been removed since

    # Skip if the CSS Settings DON'T need updating
    if not isCSSSettingsOutdated(psettings, csssettings):
        print("cssssettings up to date")
        return psettings, False

    # Update the CSS Settings influencing values for the browser
    browsermodule.updateCSSSettings(parentinfo, profiledir, csssettings)

    # Update recorded CSS Settings
    updated = False
    if csssettings == {} and "css" in psettings:
        psettings.pop("css") # Not necessary - remove it
        updated = True
    elif csssettings != {}:
        psettings["css"] = {}
        updated = True
        for i in csssettings:
            psettings["css"][i] = csssettings[i]
    
    return psettings, updated
    

def updateCSS(parentinfo, profiledir):
    # Skip if the browser chosen isn't eligible
    if "cssfolder" not in variables.sources[parentinfo["browsertype"]][parentinfo["browser"]]:
        return
    # Skip if the CSS DOESN'T need updating
    if isCSSOutdated(profiledir, parentinfo["browsertype"], parentinfo["browser"]) == False:
        return
    
    cssroot = "%s/%s" % (profiledir,
                variables.sources[parentinfo["browsertype"]][parentinfo["browser"]]["cssroot"])
    profilecss = cssroot + "/custom"
    csspath = "%s/.config/solstice/%s-css" % (os.path.expanduser("~"),
                    variables.sources[parentinfo["browsertype"]][parentinfo["browser"]]["cssfolder"])
    
    # Delete profile's existing CSS mods folder
    if os.path.exists(profilecss):
        shutil.rmtree(profilecss)

    try:
        if os.path.isfile("%s/config.json" % csspath) and os.path.isfile("%s/custom.css" % csspath):
            # Copy mods to the profile's CSS mods folder
            shutil.copytree(csspath, profilecss)
            # Remove redundant files
            os.remove("%s/config.json" % profilecss)

            # Import the custom CSS
            with open("%s/solstmods.css" % cssroot, 'w') as fp:
                fp.write('@import "custom/custom.css";')
        else:
            with open("%s/solstmods.css" % cssroot, 'w') as fp:
                fp.write(_("/* No mods are currently installed. For more information: %s */") % "TBD")
    except:
        raise SolsticeModuleException(_("Failed to update CSS modifications"))
    

def updateCSSRoot(browsertype, browser, psettings, psettingsupd):
    if "cssroot" not in variables.sources[browsertype][browser]:
        # No cssroot for this browser
        if "lastcssroot" not in psettings:
            return psettings, psettingsupd
        psettings.pop("lastcssroot")
        psettingsupd = True
    else: # Browser supports CSS
        if "lastcssroot" in psettings and psettings["lastcssroot"] == variables.sources[browsertype][browser]["cssroot"]:
            return psettings, psettingsupd
        psettings["lastcssroot"] = variables.sources[browsertype][browser]["cssroot"]
        psettingsupd = True
    return psettings, psettingsupd


##########################################################
# Bonuses
##########################################################

def updateBonuses(parentinfo, psettings, updated, profiledir, bonuses):
    # Skip if the bonuses WERE NOT changed
    if "lastbonusids" in psettings:
        if psettings["lastbonusids"] == bonuses:
            return psettings, updated

    # Update values in the browser
    if parentinfo["browsertype"] == "chromium":
        from . import chromium
        chromium.setBonuses(profiledir, bonuses)
    elif parentinfo["browsertype"] == "firefox":
        from . import firefox
        firefox.setBonuses(profiledir, bonuses)

    # Update recorded bonuses
    psettings["lastbonusids"] = bonuses

    return psettings, True


##########################################################
# Profile Execution
##########################################################

def runProfile(parentinfo, appinfo, appsettings, pdir, pid, closewndcall):
    if parentinfo["browsertype"] not in variables.sources:
        raise SolsticeModuleException(_("Corrupt or incompatible data - %s is not a type of supported browser") % parentinfo["browsertype"])
    if parentinfo["browser"] not in variables.sources[parentinfo["browsertype"]]:
        raise SolsticeModuleException(_("Corrupt or incompatible data - %s is not a supported browser") % parentinfo["browser"])
    profiledir = pdir + "/" + pid

    # Get the profile settings
    if os.path.isfile("%s/.solstice-settings" % profiledir):
        with open("%s/.solstice-settings" % profiledir, 'r') as fp:
            psettings = json.loads(fp.read())
    else: #Write fallback profile settings
        psettings = {"readablename": pid}
        try:
            with open("%s/.solstice-settings" % profiledir, 'w') as fp:
                fp.write(json.dumps(psettings, separators=(',', ':')))
        except Exception as e:
            raise SolsticeModuleException(_("%s contains no settings") % pid)

    # Check if core files are missing from the profile
    filesMissing = False
    for i in variables.sources[parentinfo["browsertype"]][parentinfo["browser"]]["expected-files"]:
        if not os.path.isfile("%s/%s" % (profiledir, i)):
            filesMissing = True
            break
    
    # IF the profile isn't already running,
    if profileInUse(profiledir) != True:
        # Check if the profile needs updating
        downloadsUpd, appUpd, solstUpd, browserUpd, cssRootUpd = utils.isProfileOutdated(parentinfo, appsettings, psettings)

        # Delete previous CSS if under various circumstances
        if (solstUpd or browserUpd or cssRootUpd) and "lastcssroot" in psettings:
            if os.path.exists("%s/%s" % (profiledir, psettings["lastcssroot"])):
                shutil.rmtree("%s/%s" % (profiledir, psettings["lastcssroot"]))

        # Collect browsermodule and make notes
        browsermodule = getBrowserModule(parentinfo["browsertype"])
        psettingsupd = False

        # Update the CSS if eligible
        updateCSS(parentinfo, profiledir)

        # Update the profile if it needs updating
        if filesMissing or \
                solstUpd or browserUpd or cssRootUpd or \
                downloadsUpd or appUpd:
            psettings, psettingsupd = updateProfile(parentinfo, appsettings, psettings, profiledir, browsermodule)
            # NOTE: updateProfile will updateCSSSettings and updateBonuses during its process
        else:
            # Update profile settings pertaining to custom CSS
            psettings, psettingsupd = updateCSSSettings(parentinfo, psettings, profiledir, browsermodule)
            # and Bonuses
            psettings, psettingsupd = updateBonuses(parentinfo, psettings, psettingsupd, profiledir, parentinfo["bonusids"])

        # Update CSS directory and save any profile settings changes
        psettings, psettingsupd = updateCSSRoot(parentinfo["browsertype"], parentinfo["browser"], psettings, psettingsupd)
        if psettingsupd == True:
            try:
                with open("%s/.solstice-settings" % profiledir, 'w') as fp:
                    fp.write(json.dumps(psettings, separators=(',', ':')))
            except:
                raise SolsticeModuleException(_("Failed to write to .solstice-settings"))
            
        if parentinfo["browsertype"] == "chromium" and os.path.isfile("%s/Last Version" % profiledir):
            # Skips migration procedures and Vivaldi changelog opening
            try:
                os.remove("%s/Last Version" % profiledir)
            except Exception as e:
                print(_("W: Failed to delete Last Version: %s") % e)
    else:
        # Throw an exception if core files are missing
        if filesMissing:
            raise SolsticeModuleException(_("%s needs to be updated but is currently running. Please close this application's windows and try again.") % psettings["readablename"])

    # Adjust command for launching profile if "No Cache" is turned on
    commandtorun = variables.sources[parentinfo["browsertype"]][parentinfo["browser"]]["command"]
    if "nocache" in psettings and psettings["nocache"] == True:
        #Append and prepend to command as according to the selected preferences
        commandtorun = variables.sources[parentinfo["browsertype"]][parentinfo["browser"]]["nocacheprefix"] + commandtorun
        commandtorun = commandtorun + variables.sources[parentinfo["browsertype"]][parentinfo["browser"]]["nocachesuffix"]

    # Translate arguments to their context-appropriate values
    for i, word in enumerate(commandtorun):
        commandtorun[i] = word.replace(
            "%WEBSITEURL%", appinfo["website"]).replace(
            "%WINCLASS%", parentinfo["wmclass"]).replace(
            "%PROFILEDIR%", profiledir)

    # Launch profile in its browser
    ssbproc = subprocess.Popen(commandtorun, close_fds=True)

    # Note the PID of the session if this is the session's launching process
    if os.path.isfile(profiledir + "/.solstpid"):
        with open(profiledir + "/.solstpid", 'r') as pidfile:
            lastpid = pidfile.readline()
        try:
            lastpid = int(lastpid)
            if not utils.procExists(lastpid):
                os.remove(profiledir + "/.solstpid") #The PID doesn't exist
        except:
            os.remove(profiledir + "/.solstpid")
    if not os.path.isfile(profiledir + "/.solstpid"):
        with open(profiledir + "/.solstpid", 'w') as pidfile:
            pidfile.write(str(ssbproc.pid))

    # Delete history files (Chromium)
    if parentinfo["nohistory"] == True and parentinfo["browsertype"] == "chromium":
        if not closewndcall == None:
            closewndcall()
        #FIXME: We need a better way of doing this.
        time.sleep(20)
        if os.path.isfile(profiledir + "/Default/History"):
            os.remove(profiledir + "/Default/History")
        if os.path.isfile(profiledir + "/Default/History-journal"):
            os.remove(profiledir + "/Default/History-journal")
        if os.path.isdir(profiledir + "/Default/Sessions"):
            shutil.rmtree(profiledir + "/Default/Sessions")


def profileInUse(profiledir):
    if os.path.isfile(profiledir + "/.solstpid"):
        try:
            with open(profiledir + "/.solstpid", 'r') as pidfile:
                lastpid = pidfile.readline()
            lastpid = int(lastpid)
            if utils.procExists(lastpid):
                return True
        except Exception as e:
            if e.__class__.__name__ != "ProfileInUseException":
                print(_("W: Could not determine if the profile is in use: %s") % e)
            else:
                raise SolsticeModuleException(e)
    return False


def updateProfile(parentinfo, appsettings, psettings, profiledir, browsermodule=None):
    csssettings = getCSSSettings(parentinfo["browsertype"], parentinfo["browser"])

    # Update recorded CSS Settings
    if "css" not in csssettings and "css" in psettings:
        psettings.pop("css") # Not necessary - remove it
    elif "css" in csssettings:
        if "css" not in psettings:
            psettings["css"] = {}
        for i in csssettings:
            if psettings["css"][i] != csssettings[i]:
                psettings["css"][i] = csssettings[i]

    # Run the appropriate module's profile updating code
    if browsermodule == None:
        browsermodule = getBrowserModule(parentinfo["browsertype"])
    browsermodule.updateProfile(parentinfo, appsettings, psettings, profiledir, csssettings)

    #...and update lastupdated values, and save .solstice-settings.
    psettings["applastupdated"] = int(parentinfo["lastupdated"])
    psettings["solstlastupdated"] = int(variables.solsticeLastUpdated)
    psettings["lastbrowser"] = parentinfo["browser"]
    psettings["lastdownloadsdir"] = appsettings["lastdownloadsdir"]
    psettings["lastbonusids"] = parentinfo["bonusids"]

    return psettings, True


##########################################################
# Profile Management
##########################################################

def setProfileName(parentinfo, newname, profiledir, running):
    # Update values in the browser if the profile isn't running
    #  If running, the profile will be marked to naturally update, including the new name.
    if running != True:
        if parentinfo["browsertype"] == "chromium":
            from . import chromium
            chromium.setProfileName(parentinfo, newname, profiledir)
        elif parentinfo["browsertype"] == "firefox":
            from . import firefox
            firefox.setProfileName(parentinfo, newname, profiledir)

    # Save the new name in the .solstice-settings file
    confdict = {}
    if os.path.isfile("%s/.solstice-settings" % profiledir):
        with open("%s/.solstice-settings" % profiledir, 'r') as fp:
            confdict = json.loads(fp.read())

    confdict["readablename"] = newname

    try:
        with open("%s/.solstice-settings" % profiledir, 'w') as fp:
            fp.write(json.dumps(confdict, separators=(',', ':')))
    except Exception as exceptionstr:
        raise SolsticeModuleException(_("Failed to write to .solstice-settings"))


def setNoCache(parentinfo, newbool, profiledir, running):
    # Update values in the browser if the profile isn't running
    #  If running, the profile will be marked to naturally update, including the new value.
    if running != True:
        if parentinfo["browsertype"] == "chromium":
            from . import chromium
            chromium.setNoCache(newbool, profiledir)
        elif parentinfo["browsertype"] == "firefox":
            from . import firefox
            firefox.setNoCache(newbool, profiledir)

    # Save the new name in the .solstice-settings file
    confdict = {}
    if os.path.isfile("%s/.solstice-settings" % profiledir):
        with open("%s/.solstice-settings" % profiledir, 'r') as fp:
            confdict = json.loads(fp.read())

    confdict["nocache"] = newbool

    try:
        with open("%s/.solstice-settings" % profiledir, 'w') as fp:
            fp.write(json.dumps(confdict, separators=(',', ':')))
    except Exception as exceptionstr:
        raise SolsticeModuleException(_("Failed to write to .solstice-settings"))