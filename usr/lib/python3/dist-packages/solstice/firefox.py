# This file is part of Feren Solstice.
#
# Copyright 2020-2023 Dominic Hayes

from . import utils
import os
import gettext
gettext.install("solstice-python", "/usr/share/locale", names="ngettext")
import gi
from gi.repository import GLib
import shutil
import json
import filecmp

class SolsticeFirefoxException(Exception):
    pass


def updateProfile(parentinfo, appsettings, psettings, profiledir, csssettings):
    # Abort if the chrome folder for the CSS is somehow not present
    if not os.path.isdir("%s/chrome" % profiledir):
        raise SolsticeFirefoxException(_("The profile's chrome folder does not exist - it should have been created by updateCSS"))

    # Apply new defaults into profile
    for i in ["handlers.json", "user.js"]:
        shutil.copy("/usr/share/solstice/firefox/" + i, profiledir + "/" + i)
    
    # Set profile defaults specific to the profile-application configuration
    prefile = profiledir + "/user.js"
    try:
        with open(prefile, 'r') as fp:
            confs = fp.read().splitlines()
    except:
        raise SolsticeFirefoxException(_("Failed to load user.js"))
    
    for i, line in enumerate(confs):
        confs[i] = line.replace("WEBSITEHERE", parentinfo["website"])\
            .replace("NAMEHERE", parentinfo["name"])\
            .replace("DOWNLOADSDIRHERE", appsettings["lastdownloadsdir"] + "/" + appsettings["downloadsdirname"])
    # confs = setProfileName(parentinfo, psettings["readablename"], profiledir, confs)
    confs = setNoCache(psettings["nocache"], profiledir, confs)

    # Include Workspaces integration, and selected bonuses, into the profile
    # confs = setBonuses(profiledir, parentinfo["bonusids"], confs)

    # Set permissions for our websites and required services' websites
    # confs = setPermissions(confs, parentinfo)

    # Set Workspaces and History availability
    confs = setExtFeatures(confs, parentinfo["nohistory"], parentinfo["workspaces"])

    # Set the palette this application will use in the respective browsers
    setPalette(csssettings, profiledir, parentinfo)

    # Save to the user.js file
    try:
        with open(prefile, 'w') as fp:
            fp.write('\n'.join(confs))
    except Exception as exceptionstr:
        raise SolsticeFirefoxException(_("Failed to write to user.js"))


##########################################################
# CSS Settings
##########################################################

def updateCSSSettings(parentinfo, profiledir, csssettings):
    # Update the palette this application will use per the settings
    confdict = setPalette(csssettings, profiledir, parentinfo)


##########################################################
# Profile Updating
##########################################################

def setProfileName(parentinfo, newname, profiledir, confs=None):
    # if not os.path.isdir(profiledir):
    #     raise SolsticeChromiumException(_("The profile %s does not exist") % profiledir.split("/")[-1])
    
    patchfiles = (confs == None)
    # # user.js file
    # if confs == None:
    #     prefile = "%s/user.js" % profiledir
    #     if os.path.isfile(prefile): # Load user.js into variable if one exists
    #         with open(prefile, 'r') as fp:
    #             confs = fp.read().splitlines()

    # NOTE:
    # Firefox browsers DON'T have anything to do here.
    # Firefox-based browsers don't show profile names in the interface.
    
    if patchfiles:
        pass
        # # Save to user.js
        # try:
        #     with open(prefile, 'w') as fp:
        #         fp.write('\n'.join(confs))
        # except Exception as exceptionstr:
        #     raise SolsticeFirefoxException(_("Failed to write to user.js"))
    else:
        return confs


def setBonuses(profiledir, bonuses=[], confs=None):
    # if not os.path.isdir(profiledir):
    #     raise SolsticeChromiumException(_("The profile %s does not exist") % profiledir.split("/")[-1])
    
    patchfiles = (confs == None)
    # # user.js file
    # if confs == None:
    #     prefile = "%s/user.js" % profiledir
    #     if os.path.isfile(prefile): # Load user.js into variable if one exists
    #         with open(prefile, 'r') as fp:
    #             confs = fp.read().splitlines()

    # NOTE:
    # Firefox browsers DON'T have anything to do here.
    # There currently isn't a reliable way to install extensions onto
    # Firefox-based browsers (thus, bonuses aren't available).
    
    if patchfiles:
        pass
        # # Save to user.js
        # try:
        #     with open(prefile, 'w') as fp:
        #         fp.write('\n'.join(confs))
        # except Exception as exceptionstr:
        #     raise SolsticeFirefoxException(_("Failed to write to user.js"))
    else:
        return confs
    

def setNoCache(newbool, profiledir, confs=None):
    # TODO: Only run these functions if the profile is up-to-date and isn't running
    if not os.path.isdir(profiledir):
        raise SolsticeFirefoxException(_("The profile %s does not exist") % profiledir.split("/")[-1])

    patchfiles = (confs == None)
    # user.js file
    if confs == None:
        prefile = "%s/user.js" % profiledir
        if os.path.isfile(prefile): # Load user.js into variable if one exists
            with open(prefile, 'r') as fp:
                confs = fp.read().splitlines()
        else:
            raise SolsticeFirefoxException(_("user.js does not exist - the profile should have been updated instead of running this function"))
    
    valuestoadd = {"browser.cache.disk.enable": "false", "browser.cache.memory.enable": "false"}
    if newbool == False:
        valuestoadd["browser.cache.disk.enable"] = "true"
        valuestoadd["browser.cache.memory.enable"] = "true"

    # Check for and update existing values in user.js
    for i, line in enumerate(confs):
        for ii in valuestoadd:
            if line.startswith('user_pref("' + ii + '", '):
                confs[i] = 'user_pref("' + ii + '", ' + valuestoadd[ii] + ");"
                valuestoadd.pop(ii) # Ensure this value isn't duplicated later
                break # Exit loop to prevent throwing ListChanged
    
    # Add missing values to user.js, if any
    for i in valuestoadd:
        confs.append('user_pref("' + i + '", ' + valuestoadd[i] + ");")

    if patchfiles:
        # Save to user.js
        try:
            with open(prefile, 'w') as fp:
                fp.write('\n'.join(confs))
        except Exception as exceptionstr:
            raise SolsticeFirefoxException(_("Failed to write to user.js"))
    else:
        return confs


def setPermissions(confs, parentinfo):
    # # Open the Services file
    # with open("/usr/share/solstice/info/services.json", 'r') as fp:
    #     services = json.loads(fp.read())

    # # Collate websites to grant permissions to
    # websites = [utils.shortenURL(parentinfo["website"])] # Main website
    # for i in parentinfo["childwebsites"]: # Child websites
    #     ii = utils.shortenURL(i)
    #     try:
    #         ii = ii.split("/")[0]
    #     except:
    #         pass
    #     websites.append(ii)
    # for i in parentinfo["services"]: # Required services' domains
    #     if i in services:
    #         for ii in services[i]:
    #             websites.append(services[i][ii])
    
    # NOTE:
    # Firefox browsers DON'T have anything to do here.
    # There currently isn't a reliable way to manage website
    # permissions in Firefox-based browsers.
    
    return confs
    

def setExtFeatures(confs, nohistory, workspaces):
    valuestoadd = {"privacy.clearOnShutdown.history": "false", "browser.startup.page": "1", "floorp.browser.workspaces.enabled": "false"}
    if nohistory == True:
        valuestoadd["privacy.clearOnShutdown.history"] = "true"
    if workspaces == True:
        valuestoadd["browser.startup.page"] = "3"
        valuestoadd["floorp.browser.workspaces.enabled"] = "true"

    # Check for and update existing values in user.js
    for i, line in enumerate(confs):
        for ii in valuestoadd:
            if line.startswith('user_pref("' + ii + '", '):
                confs[i] = 'user_pref("' + ii + '", ' + valuestoadd[ii] + ");"
                valuestoadd.pop(ii) # Ensure this value isn't duplicated later
                break # Exit loop to prevent throwing ListChanged
    
    # Add missing values to user.js, if any
    for i in valuestoadd:
        confs.append('user_pref("' + i + '", ' + valuestoadd[i] + ");")

    return confs


#Colourise the Firefox interface
def setPalette(csssettings, profiledir, parentinfo):
    visuallyconnectedtabs = False #Account for Mozilla's... design decisions
    # Override if CSS states wanting otherwise
    if "connectedtabs" in csssettings:
        if csssettings["connectedtabs"] == True:
            visuallyconnectedtabs = True

    # Copy Solstice's Firefox CSS
    for i in ["userChrome.css", "userContent.css", "GTKless.css", "solstice.css"]:
        shutil.copy("/usr/share/solstice/firefox/chrome/" + i, profiledir + "/chrome/" + i)

    # Get header, tab and page colours appropriate to the visual tabs connection or lack-of
    if visuallyconnectedtabs == True:
        lighthdr, darkhdr = parentinfo["connheaderlight"], parentinfo["connheaderdark"]
        lighttab, darktab = parentinfo["conntablight"], parentinfo["conntabdark"]
        lightpage, darkpage = parentinfo["connsitelight"], parentinfo["connsitedark"]
    else:
        lighthdr, darkhdr = parentinfo["headerlight"], parentinfo["headerdark"]
        lighttab, darktab = parentinfo["tablight"], parentinfo["tabdark"]
        lightpage, darkpage = parentinfo["sitelight"], parentinfo["sitedark"]

    # Assemble remaining colour palette for the CSS
    #  Private (NOTE: Colour palette is the same regardless of connected tabs option)
    privatehdr = utils.colourFilter(parentinfo["accent"], -70.0)
    privatetab = utils.colourFilter(parentinfo["accent"], -46.0)
    privatepage = privatehdr

    #  Foregrounds - Header (Private)
    privatehdrfg, privatehdrfgrgb = ("#000000", "rgba(0, 0, 0, ") if utils.colourIsLight(privatehdr) == True else ("#FFFFFF", "rgba(255, 255, 255, ")

    #  Foregrounds - Tabs (Private)
    privatetabfg = "#000000" if utils.colourIsLight(privatetab) == True else "#FFFFFF"

    #  Foregrounds - Pages (Private)
    #   NOTE: Same colours as titlebar
    privatepagefg = privatehdrfg

    #  Foregrounds - Titlebar
    lighthdrfg, lighthdrfgrgb = ("#000000", "rgba(0, 0, 0, ") if utils.colourIsLight(lighthdr) == True else ("#FFFFFF", "rgba(255, 255, 255, ")
    darkhdrfg, darkhdrfgrgb = ("#000000", "rgba(0, 0, 0, ") if utils.colourIsLight(darkhdr) == True else ("#FFFFFF", "rgba(255, 255, 255, ")

    #  Foregrounds - Tabs
    lighttabfg = "#000000" if utils.colourIsLight(lighttab) == True else "#FFFFFF"
    darktabfg = "#000000" if utils.colourIsLight(darktab) == True else "#FFFFFF"

    #  Foregrounds - Pages
    lightpagefg = "#000000" if utils.colourIsLight(lightpage) == True else "#FFFFFF"
    darkpagefg = "#000000" if utils.colourIsLight(darkpage) == True else "#FFFFFF"

    #  Foregrounds - Accent Colour
    accentfg = "#000000" if utils.colourIsLight(parentinfo["accent"]) == True else "#FFFFFF"
    darkaccentfg = "#000000" if utils.colourIsLight(parentinfo["accentdark"]) == True else "#FFFFFF"

    # Swap/change colours if they do not provide contrast or are too similar to other colours
    #  Accent in titlebar
    if utils.coloursDiffer(parentinfo["accent"], lighthdr):
        accenthdrbg, accenthdrfg = parentinfo["accent"], accentfg
    else:
        accenthdrbg, accenthdrfg = accentfg, parentinfo["accent"]
    
    #  Accent in titlebar (Dark)
    if utils.coloursDiffer(parentinfo["accentdark"], darkhdr):
        accenthdrbgdark, accenthdrfgdark = parentinfo["accentdark"], darkaccentfg
    else:
        accenthdrbgdark, accenthdrfgdark = darkaccentfg, parentinfo["accentdark"]
    
    #  Accent in tabs
    if utils.coloursDiffer(parentinfo["accent"], lighttab):
        accenttabbg, accenttabfg = parentinfo["accent"], accentfg
    else:
        accenttabbg, accenttabfg = accentfg, parentinfo["accent"]
    
    #  Accent in tabs (Dark)
    if utils.coloursDiffer(parentinfo["accentdark"], darktab):
        accenttabbgdark, accenttabfgdark = parentinfo["accentdark"], darkaccentfg
    else:
        accenttabbgdark, accenttabfgdark = darkaccentfg, parentinfo["accentdark"]
    
    #  Accent in pages
    if utils.coloursDiffer(parentinfo["accent"], lightpage):
        accentpagebg, accentpagefg = parentinfo["accent"], accentfg
    else:
        accentpagebg, accentpagefg = accentfg, parentinfo["accent"]
    
    #  Accent in pages (Dark)
    if utils.coloursDiffer(parentinfo["accentdark"], darkpage):
        accentpagebgdark, accentpagefgdark = parentinfo["accentdark"], darkaccentfg
    else:
        accentpagebgdark, accentpagefgdark = darkaccentfg, parentinfo["accentdark"]
    
    #  Visually connected palette
    if visuallyconnectedtabs == True:
        connbg, connfg, connbgdark, connfgdark = lighttab, lighttabfg, darktab, darktabfg
        connbgprivate, connfgprivate = privatetab, privatetabfg
    else:
        connbg, connfg, connbgdark, connfgdark = lighthdr, lighthdrfg, darkhdr, darkhdrfg
        connbgprivate, connfgprivate = privatehdr, privatehdrfg
    # Use page colour in about:*

    # Write to CSS file
    with open(profiledir + "/chrome/solstice.css", 'r') as fp:
        result = fp.read().splitlines()
    i = 0
    while i < len(result):
        result[i] = result[i]\
            .replace("AccentBGLight", parentinfo["accent"]).replace("AccentFGLight", accentfg)\
            .replace("AccentBGDark", parentinfo["accentdark"]).replace("AccentFGDark", darkaccentfg)\
            .replace("AccentHdrBGLight", accenthdrbg).replace("AccentHdrFGLight", accenthdrfg)\
            .replace("AccentHdrBGDark", accenthdrbgdark).replace("AccentHdrFGDark", accenthdrfgdark)\
            .replace("AccentTabBGLight", accenttabbg).replace("AccentTabFGLight", accenttabfg)\
            .replace("AccentTabBGDark", accenttabbgdark).replace("AccentTabFGDark", accenttabfgdark)\
            .replace("AccentPageBGLight", accentpagebg).replace("AccentPageFGLight", accentpagefg)\
            .replace("AccentPageBGDark", accentpagebgdark).replace("AccentPageFGDark", accentpagefgdark)\
            .replace("HdrBGLight", lighthdr).replace("HdrFGLight", lighthdrfg)\
            .replace("HdrBGDark", darkhdr).replace("HdrFGDark", darkhdrfg)\
            .replace("TabBGLight", lighttab).replace("TabFGLight", lighttabfg)\
            .replace("TabBGDark", darktab).replace("TabFGDark", darktabfg)\
            .replace("PageBGLight", lightpage).replace("PageFGLight", lightpagefg)\
            .replace("PageBGDark", darkpage).replace("PageFGDark", darkpagefg)\
            .replace("HdrFG02Light", lighthdrfgrgb + "0.2)").replace("HdrFG03Light", lighthdrfgrgb + "0.3)")\
            .replace("HdrFG02Dark", darkhdrfgrgb + "0.2)").replace("HdrFG03Dark", darkhdrfgrgb + "0.3)")\
            .replace("PrivateHdrFG02", privatehdrfgrgb + "0.2)").replace("PrivateHdrFG03", privatehdrfgrgb + "0.3)")\
            .replace("PrivateHdrBG", privatehdr).replace("PrivateHdrFG", privatehdrfg)\
            .replace("PrivateTabBG", privatetab).replace("PrivateTabFG", privatetabfg)\
            .replace("PrivatePageBG", privatepage).replace("PrivatePageFG", privatepagefg)\
            .replace("ConnBGLight", connbg).replace("ConnFGLight", connfg)\
            .replace("ConnBGDark", connbgdark).replace("ConnFGDark", connfgdark)
        if " /* Special condition for adaptivebg - light */" in result[i]:
            if utils.coloursDiffer(accentpagebg, lightpagefg): #If the selected colour is not the exact same as the page foreground colour,
                result.pop(i+2) #then disable the contrast improver
                result.pop(i+1)
                result.pop(i)
                result.pop(i-1)
                i -= 1 #We removed the prior line, so go back one line.
                continue
        elif " /* Special condition for adaptivebg - dark */" in result[i]:
            if utils.coloursDiffer(accentpagebgdark, darkpagefg):
                result.pop(i+2)
                result.pop(i+1)
                result.pop(i)
                result.pop(i-1)
                i -= 1
                continue
        elif " /* CSS Option - disable tab shadows */" in result[i]:
            if visuallyconnectedtabs == True or parentinfo["tabhasshadow"] == True:
                result.pop(i+3)
                result.pop(i+2)
                result.pop(i+1)
                result.pop(i)
                result.pop(i-1)
                i -= 1
                continue
        i += 1

    # Save changes
    try:
        with open(profiledir + "/chrome/solstice.css", 'w') as fp:
            fp.write('\n'.join(result))
    except Exception as e:
        raise SolsticeFirefoxException(_("Writing solstice.css failed: %e") % e)
