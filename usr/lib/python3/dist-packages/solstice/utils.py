# This file is part of Feren Solstice.
#
# Copyright 2020-2023 Dominic Hayes

from . import variables
import os
import gettext
gettext.install("solstice-python", "/usr/share/locale", names="ngettext")
import shutil #TODO: remove once icons moved
import colorsys
import collections.abc
from PIL import Image #TODO: remove once icons moved
import magic #TODO: remove once icons moved
import math
import json

class SolsticeUtilsException(Exception):
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

def complete_item_information(desktopinfo):
    #Adds fallback values for any missing values
    fallbackpalette = False
    fallbackchromi = False
    defaultitems = {"extraids": [],
                    "nohistory": False,
                    "googlehangouts": False,
                    "bonusids": [],
                    "bg": "#ffffff",
                    "bgdark": "#000000",
                    "accent": "#4ba9fb",
                    "accentdark": "#1a192d",
                    "color": "#4ba9fb",
                    "accentonwindow": True,
                    "chromicolor": "-5919045"}
    itemsrequired = ["name", "wmclass", "website", "browser", "browsertype", "lastupdated"]
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
            desktopinfo[item] = defaultitems[item]
    return desktopinfo

def is_browser_available(browser, browsertype):
    if browsertype not in variables.sources: #Invalid browser type
        return False
    if browser not in variables.sources[browsertype]: #Browser isn't categorised as this
        return False
    if "command" not in variables.sources[browsertype][browser]: #Browser is unavailable
        return False
    return os.path.isfile(variables.sources[browsertype][browser]["command"][0])

def get_available_browsers(browsertype):
    if browsertype not in variables.sources: #Invalid browser type
        raise SolsticeUtilsException(_("%s is not a valid browser type") % browsertype)
    result = []
    for browser in variables.sources[browsertype]:
        if "command" in variables.sources[browsertype][browser]:
            if os.path.isfile(variables.sources[browsertype][browser]["command"][0]):
                result.append(browser) #Add the available browsers to list,
    return result #and return the list

def is_feature_available(browsertype, browser, key): #use for sources[browsertype][browser][*available]
    if key not in variables.sources[browsertype][browser]:
        return False #Default to unavailable
    return variables.sources[browsertype][browser][key]
