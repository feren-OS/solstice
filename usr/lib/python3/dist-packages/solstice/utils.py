# This file is part of Feren Solstice.
#
# Copyright 2020-2023 Dominic Hayes

from . import variables
import os
import gettext
gettext.install("solstice-python", "/usr/share/locale", names="ngettext")
import gi
from gi.repository import GLib
from xdg.DesktopEntry import DesktopEntry
import colorsys
import collections.abc
from PIL import Image #TODO: remove once icons moved
import magic #TODO: remove once icons moved
import math
import json
import ast
import psutil
import shutil
import signal
import time

class SolsticeUtilsException(Exception):
    pass
class ProfileInUseException(Exception):
    pass

def dict_recurupdate(d, u):
    for k, v in u.items():
        if isinstance(v, collections.abc.Mapping):
            d[k] = dict_recurupdate(d.get(k, {}), v)
        else:
            d[k] = v
    return d

def shorten_url(website):
    shortenedurl = website.split("://")[1:] #Remove the HTTPS portion
    shortenedurl = ''.join(shortenedurl) #Rejoin list into string
    try:
        shortenedurl = shortenedurl.split("/")[0] #Shorten to just domain
    except:
        pass
    return shortenedurl

def boolean_to_jsonbool(boole):
    if boole == True:
        return "true"
    else:
        return "false"

def color_is_light(hexcode):
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

def color_filter(hexcode, amount, multiply=False):
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

    redc, greenc, bluec = colorsys.hls_to_rgb(hue, lumi, sat) #Convert to RGB
    redc, greenc, bluec = int(redc), int(greenc), int(bluec) #Convert back to integers
    return '#%02x%02x%02x' % (redc, greenc, bluec) #Returns conversion to hexcode

def are_colours_different(hexcode1, hexcode2):
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

def proc_exists(pid):
    try:
        os.kill(pid, 0) #Send a You There? to the PID identified
    except:
        return False
    return True

def export_icon_file(itemid, iconsource): #TODO: Move to Storium module's code
    try:
        #Make sure necessary directories exist
        for i in [os.path.expanduser("~") + "/.local", os.path.expanduser("~") + "/.local/share", os.path.expanduser("~") + "/.local/share/icons", os.path.expanduser("~") + "/.local/share/icons/hicolor"]:
            if not os.path.isdir(i):
                os.mkdir(i)

        mimetype = magic.Magic(mime=True).from_file(iconsource)
        if mimetype == "image/png" or mimetype == "image/vnd.microsoft.icon" or mimetype == "image/jpeg" or mimetype == "image/bmp": #PNG, JPG, BMP or ICO
            iconfile = Image.open(iconsource)
            #Get and store the image's size, first
            imagesize = iconfile.size[1]

            #Now downsize the icon to each size:
            for i in [[512, "512x512"], [256, "256x256"], [128, "128x128"], [64, "64x64"], [48, "48x48"], [32, "32x32"], [24, "24x24"], [16, "16x16"]]:
                #...if it is large enough
                if imagesize < i[0]:
                    continue

                #Create the directory if it doesn't exist
                for ii in [os.path.expanduser("~") + "/.local/share/icons/hicolor/" + i[1], os.path.expanduser("~") + "/.local/share/icons/hicolor/" + i[1] + "/apps"]:
                    if not os.path.isdir(ii):
                        os.mkdir(ii)

                targetpath = os.path.expanduser("~") + "/.local/share/icons/hicolor/" + i[1] + "/apps/solstice-" + itemid + ".png"
                if imagesize != i[0]:
                    iconfile.resize((i[0], i[0]))
                    iconfile.save(targetpath, "PNG")
                else:
                    shutil.copy(iconsource, targetpath)
        elif mimetype == "image/svg+xml": #SVG
            #Create the directory if it doesn't exist
            for ii in [os.path.expanduser("~") + "/.local/share/icons/hicolor/scalable", os.path.expanduser("~") + "/.local/share/icons/hicolor/scalable/apps"]:
                if not os.path.isdir(ii):
                    os.mkdir(ii)

            #Copy the SVG over
            targetpath = os.path.expanduser("~") + "/.local/share/icons/hicolor/scalable/apps/solstice-" + itemid + ".svg"
            shutil.copy(iconsource, targetpath)

    except Exception as e:
        raise SolsticeUtilsException(_("Exporting icon failed: %s") % e)

def profileid_generate(profilesdir, profilename):
    name = profilename.replace(" ", "").replace("\\", "").replace("/", "").replace("?", "").replace("*", "").replace("+", "").replace("%", "").lower()
    result = str(name)

    if os.path.isdir("{0}/{1}".format(profilesdir, result)): #Duplication prevention
        numbertried = 2
        while os.path.isdir("{0}/{1}{2}".format(profilesdir, result, numbertried)):
            numbertried += 1
        result = name + str(numbertried) #Append duplication prevention number

    return result

def get_profilepath(itemid, profileid):
    return "{0}/{1}/{2}".format(variables.solstice_profiles_directory, itemid, profileid)

def create_profile_folder(itemid, profileid):
    if not os.path.isdir(variables.solstice_profiles_directory): #Make sure the profiles directory even exists
        try:
            os.mkdir(variables.solstice_profiles_directory)
        except Exception as e:
            raise SolsticeUtilsException(_("Failed to create the user's Solstice Profiles folder: %s") % e)

    if not os.path.isdir(variables.solstice_profiles_directory + "/%s" % itemid): #Now create the directory for this website application's profiles to go
        try:
            os.mkdir(variables.solstice_profiles_directory + "/%s" % itemid)
        except Exception as e:
            raise SolsticeUtilsException(_("Failed to create the application's Solstice Profiles folder: %s") % e)

    if os.path.isdir("{0}/{1}/{2}".format(variables.solstice_profiles_directory, itemid, profileid)): #Fail if profile exists
        raise SolsticeUtilsException(_("The profile %s already exists") % profileid)
    else:
        os.mkdir("{0}/{1}/{2}".format(variables.solstice_profiles_directory, itemid, profileid))

def get_profile_settings(itemid, profileid):
    #Returns: readablename, nocache, darkmode
    profiledir = get_profilepath(itemid, profileid)
    if not os.path.isfile("%s/.solstice-settings" % profiledir):
        return profileid, False, False
    with open("%s/.solstice-settings" % profiledir, 'r') as fp:
        profileconfs = json.loads(fp.read())
    result = {}
    if "readablename" in profileconfs:
        result["readablename"] = profileconfs["readablename"]
    else:
        result["readablename"] = profileid
    if "nocache" in profileconfs:
        result["nocache"] = profileconfs["nocache"]
    else:
        result["nocache"] = False
    if "darkmode" in profileconfs:
        result["darkmode"] = profileconfs["darkmode"]
    else:
        result["darkmode"] = False
    return result["readablename"], result["nocache"], result["darkmode"]

def get_profile_outdated(profileid, itemid, shortcutlastupdated, browserid):
    profilepath = get_profilepath(itemid, profileid)
    if not os.path.isfile("%s/.solstice-settings" % profilepath):
        return True #lastupdated* is in said file
    with open("%s/.solstice-settings" % profilepath, 'r') as fp:
        profileconfs = json.loads(fp.read())
    if "lastupdatedshortcut" not in profileconfs:
        return True #not having lastupdatedshortcut means it's outdated by definition
    if "lastupdatedsolstice" not in profileconfs:
        return True #not having lastupdatedsolstice also does
    if "lastbrowser" not in profileconfs:
        return True #not having lastbrowser also does
    try:
        if int(profileconfs["lastupdatedshortcut"]) < int(shortcutlastupdated):
            return True #profile's last update was earlier than the shortcut's
        else:
            if int(profileconfs["lastupdatedsolstice"]) < int(variables.solstice_lastupdated):
                return True #profile's last update was earlier than Solstice's was
            elif profileconfs["lastbrowser"] != browserid:
                return True #profile's last browser wasn't the current one
            else:
                return False #profile is up to date
    except:
        return True #this usually means they aren't numbers, thus outdated by definition

def complete_item_information(desktopinfo):
    #Adds fallback values for any missing values
    fallbackpalette = False
    fallbackchromi = False
    defaultitems = {"nohistory": False,
                    "googlehangouts": False,
                    "workspaces": False,
                    "bonusids": [],
                    "bg": "#ffffff",
                    "bgdark": "#000000",
                    "accent": "#4ba9fb",
                    "accentdark": "#1a192d",
                    "color": "#4ba9fb",
                    "colordark": "#4ba9fb",
                    "accentonwindow": True,
                    "chromicolor": "-5919045"}
    itemsrequired = ["name", "wmclass", "website", "browser", "browsertype", "extrawebsites", "lastupdated"]
    for item in itemsrequired:
        if item not in desktopinfo or desktopinfo[item] == "":
            raise SolsticeUtilsException(_("Corrupt or overdated .desktop file - %s is missing") % item)
    #Fall back to Solstice palette if the provided palette is incomplete
    if "bg" not in desktopinfo or "bgdark" not in desktopinfo or "accent" not in desktopinfo or "accentdark" not in desktopinfo:
        fallbackpalette = True
    elif desktopinfo["bg"] == "" or desktopinfo["bgdark"] == "" or desktopinfo["accent"] == "" or desktopinfo["accentdark"] == "":
        fallbackpalette = True
    if fallbackpalette == True:
        desktopinfo.pop("bg")
        desktopinfo.pop("bgdark")
        desktopinfo.pop("accent")
        desktopinfo.pop("accentdark")
        desktopinfo.pop("accentonwindow")
        print(_("W: %s is missing colour palette, falling back to Solstice palette") % desktopinfo["name"])
    if "colordark" not in desktopinfo or desktopinfo["colordark"] == "":
        desktopinfo.pop("colordark") #Don't warn as colordark is an optional accent colour extension
    if "color" not in desktopinfo or desktopinfo["color"] == "":
        desktopinfo.pop("color")
        print(_("W: %s is missing accent colour, falling back to Solstice accent colour") % desktopinfo["name"])
    #Same for Chromium colour
    if "chromicolor" not in desktopinfo:
        fallbackchromi = True
    elif desktopinfo["chromicolor"] == "":
        fallbackchromi = True
    if fallbackchromi == True:
        desktopinfo.pop("chromicolor")
        print(_("W: %s is missing Chromium colour, falling back to Solstice Chromium colour") % desktopinfo["name"])
    #Add in fallback values for missing values
    for item in defaultitems:
        if item not in desktopinfo or desktopinfo[item] == "":
            if item == "colordark" and "color" in desktopinfo:
                desktopinfo[item] = desktopinfo["color"]
            else:
                desktopinfo[item] = defaultitems[item]
    return desktopinfo

def is_browser_available(browser, browsertype):
    if browsertype not in variables.sources: #Invalid browser type
        return False
    if browser not in variables.sources[browsertype]: #Browser isn't categorised as this
        return False
    if "required-file" not in variables.sources[browsertype][browser]: #Browser is unavailable
        return False
    return os.path.isfile(variables.sources[browsertype][browser]["required-file"][0])

def get_available_browsers(browsertype):
    if browsertype not in variables.sources: #Invalid browser type
        raise SolsticeUtilsException(_("%s is not a valid browser type") % browsertype)
    result = []
    for browser in variables.sources[browsertype]:
        if "required-file" in variables.sources[browsertype][browser]:
            if os.path.isfile(variables.sources[browsertype][browser]["required-file"][0]):
                result.append(browser) #Add the available browsers to list,
    return result #and return the list

def is_feature_available(browsertype, browser, key): #use for sources[browsertype][browser][*available]
    if key not in variables.sources[browsertype][browser]:
        return False #Default to unavailable
    return variables.sources[browsertype][browser][key]

def remove_prefix(text, prefix):
    if text.startswith(prefix):
        return text[len(prefix):]
    return text

def remove_suffix(text, suffix):
    if text.endswith(suffix):
        return text[:-len(suffix)]
    return text

def set_flatpak_permissions(itemid, itemname, browsertype, browser):
    os.system('/usr/bin/flatpak override --user {0} --filesystem="{1}/{2}"'.format(variables.sources[browsertype][browser]["flatpak"], variables.solstice_profiles_directory, itemid))
    #NOTE: Flatpak permissions are granted to the profiles folder per application so that the browser cannot read profiles it is not assigned to
    #...and also let them access their respective Downloads folders
    os.system('/usr/bin/flatpak override --user {0} --filesystem="{1}"'.format(variables.sources[browsertype][browser]["flatpak"], GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOWNLOAD) + "/" + _("{0} Downloads").format(itemname)))

def remove_flatpak_permissions(itemid, itemname, browsertype, browser):
    targetfile = os.path.expanduser("~") + "/.local/share/flatpak/overrides/" + variables.sources[browsertype][browser]["flatpak"]
    with open(targetfile, "rt") as fp:
        newcontents = fp.readlines()
    i = 0
    for line in newcontents:
        if line.startswith("filesystems="):
            if "{0}/{1};".format(variables.solstice_profiles_directory, itemid) not in line \
            and GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOWNLOAD) + "/" + _("%s Downloads") % itemname + ";" not in line:
                return #If the Flatpak doesn't have those permissions, don't bother writing to file
            newcontents[i] = newcontents[i].replace("!{0}/{1};".format(variables.solstice_profiles_directory, itemid), "")
            newcontents[i] = newcontents[i].replace("!" + GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOWNLOAD) + "/" + _("%s Downloads") % itemname + ";", "")
            newcontents[i] = newcontents[i].replace("{0}/{1};".format(variables.solstice_profiles_directory, itemid), "")
            newcontents[i] = newcontents[i].replace(GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOWNLOAD) + "/" + _("%s Downloads") % itemname + ";", "")
        i += 1
    with open(targetfile, "w") as fp:
        fp.write("".join(newcontents))

def set_browser(currentfile, browsertype, itemid, itemname, oldbrowser, newbrowser):
    #If the old browser was a Flatpak, remove its permissions
    if "flatpak" in variables.sources[browsertype][oldbrowser]:
        remove_flatpak_permissions(itemid, itemname, browsertype, oldbrowser)
    #If the new browser is a Flatpak, grant it permissions
    if "flatpak" in variables.sources[browsertype][newbrowser]:
        set_flatpak_permissions(itemid, itemname, browsertype, newbrowser)

    currentchild = ""
    oldshortcut=DesktopEntry()
    oldshortcut.parse(currentfile)

    #Check if it's a parent ID, and if so switch to it
    if oldshortcut.get("X-Solstice-ParentID") != "":
        #currentchild = os.path.basename(currentfile).replace(itemid + "-", "").removesuffix(".desktop")
        currentchild = remove_suffix(os.path.basename(currentfile).replace(itemid + "-", ""), ".desktop")
        currentfilelist = currentfile.split("/")
        currentfilelist[-1] = currentfilelist[-1].replace("-" + currentchild + ".desktop", ".desktop")
        currentfile = "/".join(currentfilelist)
        #Swap out for parent .desktop
        oldshortcut=DesktopEntry()
        oldshortcut.parse(currentfile)

    #Get childrens' IDs
    childids = []
    childids = ast.literal_eval(oldshortcut.get("X-Solstice-Children"))
    updatedidpaths = {}
    #Update childrens' shortcuts
    for i in childids:
        childfilelist = currentfile.split("/")
        childfilelist[-1] = childfilelist[-1].replace(itemid + ".desktop", itemid + "-" + i + ".desktop")
        childfile = "/".join(childfilelist)
        updatedidpaths[i] = set_browser_shortcut(childfile, browsertype, itemid, newbrowser, i)
    #Then update the main shortcut
    updatedidpaths[itemid] = set_browser_shortcut(currentfile, browsertype, itemid, newbrowser)

    if currentchild == "": #If this was summoned for the parent shortcut...
        return updatedidpaths[itemid] #Return new shortcut path
    else: #Otherwise...
        return updatedidpaths[currentchild] #Return child shortcut path
            
def set_browser_shortcut(currentfile, browsertype, itemid, newbrowser, childid=""):
    #Put old shortcut's lines into memory
    with open(currentfile, 'r') as old:
        newshortcut = old.readlines()

    #Generate a new name for the shortcut
    if childid == "":
        newfilename = variables.sources[browsertype][newbrowser]["classprefix"] + itemid
    else:
        newfilename = variables.sources[browsertype][newbrowser]["classprefix"] + itemid + "-" + childid
    newpath = os.path.join(os.path.dirname(currentfile), newfilename + ".desktop")

    i = 0
    for line in newshortcut:
        if line.startswith("X-Solstice-Browser="):
            newshortcut[i] = "X-Solstice-Browser=" + newbrowser + "\n"
        elif line.startswith("StartupWMClass="):
            newshortcut[i] = "StartupWMClass=" + newfilename + "\n"
        elif line.startswith("Exec="):
            if line.endswith(" --force-manager\n"):
                newshortcut[i] = 'Exec=/usr/bin/solstice "' + newpath + '" --force-manager\n'
            else:
                newshortcut[i] = 'Exec=/usr/bin/solstice "' + newpath + '"\n'
        i += 1
    
    os.remove(currentfile) #Remove old shortcut
    #Write new shortcut
    with open(newpath, 'w') as fp:
        fp.write(''.join(newshortcut))

    #Mark as executable too
    os.system('/usr/bin/chmod +x "%s"' % newpath)

    #Return the shortcut to relaunch into
    return newpath

def delete_profilefolder(profilepath):
    if not os.path.isdir(profilepath):
        raise SolsticeUtilsException(_("The profile %s does not exist") % profilepath.split("/")[-1])
    else:
        if os.path.isfile(profilepath + "/.solstice-active-pid"):
            try:
                with open(profilepath + "/.solstice-active-pid", 'r') as pidfile:
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
        shutil.rmtree(profilepath)
    except Exception as e:
        raise SolsticeUtilsException(_("Failed to delete {0}: {1}").format(profilepath.split("/")[-1], e))

def uninstall_shortcut(itemid): #TODO: Move this into Storium module
    profilesdir = "{0}/{1}".format(variables.solstice_profiles_directory, itemid)
    itemnames = []
    #Delete all profiles, first
    if os.path.isdir(profilesdir):
        for i in os.listdir(profilesdir):
            if os.path.isdir(profilesdir + "/" + i):
                delete_profilefolder(profilesdir + "/" + i)
        shutil.rmtree(profilesdir)
    #Now delete the shortcuts
    for browsertype in variables.sources: #Iterate through all possible classprefixes
        for browser in variables.sources[browsertype]:
            classprefix = variables.sources[browsertype][browser]["classprefix"]
            possiblefile = os.path.join(os.path.expanduser("~"), ".local/share/applications", classprefix + itemid + ".desktop")
            if os.path.isfile(possiblefile):
                try:
                    entry=DesktopEntry()
                    entry.parse(possiblefile)
                except:
                    continue #Skip if file's invalid
                #Find the children first, note name,
                childids = ast.literal_eval(entry.get("X-Solstice-Children"))
                if entry.getName() not in itemnames:
                    itemnames.append(entry.getName())
                #and delete the children
                for i in childids:
                    childfilelist = possiblefile.split("/")
                    childfilelist[-1] = childfilelist[-1].replace(itemid + ".desktop", itemid + "-" + i + ".desktop")
                    childfile = "/".join(childfilelist)
                    try:
                        os.remove(childfile)
                    except:
                        pass #Ignore children deletion failures
                #Now delete the original file
                try:
                    os.remove(possiblefile)
                except Exception as e:
                    raise SolsticeUtilsException(_("Failed to uninstall shortcuts: %s") % e)
    #Now revoke Flatpak permissions
    for browsertype in variables.sources: #Iterate through all possible Flatpaks
        for browser in variables.sources[browsertype]:
            if "flatpak" not in variables.sources[browsertype][browser]:
                continue
            for name in itemnames:
                remove_flatpak_permissions(itemid, name, browsertype, browser)
