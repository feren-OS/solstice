# This file is part of Feren Solstice.
#
# Copyright 2020-2023 Dominic Hayes

from . import variables
import os
import gettext
gettext.install("solstice-python", "/usr/share/locale", names="ngettext")
import locale
import gi
from gi.repository import GLib
from xdg.DesktopEntry import DesktopEntry
import colorsys
import collections.abc
import math
import json
import ast
import psutil
import shutil
import signal
import time
import grp

class SolsticeUtilsException(Exception):
    pass
class ProfileInUseException(Exception):
    pass


def dictRecurUpdate(d, u, fuselists=False):
    for k, v in u.items():
        if type(v) is dict:
            # Recurse into dictionary value
            d[k] = dictRecurUpdate(d.get(k, {}), v, fuselists)
        elif type(v) is list and fuselists:
            # Create a list if there is none at the original dict
            if k not in d or type(d[k]) is not list:
                d[k] = []
            d[k] = list(set(d[k] + v))
        else:
            d[k] = v
    return d


def recursiveFileList(directory):
    if not os.path.isdir(directory):
        return []

    dirs = [x[0] for x in os.walk(directory)]
    result = []
    for i in dirs:
        for ii in os.listdir(i):
            if os.path.isfile(i + "/" + ii):
                if i == directory:
                    result.append(ii)
                else:
                    result.append(i[len(directory)+1:] + "/" + ii)
    return result


def shortenURL(website):
    shortenedurl = website.split("://")[1:] #Remove the HTTPS portion
    shortenedurl = ''.join(shortenedurl) #Rejoin list into string
    try:
        shortenedurl = shortenedurl.split("/")[0] #Shorten to just domain
    except:
        pass
    return shortenedurl


def colourFilter(hexcode, amount, multiply=False):
    #string, float, bool

    #Returns:
    # Darkened/Lightened colour
    redc, greenc, bluec = tuple(int(hexcode[i:i+2], 16) for i in (1, 3, 5)) #Dodge the # character
    hue, lumi, sat = colorsys.rgb_to_hls(redc, greenc, bluec)

    if amount < 0.0: #Negative means darkening
        if multiply == True:
            lumi = lumi * (1.0 + amount) #1.0 + -amount, amount is negative, thus it darkens it during multiplication
        else:
            if (lumi + amount) < 0.0:
                lumi = 0.0
            else:
                lumi += amount
    else: #Positive means lightening, and 0.0 means no change
        if multiply == True:
            lumi = lumi * (1.0 + amount) #Add 1.0 to the amount to lighten it instead of darkening it during multiplication
        else:
            if (lumi + amount) > 255.0:
                lumi = 255.0
            else:
                lumi += amount

    if lumi == 255.0:
        return "#FFFFFF"
    elif lumi == 0.0:
        return "#000000"

    redc, greenc, bluec = colorsys.hls_to_rgb(hue, lumi, sat) #Convert to RGB
    redc, greenc, bluec = int(redc), int(greenc), int(bluec) #Convert back to integers
    return '#%02x%02x%02x' % (redc, greenc, bluec) #Returns conversion to hexcode


def colourIsLight(hexcode):
    #string

    #Returns:
    # True: Light
    # False: Dark
    redc, greenc, bluec = tuple(int(hexcode[i:i+2], 16) for i in (1, 3, 5)) #Dodge the # character
    rSRGB = redc / 255
    gSRGB = greenc / 255
    bSRGB = bluec / 255

    r = rSRGB / 12.92 if rSRGB <= .03928 else math.pow((rSRGB + .055) / 1.055, 2.4)
    g = gSRGB / 12.92 if rSRGB <= .03928 else math.pow((gSRGB + .055) / 1.055, 2.4)
    b = rSRGB / 12.92 if bSRGB <= .03928 else math.pow((bSRGB + .055) / 1.055, 2.4)
    lumi = .2126 * r + .7152 * g + .0722 * b

    if lumi > 0.4:
        return True
    else:
        return False

def coloursDiffer(hexcode1, hexcode2):
    #string, string

    #Returns:
    # True: Yes
    # False: No
    red1, green1, blue1 = tuple(int(hexcode1[i:i+2], 16) for i in (1, 3, 5))
    red2, green2, blue2 = tuple(int(hexcode2[i:i+2], 16) for i in (1, 3, 5))

    #Red
    redmatches = False
    if red2 > (red1 - 20) and red2 < (red1 + 20):
        redmatches = True
    #Green
    greenmatches = False
    if green2 > (green1 - 20) and green2 < (green1 + 20):
        greenmatches = True
    #Blue
    bluematches = False
    if blue2 > (blue1 - 20) and blue2 < (blue1 + 20):
        bluematches = True

    if redmatches and greenmatches and bluematches:
        return False
    else:
        return True

def isColorGrey(hexcode):
    #string

    #Returns:
    # True: Yes
    # False: No
    redc, greenc, bluec = tuple(int(hexcode[i:i+2], 16) for i in (1, 3, 5))
    hue, sat, val = colorsys.rgb_to_hsv(redc, greenc, bluec)

    if sat > 0.3:
        return False
    else:
        return True


def procExists(pid):
    try:
        os.kill(pid, 0) #Send a You There? to the PID identified
    except:
        return False
    return True


def getParentShortcut(parentid, wmclass, childid, filepath):
    #Get browser prefix
    browserprefix = wmclass[:-len(childid)]
    #Get the child shortcut's path
    shortcutpath = os.path.dirname(filepath)

    #Return parent shortcut location
    result = shortcutpath + "/" + browserprefix + parentid + ".desktop"
    if not os.path.isfile(result):
        raise SolsticeUtilsException(_("The shortcut's parent shortcut cannot be found."))
    return result


def browserFeatureAvailable(browsertype, browser, feature):
    if feature in variables.sources[browsertype][browser]:
        if variables.sources[browsertype][browser][feature] == True:
            return True
    return False


def generateProfileID(profilesdir, profilename):
    name = profilename.replace(" ", "").replace("\\", "").replace("/", "").replace("?", "").replace("*", "").replace("+", "").replace("%", "").lower()
    result = str(name)

    if os.path.isdir("{0}/{1}".format(profilesdir, result)): #Duplication prevention
        numbertried = 2
        while os.path.isdir("{0}/{1}{2}".format(profilesdir, result, numbertried)):
            numbertried += 1
        result = name + str(numbertried) #Append duplication prevention number

    return result


def getProfileSettings(profilesdir, profileid):
    #Returns: readablename, nocache
    if not os.path.isfile("%s/%s/.solstice-settings" % (profilesdir, profileid)):
        return profileid, False
    with open("%s/%s/.solstice-settings" % (profilesdir, profileid), 'r') as fp:
        profileconfs = json.loads(fp.read())
    readablename = profileid
    if "readablename" in profileconfs:
        readablename = profileconfs["readablename"]
    nocache = False
    if "nocache" in profileconfs:
        nocache = profileconfs["nocache"]
    return readablename, nocache


def isProfileOutdated(parentinfo, appsettings, psettings):
    downloads = False
    app = False
    solst = False
    browser = False
    cssroot = False

    #Downloads directory changed since profile opened
    if "lastdownloadsdir" not in psettings:
        downloads = True # No Downloads folder has been set yet, thus the profile needs updating to add one
    else:
        try:
            if psettings["lastdownloadsdir"] != appsettings["lastdownloadsdir"]:
                downloads = True
        except:
            downloads = True # This usually means they aren't numbers, thus outdated by definition

    #Application updated since profile opened
    if "applastupdated" not in psettings:
        app = True #not having applastupdated means it's outdated by definition
    else:
        try:
            if int(psettings["applastupdated"]) != parentinfo["lastupdated"]:
                app = True
        except:
            app = True

    #Solstice updated since profile opened
    if "solstlastupdated" not in psettings:
        solst = True
    else:
        try:
            if int(psettings["solstlastupdated"]) != variables.solsticeLastUpdated:
                solst = True
        except:
            solst = True

    #Browser changed since profile opened
    if "lastbrowser" not in psettings:
        browser = True
    else:
        try:
            if psettings["lastbrowser"] != parentinfo["browser"]:
                browser = True
        except:
            browser = True

    #CSS root directory changed since profile opened
    if "cssroot" in variables.sources[parentinfo["browsertype"]][parentinfo["browser"]]:
        if "lastcssroot" not in psettings:
            cssroot = True
        else:
            try:
                if psettings["lastcssroot"] != variables.sources[parentinfo["browsertype"]][parentinfo["browser"]]["cssroot"]:
                    cssroot = True
            except:
                cssroot = True
    elif "lastcssroot" in psettings and "cssroot" not in variables.sources[parentinfo["browsertype"]][parentinfo["browser"]]:
        cssroot = True

    #All checks have passed
    return downloads, app, solst, browser, cssroot


def amAdministrator():
    #Returns True if the current user is in the administrators group
    if os.geteuid() == 0:
        return True #being root counts as administrator.
    for g in os.getgroups():
        if grp.getgrgid(g).gr_name == "sudo":
            return True
    return False


def isBrowserAvailable(browser, browsertype):
    if browsertype not in variables.sources: #Invalid browser type
        return False
    if browser not in variables.sources[browsertype]: #Browser isn't categorised as this
        return False
    if "required-file" not in variables.sources[browsertype][browser]: #Browser is unavailable
        return False
    return os.path.isfile(variables.sources[browsertype][browser]["required-file"][0])


def getAvailableBrowsers(browsertype):
    if browsertype not in variables.sources: #Invalid browser type
        raise SolsticeUtilsException(_("%s is not a valid browser type") % browsertype)
    installed = 0
    available = 0
    for browser in variables.sources[browsertype]:
        if "unavailable" not in variables.sources[browsertype][browser]:
            available += 1
        else:
            continue
        if "required-file" in variables.sources[browsertype][browser]:
            if os.path.isfile(variables.sources[browsertype][browser]["required-file"][0]):
                installed += 1
    return installed, available #and return the quantity


def removeFlatpakProfilesPerm(flatpakid, profilesdir):
    targetfile = os.path.expanduser("~") + "/.local/share/flatpak/overrides/" + flatpakid

    if not os.path.isfile(targetfile):
        return #No file means no permissions set
    with open(targetfile, "rt") as fp:
        newcontents = fp.readlines()
    i = 0
    changed = False
    for line in newcontents:
        if line.startswith("filesystems="):
            if "%s;" % profilesdir not in line:
                continue #If the Flatpak doesn't have those permissions, don't bother writing to file
            newcontents[i] = newcontents[i].replace("!%s;" % profilesdir, "")
            newcontents[i] = newcontents[i].replace("%s;" % profilesdir, "")
            changed = True
        i += 1
    if changed == True:
        with open(targetfile, "w") as fp:
            fp.write("".join(newcontents))

def removeFlatpakDownloadsPerm(flatpakid, downloadsdir, downloadsname):
    targetfile = os.path.expanduser("~") + "/.local/share/flatpak/overrides/" + flatpakid

    if not os.path.isfile(targetfile):
        return #No file means no permissions set
    with open(targetfile, "rt") as fp:
        newcontents = fp.readlines()
    i = 0
    changed = False
    for line in newcontents:
        if line.startswith("filesystems="):
            if "%s/%s;" % (downloadsdir, downloadsname) not in line:
                continue #If the Flatpak doesn't have those permissions, don't bother writing to file
            newcontents[i] = newcontents[i].replace("%s/%s;" % (downloadsdir, downloadsname), "")
            newcontents[i] = newcontents[i].replace("%s/%s;" % (downloadsdir, downloadsname), "")
            changed = True
        i += 1
    if changed == True:
        with open(targetfile, "w") as fp:
            fp.write("".join(newcontents))

def removeFlatpakPerms(itemid):
    #Global permissions removal - used by the Storium module's uninstaller
    profilesdir = "{0}/{1}".format(variables.solsticeProfilesDirectory, itemid)
    with open("%s/.solstice-settings" % profilesdir, 'r') as fp:
        configs = json.loads(fp.read())
    if "lastdownloadsdir" not in configs:
        configs["lastdownloadsdir"] = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOWNLOAD) #Fallback value
    for i in variables.sources:
        for ii in variables.sources[i]:
            if "flatpak" in variables.sources[i][ii]:
                targetfile = os.path.expanduser("~") + "/.local/share/flatpak/overrides/" + variables.sources[i][ii]["flatpak"]

                if not os.path.isfile(targetfile):
                    continue #No file means no permissions set
                with open(targetfile, "rt") as fp:
                    newcontents = fp.readlines()
                i = 0
                changed = False
                for line in newcontents:
                    if line.startswith("filesystems="):
                        if "%s;" % profilesdir in line:
                            newcontents[i] = newcontents[i].replace("!%s;" % profilesdir, "")
                            newcontents[i] = newcontents[i].replace("%s;" % profilesdir, "")
                            changed = True
                        if "downloadsdirname" not in configs:
                            continue
                        if "%s/%s;" % (configs["lastdownloadsdir"], configs["downloadsdirname"]) not in line:
                            continue #If the Flatpak doesn't have those permissions, don't bother writing to file
                        newcontents[i] = newcontents[i].replace("%s/%s;" % (configs["lastdownloadsdir"], configs["downloadsdirname"]), "")
                        newcontents[i] = newcontents[i].replace("%s/%s;" % (configs["lastdownloadsdir"], configs["downloadsdirname"]), "")
                        changed = True
                    i += 1
                if changed == True:
                    with open(targetfile, "w") as fp:
                        fp.write("".join(newcontents))
    if "downloadsdirname" not in configs:
        raise SolsticeUtilsException(_("Cannot remove Downloads folder permissions as the Downloads folder was not set."))


def grantFlatpakProfilesPerm(browsertype, browser, profilesdir):
    if "flatpak" in variables.sources[browsertype][browser]:
        os.system('/usr/bin/flatpak override --user %s --filesystem="%s"' % (variables.sources[browsertype][browser]["flatpak"], profilesdir))

def grantFlatpakDownloadsPerm(browsertype, browser, downloadsdir, downloadsname):
    if "flatpak" in variables.sources[browsertype][browser]:
        os.system('/usr/bin/flatpak override --user %s --filesystem="%s/%s"' % (variables.sources[browsertype][browser]["flatpak"], downloadsdir, downloadsname))


def changeBrowserValue(parentfile, browsertype, oldbrowser, newbrowser, childfile=None):
    #Read the parent file to obtain required information
    parent=DesktopEntry()
    parent.parse(parentfile)
    parentdirectory = os.path.dirname(parentfile)

    oldprefix = variables.sources[browsertype][oldbrowser]["classprefix"]
    newprefix = variables.sources[browsertype][newbrowser]["classprefix"]

    #Get childrens' IDs
    childids = ast.literal_eval(parent.get("X-Solstice-Children"))
    #Update childrens' shortcuts
    for i in childids:
        childfile = parentdirectory + "/" + oldprefix + i + ".desktop"
        if not os.path.isfile(childfile):
            raise SolsticeUtilsException(_("%s's shortcut was not found") % i)
        newpath = parentdirectory + "/" + newprefix + i + ".desktop"
        with open(childfile, 'r') as old:
            newshortcut = old.readlines()
        ii = 0
        for line in newshortcut:
            if line.startswith("StartupWMClass="):
                newshortcut[ii] = "StartupWMClass=" + newprefix + i + "\n"
            elif line.startswith("Exec="):
                if line.endswith(" --force-manager\n"):
                    newshortcut[ii] = 'Exec=/usr/bin/solstice "' + newpath + '" --force-manager\n'
                else:
                    newshortcut[ii] = 'Exec=/usr/bin/solstice "' + newpath + '"\n'
            ii += 1

        os.remove(childfile) #Remove old shortcut
        #Write new shortcut
        with open(newpath, 'w') as fp:
            fp.write(''.join(newshortcut))
        #Mark shortcut as executable
        os.system('/usr/bin/chmod +x "%s"' % newpath)

    #Update parent file
    i = parent.get("X-Solstice-ID")
    newpath = parentdirectory + "/" + newprefix + i + ".desktop"
    with open(parentfile, 'r') as old:
        newshortcut = old.readlines()
    ii = 0
    for line in newshortcut:
        if line.startswith("X-Solstice-Browser="):
            newshortcut[ii] = "X-Solstice-Browser=" + newbrowser + "\n"
        elif line.startswith("StartupWMClass="):
            newshortcut[ii] = "StartupWMClass=" + newprefix + i + "\n"
        elif line.startswith("Exec="):
            if line.endswith(" --force-manager\n"):
                newshortcut[ii] = 'Exec=/usr/bin/solstice "' + newpath + '" --force-manager\n'
            else:
                newshortcut[ii] = 'Exec=/usr/bin/solstice "' + newpath + '"\n'
        ii += 1

    os.remove(parentfile) #Remove old shortcut
    #Write new shortcut
    with open(newpath, 'w') as fp:
        fp.write(''.join(newshortcut))
    #Mark as executable too
    os.system('/usr/bin/chmod +x "%s"' % newpath)

    #Return the shortcut to relaunch into
    if childfile == None:
        return newpath
    else:
        return childfile.replace(parentdirectory + "/" + oldprefix, parentdirectory + "/" + newprefix)


def deleteProfile(profiledir):
    if not os.path.isdir(profiledir):
        raise SolsticeUtilsException(_("The profile %s does not exist") % profiledir.split("/")[-1])
    else:
        if os.path.isfile(profiledir + "/.solstice-active-pid"):
            try:
                with open(profiledir + "/.solstice-active-pid", 'r') as pidfile:
                    lastpid = pidfile.readline()
                lastpid = int(lastpid)
                try:
                    target = psutil.Process(lastpid)
                    for i in target.children(recursive=True):
                        i.kill() #Kill the process immediately,
                    target.kill() # so we can remove it
                    time.sleep(0.4)
                except:
                    pass
            except Exception as e:
                raise ProfileInUseException(_("Failed to end %s's current session") % profileid)

    try:
        shutil.rmtree(profiledir)
    except Exception as e:
        raise SolsticeUtilsException(_("Failed to delete {0}: {1}").format(profiledir.split("/")[-1], e))


def getTranslation(value, getid=False):
    for i in [locale.getlocale()[0], locale.getlocale()[0].split("_")[0], "C"]:
        if i in value:
            if getid == False:
                return value[i]
            else:
                return i
    return None
