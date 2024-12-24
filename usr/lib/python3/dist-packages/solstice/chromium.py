# This file is part of Feren Solstice.
#
# Copyright 2020-2023 Dominic Hayes

from . import utils, variables
import os
import gettext
gettext.install("solstice-python", "/usr/share/locale", names="ngettext")
import gi
from gi.repository import GLib
import json
import shutil
import filecmp
import colorsys

class SolsticeChromiumException(Exception):
    pass


def updateProfile(parentinfo, appsettings, psettings, profiledir, csssettings):
    def excludeSettings(defaults, blacklist, prefs):
        if prefs == {}:
            # Skip excluding defaults if the profile isn't configured yet
            return defaults
        # Exclude defaults from being re-set if their settings already exist and should not be reset
        for i in blacklist:
            if type(blacklist[i]) == dict:
                if i in prefs: # Recurse
                    defaults[i] = excludeSettings(defaults[i], blacklist[i], prefs[i])
            else:
                if i in prefs:
                    if blacklist[i] == None:
                        defaults.pop(i) #Never reset (null)
                    elif prefs[i] not in blacklist[i]:
                        defaults.pop(i) #Reset only if value matches criteria
        return defaults

    # Generate profile folder if not present
    if not os.path.isdir("%s/Default" % profiledir):
        try:
            os.mkdir("%s/Default" % profiledir)
        except Exception as e:
            raise SolsticeChromiumException(_("Failed to create the profile's folder: %s") % e)

    # Update the Solstice CSS
    updateSolstDefaultCSS(profiledir, parentinfo["browser"])

    # Get current and default profile defaults
    prefile = "%s/Default/Preferences" % profiledir
    if os.path.isfile(prefile):
        with open(prefile, 'r') as fp:
            confdict = json.loads(fp.read())
    else:
        confdict = {}
    with open("/usr/share/solstice/chromium/Preferences", 'r') as fp:
        defaults = json.loads(fp.read())

    # Also get current Local State if it exists
    lsfile = "%s/Local State" % profiledir
    if os.path.isfile(lsfile):
        with open(lsfile, 'r') as fp:
            lsdict = json.loads(fp.read())
    else:
        lsdict = {}

    # Prevent certain settings from being reset on existing profiles
    defaults["default"] = excludeSettings(defaults["default"], defaults["resetblacklist"], confdict)

    # Apply new defaults into profile
    confdict = utils.dictRecurUpdate(confdict, defaults["default"])

    # Repeat with Local State
    with open("/usr/share/solstice/chromium/Local State", 'r') as fp:
        lsdefaults = json.loads(fp.read())
        lsdefaults["default"] = excludeSettings(lsdefaults["default"], lsdefaults["resetblacklist"], lsdict)
        lsdict = utils.dictRecurUpdate(lsdict, lsdefaults["default"])

    # Set profile defaults specific to the profile-application configuration
    confdict["custom_links"]["list"][0]["title"] = parentinfo["name"]
    confdict["custom_links"]["list"][0]["url"] = parentinfo["website"]
    confdict["download"]["default_directory"] = appsettings["lastdownloadsdir"] + "/" + appsettings["downloadsdirname"]
    confdict["homepage"] = parentinfo["website"]
    confdict["session"]["startup_urls"] = [parentinfo["website"]]
    confdict["vivaldi"]["homepage"] = parentinfo["website"]
    confdict["vivaldi"]["homepage_cache"] = parentinfo["website"]
    if "cssroot" in variables.sources[parentinfo["browsertype"]][parentinfo["browser"]]:
        confdict["vivaldi"]["appearance"]["css_ui_mods_directory"] = "%s/%s" % \
                (profiledir, variables.sources[parentinfo["browsertype"]][parentinfo["browser"]]["cssroot"])
    confdict, lsdict = setProfileName(parentinfo, psettings["readablename"], profiledir, confdict, lsdict)
    # confdict = setNoCache(psettings["nocache"], profiledir, confdict)

    # Include Plasma Integration, and selected bonuses, into the profile
    confdict = setBonuses(profiledir, parentinfo["bonusids"], confdict)

    # Set permissions for our websites and required services' websites
    confdict = setPermissions(defaults, confdict, parentinfo)

    # Set Workspaces and History availability
    confdict = setExtFeatures(defaults, confdict, parentinfo["nohistory"], parentinfo["workspaces"])

    # Set the palette this application will use in the respective browsers
    confdict = setPalette(csssettings, confdict, parentinfo)

    # Enable Vivaldi's bubbly mode if CSS requests it
    if "connectedtabs" in csssettings:
        if csssettings["connectedtabs"] == False:
            confdict["vivaldi"]["appearance"]["density"] = True

    # Save to the Preferences file
    try:
        with open(prefile, 'w') as fp:
            fp.write(json.dumps(confdict, separators=(',', ':'))) # This dumps minified json (how convenient), which is EXACTLY what Chrome uses for Preferences, so it's literally pre-readied
    except:
        raise SolsticeChromiumException(_("Failed to write to Preferences"))

    # Save to the Local State file
    try:
        with open(lsfile, 'w') as fp:
            fp.write(json.dumps(lsdict, separators=(',', ':')))
    except:
        raise SolsticeChromiumException(_("Failed to write to Local State"))


    # Finally, create the First Run file
    try:
        with open("%s/First Run" % profiledir, 'w') as fp:
            pass # Skips the initial Welcome options dialog
    except Exception as e:
        raise SolsticeChromiumException(_("Failed at the last minute"))


##########################################################
# CSS Settings
##########################################################

def updateCSSSettings(parentinfo, profiledir, csssettings):
    # Get current and default profile defaults
    prefile = "%s/Default/Preferences" % profiledir
    if os.path.isfile(prefile):
        with open(prefile, 'r') as fp:
            confdict = json.loads(fp.read())
    else:
        raise SolsticeChromiumException(_("Preferences does not exist - the profile should have been updated instead of running this function"))
    
    # Update the palette this application will use per the settings
    confdict = setPalette(csssettings, confdict, parentinfo)

    # Toggle Vivaldi's bubbly mode accordingly
    confdict["vivaldi"]["appearance"]["density"] = False
    if "connectedtabs" in csssettings:
        if csssettings["connectedtabs"] == False:
            confdict["vivaldi"]["appearance"]["density"] = True

    # Save changes to Preferences file
    try:
        with open(prefile, 'w') as fp:
            fp.write(json.dumps(confdict, separators=(',', ':'))) # This dumps minified json (how convenient), which is EXACTLY what Chrome uses for Preferences, so it's literally pre-readied
    except:
        raise SolsticeChromiumException(_("Failed to write to Preferences"))


##########################################################
# Profile Updating
##########################################################

def updateSolstDefaultCSS(profiledir, browser):
    # Don't continue if the browser is ineligible
    if "cssfolder" not in variables.sources["chromium"][browser]:
        return
    cssroot = variables.sources["chromium"][browser]["cssroot"]

    # Abort if the Browser-specific CSS's folder is somehow not present
    if not os.path.isdir(profiledir + "/" + cssroot):
        raise SolsticeChromiumException(_("The CSS's folder does not exist - it should have been created by updateCSS"))

    # Copy Solstice's Browser-specific CSS
    try:
        shutil.copy("/usr/share/solstice/chromium/chrome/%s.css" % variables.sources["chromium"][browser]["cssfolder"],
                "%s/solsticss.css" % (profiledir + "/" + cssroot))
    except Exception as e:
        raise SolsticeChromiumException(_("Failed to copy Solstice's CSS: %s") % e)
    

def setProfileName(parentinfo, newname, profiledir, confdict=None, lsdict=None):
    if not os.path.isdir(profiledir):
        raise SolsticeChromiumException(_("The profile %s does not exist") % profiledir.split("/")[-1])

    patchfiles = (confdict == None and lsdict == None)
    # Preferences file
    if confdict == None:
        prefile = "%s/Default/Preferences" % profiledir
        if os.path.isfile(prefile): # Load Preferences into variable if one exists
            with open(prefile, 'r') as fp:
                confdict = json.loads(fp.read())
    # Local State file
    if lsdict == None:
        lsfile = "%s/Local State" % profiledir
        if os.path.isfile(lsfile): # Load Local State into variable if one exists
            with open(lsfile, 'r') as fp:
                lsdict = json.loads(fp.read())

    # Update configurations in Preferences
    confdict["profile"]["name"] = _("{0} - {1}").format(newname, parentinfo["name"])
    # Remove cached profile name
    if "profile" in lsdict:
        if "info_cache" in lsdict["profile"]:
            if "Default" in lsdict["profile"]["info_cache"]:
                lsdict["profile"]["info_cache"].pop("Default")

    if patchfiles:
        # Save to Preferences
        try:
            with open(prefile, 'w') as fp:
                fp.write(json.dumps(confdict, separators=(',', ':')))
        except Exception as exceptionstr:
            raise SolsticeChromiumException(_("Failed to write to Preferences"))
        # Save to Local State
        try:
            with open(lsfile, 'w') as fp:
                fp.write(json.dumps(lsdict, separators=(',', ':')))
        except Exception as exceptionstr:
            raise SolsticeChromiumException(_("Failed to write to Local State"))
    else:
        return confdict, lsdict


def setBonuses(profiledir, bonuses=[], confdict=None):
    if not os.path.isdir(profiledir):
        raise SolsticeChromiumException(_("The profile %s does not exist") % profiledir.split("/")[-1])

    patchfiles = (confdict == None)
    # Preferences file
    if confdict == None:
        prefile = "%s/Default/Preferences" % profiledir
        if os.path.isfile(prefile): # Load Preferences into variable if one exists
            with open(prefile, 'r') as fp:
                confdict = json.loads(fp.read())

    # Open the Bonuses file
    with open("/usr/share/solstice/chromium/bonuses.json", 'r') as fp:
        bonusesjson = json.loads(fp.read())

    # Add the required extensions settings parent if not present yet
    if "extensions" not in confdict:
        confdict["extensions"] = {}
    if "settings" not in confdict["extensions"]:
        confdict["extensions"]["settings"] = {}

    # Add/remove bonuses based on bonus-selection
    bonuses.append("plasma-integration")
    for item in bonusesjson:
        if item in bonuses:
            # Prevent 'downgrading' the selected bonuses
            for extid in bonusesjson[item]:
                if extid in confdict["extensions"]["settings"]:
                    bonusesjson[item][extid]["manifest"].pop("name", None)
                    bonusesjson[item][extid]["manifest"].pop("version", None)
                    bonusesjson[item][extid]["manifest"].pop("manifest_version", None)
                    bonusesjson[item][extid].pop("path", None)
            confdict["extensions"]["settings"] = utils.dictRecurUpdate(confdict["extensions"]["settings"], bonusesjson[item])
        else:
            for extid in bonusesjson[item]:
                confdict["extensions"]["settings"].pop(extid, None)

    if patchfiles:
        # Save to Preferences
        try:
            with open(prefile, 'w') as fp:
                fp.write(json.dumps(confdict, separators=(',', ':')))
        except Exception as exceptionstr:
            raise SolsticeChromiumException(_("Failed to write to Preferences"))
    else:
        return confdict
    

def setNoCache(newbool, profiledir, confdict=None):
    # if not os.path.isdir(profiledir):
    #     raise SolsticeChromiumException(_("The profile %s does not exist") % profiledir.split("/")[-1])
    
    patchfiles = (confdict == None)
    # # Preferences file
    # if confdict == None:
    #     prefile = "%s/Default/Preferences" % profiledir
    #     if os.path.isfile(prefile): # Load Preferences into variable if one exists
    #         with open(prefile, 'r') as fp:
    #             confdict = json.loads(fp.read())

    # NOTE:
    # Chromium browsers DON'T have anything to do here.
    # To disable cache, arguments are used instead at their runtime.

    if patchfiles:
        pass
        # # Save to Preferences
        # try:
        #     with open(prefile, 'w') as fp:
        #         fp.write(json.dumps(confdict, separators=(',', ':')))
        # except Exception as exceptionstr:
        #     raise SolsticeChromiumException(_("Failed to write to Preferences"))
    else:
        return confdict


def setPermissions(defaults, confdict, parentinfo):
    # Open the Services file
    with open("/usr/share/solstice/info/services.json", 'r') as fp:
        services = json.loads(fp.read())

    # Collate websites to grant permissions to
    websites = [utils.shortenURL(parentinfo["website"])] # Main website
    for i in parentinfo["childwebsites"]: # Child websites
        ii = utils.shortenURL(i)
        try:
            ii = ii.split("/")[0]
        except:
            pass
        websites.append(ii)
    for i in parentinfo["services"]: # Required services' domains
        if i in services:
            for ii in services[i]:
                websites.append(services[i][ii])

    # Grant permissions to the websites
    for domain in websites:
        for permtype in ["automatic_downloads", "automatic_fullscreen", "auto_picture_in_picture", "autoplay", "background_sync", "captured_surface_control", "clipboard", "cookies", "file_handling", "font_access", "images", "javascript", "local_fonts", "notifications", "payment_handler", "popups", "sensors", "sleeping_tabs", "sound", "window_placement"]:
            confdict["profile"]["content_settings"]["exceptions"][permtype] = {}
            confdict["profile"]["content_settings"]["exceptions"][permtype]["[*.]"+domain+",*"] = {"expiration": "0", "model": 0, "setting": 1}
            confdict["profile"]["content_settings"]["exceptions"][permtype][domain+",*"] = {"expiration": "0", "model": 0, "setting": 1}
        for permtype in ["ar", "bluetooth_scanning", "file_system_write_guard", "geolocation", "hid_guard", "media_stream_camera", "media_stream_mic", "midi_sysex", "serial_guard", "storage_access", "usb_guard", "vr"]:
            confdict["profile"]["content_settings"]["exceptions"][permtype] = {}
            confdict["profile"]["content_settings"]["exceptions"][permtype]["[*.]"+domain+",*"] = {"expiration": "0", "model": 0, "setting": 3}
            confdict["profile"]["content_settings"]["exceptions"][permtype][domain+",*"] = {"expiration": "0", "model": 0, "setting": 3}

    # Disabled Hangouts if the Hangouts service isn't required
    if "google-hangouts" not in parentinfo["services"]:
        confdict = utils.dictRecurUpdate(confdict, defaults["disable-googlehangouts"])
    
    # Return the modified Preferences
    return confdict


def setExtFeatures(defaults, confdict, nohistory, workspaces):
    if nohistory: # Disable History if the SSB provides History itself
        confdict = utils.dictRecurUpdate(confdict, defaults["nohistory"])
    if workspaces: # Enable Workspaces if needed
        confdict = utils.dictRecurUpdate(confdict, defaults["workspaces"])
    
    return confdict


def setPalette(csssettings, confdict, parentinfo):
    def getNearestNeighbour(header, tab, page):
        # Get the HSLs
        r, g, b = tuple(int(page[i:i+2], 16) for i in (1, 3, 5))
        pageh, pages, pagel = colorsys.rgb_to_hsv(r, g, b)
        r, g, b = tuple(int(header[i:i+2], 16) for i in (1, 3, 5))
        hdrh, hdrs, hdrl = colorsys.rgb_to_hsv(r, g, b)
        r, g, b = tuple(int(tab[i:i+2], 16) for i in (1, 3, 5))
        tabh, tabs, tabl = colorsys.rgb_to_hsv(r, g, b)

        # Find the difference
        tabldiff = abs(pagel - tabl) # Prevent from becoming negative
        hdrldiff = abs(pagel - hdrl)
        tabsdiff = abs(pages - tabs)
        hdrsdiff = abs(pages - hdrs)
        tabhdiff = abs(pageh - tabh)
        hdrhdiff = abs(pageh - hdrh)
        # Return the 'nearest neighbour' to page background
        #  NOTE: Lightness has highest priority, hence the difference is tripled
        if ((3 * tabldiff) + (2 * tabsdiff) + tabhdiff) <= ((3 * hdrldiff) + (2 * hdrsdiff) + hdrhdiff): #Tab colour is nearer
            return tab
        else:
            return header
        
    # Apply appropriate Chromium "Material You" colour
    #  NOTE: The colour from light mode is used for the colour
    if utils.isColorGrey(parentinfo["accent"]):
        # If the colour is a shade of grey, we need to actually apply grey
        #  If we don't, we'll get a random colour instead - only hue is actually used.
        confdict["browser"]["theme"]["is_grayscale"] = True
        confdict["browser"]["theme"].pop("color_variant", None)
        confdict["browser"]["theme"].pop("user_color", None)
    else:
        # NOTE: -16777216 is the minimum value, being black, with -1 being white
        #  Essentially, to apply the colour we take its hex value, convert it to decimal,
        #  and then add it to the minimum value, and... profit.
        confdict["browser"]["theme"]["user_color"] = -16777216 + int(parentinfo["accent"][1:], 16)
        confdict["browser"]["theme"]["color_variant"] = 1
        confdict["browser"]["theme"].pop("is_grayscale", None)

    # Vivaldi palette
    visuallyconnectedtabs = True # Default value
    # Override if CSS states wanting otherwise
    if "connectedtabs" in csssettings:
        if csssettings["connectedtabs"] == False:
            visuallyconnectedtabs = False

    # Get header, tab and page colours appropriate to the visual tabs connection or lack-of
    if visuallyconnectedtabs == True:
        lighthdr, darkhdr = parentinfo["connheaderlight"], parentinfo["connheaderdark"]
        lighttab, darktab = parentinfo["conntablight"], parentinfo["conntabdark"]
        lightpage, darkpage = parentinfo["connsitelight"], parentinfo["connsitedark"]
    else:
        lighthdr, darkhdr = parentinfo["headerlight"], parentinfo["headerdark"]
        lighttab, darktab = parentinfo["tablight"], parentinfo["tabdark"]
        lightpage, darkpage = parentinfo["sitelight"], parentinfo["sitedark"]

    # Light
    #  NOTE: Vivaldi has no separate page colour - therefore, we need to set
    #  the palette accordingly so the colour used in pages is the closest
    #  palette colour possible to the intended page colour by mapping accordingly.
    if getNearestNeighbour(lighthdr, lighttab, lightpage) == lighthdr:
        confdict["vivaldi"]["themes"]["system"][0]["accentOnWindow"] = False
        confdict["vivaldi"]["themes"]["system"][0]["colorAccentBg"] = lighttab
        confdict["vivaldi"]["themes"]["system"][0]["colorBg"] = lighthdr
        confdict["vivaldi"]["themes"]["system"][0]["colorWindowBg"] = lighthdr
        confdict["vivaldi"]["themes"]["system"][0]["colorFg"] = "#000000" if utils.colourIsLight(lighthdr) else "#FFFFFF"
        confdict["vivaldi"]["themes"]["system"][0]["colorHighlightBg"] = parentinfo["accent"] if utils.coloursDiffer(parentinfo["accent"], lighthdr) else confdict["vivaldi"]["themes"]["system"][0]["colorFg"]
    else:
        confdict["vivaldi"]["themes"]["system"][0]["accentOnWindow"] = True
        confdict["vivaldi"]["themes"]["system"][0]["colorAccentBg"] = lighthdr
        confdict["vivaldi"]["themes"]["system"][0]["colorBg"] = lighttab
        confdict["vivaldi"]["themes"]["system"][0]["colorWindowBg"] = lighttab
        confdict["vivaldi"]["themes"]["system"][0]["colorFg"] = "#000000" if utils.colourIsLight(lighttab) else "#FFFFFF"
        confdict["vivaldi"]["themes"]["system"][0]["colorHighlightBg"] = parentinfo["accent"] if utils.coloursDiffer(parentinfo["accent"], lighttab) else confdict["vivaldi"]["themes"]["system"][0]["colorFg"]

    # Dark
    if getNearestNeighbour(darkhdr, darktab, darkpage) == darkhdr:
        confdict["vivaldi"]["themes"]["system"][1]["accentOnWindow"] = False
        confdict["vivaldi"]["themes"]["system"][1]["colorAccentBg"] = darktab
        confdict["vivaldi"]["themes"]["system"][1]["colorBg"] = darkhdr
        confdict["vivaldi"]["themes"]["system"][1]["colorWindowBg"] = darkhdr
        confdict["vivaldi"]["themes"]["system"][1]["colorFg"] = "#000000" if utils.colourIsLight(darkhdr) else "#FFFFFF"
        confdict["vivaldi"]["themes"]["system"][1]["colorHighlightBg"] = parentinfo["accentdark"] if utils.coloursDiffer(parentinfo["accentdark"], darkhdr) else confdict["vivaldi"]["themes"]["system"][1]["colorFg"]
    else:
        confdict["vivaldi"]["themes"]["system"][1]["accentOnWindow"] = True
        confdict["vivaldi"]["themes"]["system"][1]["colorAccentBg"] = darkhdr
        confdict["vivaldi"]["themes"]["system"][1]["colorBg"] = darktab
        confdict["vivaldi"]["themes"]["system"][1]["colorWindowBg"] = darktab
        confdict["vivaldi"]["themes"]["system"][1]["colorFg"] = "#000000" if utils.colourIsLight(darktab) else "#FFFFFF"
        confdict["vivaldi"]["themes"]["system"][1]["colorHighlightBg"] = parentinfo["accentdark"] if utils.coloursDiffer(parentinfo["accentdark"], darktab) else confdict["vivaldi"]["themes"]["system"][1]["colorFg"]

    # Private (NOTE: Colour palette is the same regardless of connected tabs option)
    confdict["vivaldi"]["themes"]["system"][2]["accentOnWindow"] = False
    confdict["vivaldi"]["themes"]["system"][2]["colorAccentBg"] = utils.colourFilter(parentinfo["accent"], -46.0)
    confdict["vivaldi"]["themes"]["system"][2]["colorBg"] = utils.colourFilter(parentinfo["accent"], -70.0)
    confdict["vivaldi"]["themes"]["system"][2]["colorWindowBg"] = utils.colourFilter(parentinfo["accent"], -70.0)
    confdict["vivaldi"]["themes"]["system"][2]["colorFg"] = "#000000" if utils.colourIsLight(utils.colourFilter(parentinfo["accent"], -70.0)) else "#FFFFFF"
    confdict["vivaldi"]["themes"]["system"][2]["colorHighlightBg"] = parentinfo["accent"]
    
    return confdict