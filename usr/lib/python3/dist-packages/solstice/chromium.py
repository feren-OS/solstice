# This file is part of Feren Solstice.
#
# Copyright 2020-2023 Dominic Hayes

from . import utils
import os
import gettext
gettext.install("solstice-python", "/usr/share/locale", names="ngettext")
import gi
from gi.repository import GLib
import json
import shutil

class SolsticeChromiumException(Exception):
    pass

def update_profile(iteminfo, extrawebsites, profilename, profilepath, nocache, skiptheme, downloadsdir, downloadsname):
    #dict, list, string, string, bool, bool
    if not os.path.isdir("%s/Default" % profilepath):
        try:
            os.mkdir("%s/Default" % profilepath)
        except Exception as e:
            raise SolsticeChromiumException(_("Failed to create the profile's Chromium Preferences folder: %s") % e)
    PreferencesFile = "%s/Default/Preferences" % profilepath

    result, defaultprefs = {}, {}
    if os.path.isfile(PreferencesFile): #Load old Preferences into variable if one exists
        with open(PreferencesFile, 'r') as fp:
            result = json.loads(fp.read())
    with open("/usr/share/solstice/chromium/Preferences", 'r') as fp: #Also load default browser preferences, so we can patch
        defaultprefs = json.loads(fp.read())["general"]

    #Don't override certain settings in existing profiles
    if "session" in result: #Restore on startup preference
        if "restore_on_startup" in result["session"]:
            defaultprefs["session"].pop("restore_on_startup")
    if "webkit" in result: #Font preferences
        if "webprefs" in result["webkit"]:
            if "fonts" in result["webkit"]["webprefs"]:
                for i in "fixed", "sansserif", "serif", "standard":
                    if i in result["webkit"]["webprefs"]["fonts"]:
                        if "Zyyy" in result["webkit"]["webprefs"]["fonts"][i]:
                            defaultprefs["webkit"]["webprefs"]["fonts"][i].pop("Zyyy")
    #Don't override theme settings if they're manually changed
    if "extensions" in result: #Current theme
        if "theme" in result["extensions"]:
            if "id" in result["extensions"]["theme"]:
                defaultprefs["extensions"]["theme"].pop("id")
    if "vivaldi" in result: #Current theme (Vivaldi)
        if "themes" in result["vivaldi"]:
            if "current" in result["vivaldi"]["themes"]:
                defaultprefs["vivaldi"]["themes"].pop("current")
        if "theme" in result["vivaldi"]:
            if "schedule" in result["vivaldi"]["theme"]:
                if "enabled" in result["vivaldi"]["theme"]["schedule"]:
                    defaultprefs["vivaldi"]["theme"]["schedule"].pop("enabled")
                if "o_s" in result["vivaldi"]["theme"]["schedule"]:
                    for i in "dark", "light":
                        if i in result["vivaldi"]["theme"]["schedule"]["o_s"] and\
                        result["vivaldi"]["theme"]["schedule"]["o_s"][i] != "ice" and\
                        result["vivaldi"]["theme"]["schedule"]["o_s"][i] != "ice-dark":
                            defaultprefs["vivaldi"]["theme"]["schedule"]["o_s"].pop(i)
    #Update configurations in Preferences
    result = utils.dict_recurupdate(result, defaultprefs)

    #Set important settings unique to each SSB
    result["homepage"] = iteminfo["website"]
    result["custom_links"]["list"][0]["title"] = iteminfo["name"]
    result["custom_links"]["list"][0]["url"] = iteminfo["website"]
    result["session"]["startup_urls"] = [iteminfo["website"]]
    result["download"]["default_directory"] = downloadsdir + "/" + downloadsname
    result["ntp"]["custom_background_dict"]["attribution_line_1"] = _("{0} - {1}").format(profilename, iteminfo["name"])
    result["vivaldi"]["homepage"] = iteminfo["website"]
    result["vivaldi"]["homepage_cache"] = iteminfo["website"]

    #Set the profile's name
    result = change_profile_name(profilepath, iteminfo["name"], profilename, True, result)

    #Set no cache preference
    result = set_profile_nocache(profilepath, nocache, True, result)

    #Set permissions for the initial website
    result = chromi_set_sitepermissions(result, iteminfo["id"], iteminfo["website"], extrawebsites)

    #Toggle features for the SSB
    result = chromi_set_additionalfeatures(result, iteminfo["nohistory"], iteminfo["googlehangouts"], iteminfo["workspaces"])

    #Add bonuses to SSB
    result = chromi_set_bonuses(result, iteminfo["bonusids"])

    #Add theme colours to SSB (Vivaldi) and Chromium
    result = chromi_set_colors(result, iteminfo["bg"], iteminfo["bgdark"], iteminfo["accent"], iteminfo["accentdark"], iteminfo["color"], iteminfo["colordark"], iteminfo["accentonwindow"], profilepath, skiptheme)

    #Add the Start Page Bookmark
    chromi_add_startpage(profilepath, iteminfo["name"], iteminfo["website"])

    #Add in CSS and custom CSS
    result["vivaldi"]["appearance"]["css_ui_mods_directory"] = "%s/CSS/vivaldi" % profilepath
    # Normal CSS
    if os.path.isdir("%s/CSS" % profilepath):
        shutil.rmtree("%s/CSS" % profilepath)
    if iteminfo["browsertype"] == "chromium" and iteminfo["browser"] == "vivaldi":
        os.mkdir("%s/CSS" % profilepath)
        os.mkdir("%s/CSS/vivaldi" % profilepath)
        shutil.copyfile("/usr/share/solstice/vivaldicss/browser.css", "%s/CSS/vivaldi/main.css" % profilepath)
    # Custom CSS
    if os.path.isfile(os.path.expanduser("~") + "/.config/solstice/vivaldi.css"):
        shutil.copyfile(os.path.expanduser("~") + "/.config/solstice/vivaldi.css", "%s/CSS/vivaldi/custom.css" % profilepath)

    #Remove theme if disabled on this browser
    if skiptheme == True:
        result["extensions"]["settings"].pop("aghfnjkcakhmadgdomlmlhhaocbkloab")

    #Save to the Preferences file
    try:
        with open(PreferencesFile, 'w') as fp:
            fp.write(json.dumps(result, separators=(',', ':'))) # This dumps minified json (how convenient), which is EXACTLY what Chrome uses for Preferences, so it's literally pre-readied
    except Exception as exceptionstr:
        raise SolsticeChromiumException(_("Failed to write to Preferences"))

    #Finally, configure Local State
    chromi_update_local_state(profilepath)

    #and finish off with this:
    chromi_finishing_touches(profilepath)


#Profile Name
def change_profile_name(profilepath, itemname, value, patchvar=False, vartopatch={}):
    #string, string
    if not os.path.isdir(profilepath):
        raise SolsticeChromiumException(_("The profile %s does not exist") % profilepath.split("/")[-1])
    PreferencesFile = "%s/Default/Preferences" % profilepath

    if patchvar == False: #Allow this to also be used in update_profile without causing an additional file-write
        result = {}
        if os.path.isfile(PreferencesFile): #Load old Preferences into variable if one exists
            with open(PreferencesFile, 'r') as fp:
                result = json.loads(fp.read())
    else:
        result = vartopatch

    #Update configurations in Preferences
    result["profile"]["name"] = _("{0} - {1}").format(value, itemname)

    if patchvar == False:
        #Save to the Preferences file
        try:
            with open(PreferencesFile, 'w') as fp:
                fp.write(json.dumps(result, separators=(',', ':')))
        except Exception as exceptionstr:
            raise SolsticeChromiumException(_("Failed to write to Preferences"))
        change_profile_name_ls(profilepath) #Only run this when called externally
    else:
        return result

def change_profile_name_ls(profilepath, patchvar=False, vartopatch={}):
    #string
    if not os.path.isdir(profilepath):
        raise SolsticeChromiumException(_("The profile %s does not exist") % profilepath.split("/")[-1])
    LocalState = "%s/Local State" % profilepath

    if patchvar == False: #Allow this to also be used in chromi_update_local_state without causing an additional file-write
        result = {}
        if os.path.isfile(LocalState): #Load old Local State into variable if one exists
            with open(LocalState, 'r') as fp:
                result = json.loads(fp.read())
    else:
        result = vartopatch

    if "profile" in result: #Remove cached profile name
        if "info_cache" in result["profile"]:
            if "Default" in result["profile"]["info_cache"]:
                result["profile"]["info_cache"].pop("Default")

    if patchvar == False:
        #Save to the Local State
        try:
            with open(LocalState, 'w') as fp:
                fp.write(json.dumps(result, separators=(',', ':')))
        except Exception as exceptionstr:
            raise SolsticeChromiumException(_("Failed to write to Local State"))
    else:
        return result


#No Cache
def set_profile_nocache(profilepath, value, patchvar=False, vartopatch={}):
    #string, bool
    if not os.path.isdir(profilepath):
        raise SolsticeChromiumException(_("The profile %s does not exist") % profilepath.split("/")[-1])
    PreferencesFile = "%s/Default/Preferences" % profilepath

    #NOTE: Chromiums have no cache occur via commandline arguments, so there is no need to do anything here right now
    if patchvar == False: #Allow this to also be used in update_profile without causing an additional file-write
        return
    else:
        return vartopatch


#Default Settings
def chromi_set_sitepermissions(preferencedict, itemid, ogwebsite, extrawebsites):
    #dict, string, list

    #Set the permissions for default website in this SSB
    shortenedurl = utils.shorten_url(ogwebsite)
    for permtype in ["ar", "autoplay", "automatic_downloads", "background_sync", "clipboard", "file_handling", "font_access", "local_fonts", "midi_sysex", "notifications", "payment_handler", "sensors", "sound", "sleeping-tabs", "window_placement", "vr"]:
        preferencedict["profile"]["content_settings"]["exceptions"][permtype] = {}
        preferencedict["profile"]["content_settings"]["exceptions"][permtype]["[*.]"+shortenedurl+",*"] = {"expiration": "0", "model": 0, "setting": 1}
        preferencedict["profile"]["content_settings"]["exceptions"][permtype][shortenedurl+",*"] = {"expiration": "0", "model": 0, "setting": 1}
    for permtype in ["file_system_write_guard", "hid_guard"]:
        preferencedict["profile"]["content_settings"]["exceptions"][permtype] = {}
        preferencedict["profile"]["content_settings"]["exceptions"][permtype]["[*.]"+shortenedurl+",*"] = {"expiration": "0", "model": 0, "setting": 3}
        preferencedict["profile"]["content_settings"]["exceptions"][permtype][shortenedurl+",*"] = {"expiration": "0", "model": 0, "setting": 3}

    #Set the permissions for extra websites in this SSB
    for extrawebsite in extrawebsites:
        shortenedurl = utils.shorten_url(extrawebsite)
        try:
            shortenedurl = shortenedurl.split("/")[0]
        except:
            pass
        for permtype in ["ar", "autoplay", "automatic_downloads", "background_sync", "clipboard", "file_handling", "font_access", "local_fonts", "midi_sysex", "notifications", "payment_handler", "sensors", "sound", "sleeping-tabs", "window_placement", "vr"]:
            preferencedict["profile"]["content_settings"]["exceptions"][permtype]["[*.]"+shortenedurl+",*"] = {"expiration": "0", "model": 0, "setting": 1}
            preferencedict["profile"]["content_settings"]["exceptions"][permtype][shortenedurl+",*"] = {"expiration": "0", "model": 0, "setting": 1}
        for permtype in ["file_system_write_guard", "hid_guard"]:
            preferencedict["profile"]["content_settings"]["exceptions"][permtype]["[*.]"+shortenedurl+",*"] = {"expiration": "0", "model": 0, "setting": 3}
            preferencedict["profile"]["content_settings"]["exceptions"][permtype][shortenedurl+",*"] = {"expiration": "0", "model": 0, "setting": 3}

    #Return the modified Preferences
    return preferencedict


#Vivaldi and Brave settings
def chromi_set_additionalfeatures(preferencedict, nohistory=False, allowgooglehangouts=False, allowworkspaces=False):
    #dict, bool, bool, bool

    #First, open the Preferences file
    with open("/usr/share/solstice/chromium/preferences.json", 'r') as fp:
        preferencesjson = json.loads(fp.read())

    if not allowgooglehangouts: #Disable Google Hangouts if unneeded
        preferencedict = utils.dict_recurupdate(preferencedict, preferencesjson["disable-googlehangouts"])
    if not allowworkspaces: #Disable Workspaces if unneeded
        preferencedict = utils.dict_recurupdate(preferencedict, preferencesjson["disable-workspaces"])
    if nohistory: #Disable History if the SSB provides History itself
        preferencedict = utils.dict_recurupdate(preferencedict, preferencesjson["disable-history"])

    #Return the modified Preferences
    return preferencedict


#Bonuses
def chromi_set_bonuses(preferencedict, bonuses=[]):
    #dict, list

    #First, open the Extras file
    with open("/usr/share/solstice/chromium/bonuses.json", 'r') as fp:
        bonusesjson = json.loads(fp.read())

    #First, add the bonuses that were chosen
    for item in bonuses:
        if item in bonusesjson:
            #Check that the extension isn't already installed
            for extensionid in bonusesjson[item]["extensions"]["settings"]:
                if extensionid in preferencedict["extensions"]["settings"]:
                    #If it is, clear out stuff that would uninstall the extra if installed
                    bonusesjson[item]["extensions"]["settings"][extensionid].pop("path", None)
                    bonusesjson[item]["extensions"]["settings"][extensionid]["manifest"].pop("name", None)
                    bonusesjson[item]["extensions"]["settings"][extensionid]["manifest"].pop("version", None)
            #Now that is done, install extra to profile
            preferencedict = utils.dict_recurupdate(preferencedict, bonusesjson[item])
    #Second, we remove bonuses no longer selected
    for item in bonusesjson:
        if not item in bonuses:
            for extensionid in bonusesjson[item]["extensions"]["settings"]:
                preferencedict["extensions"]["settings"].pop(extensionid, None)

    #Now, return the modified Preferences
    return preferencedict


#Theme colouring
def chromi_set_colors(preferencedict, bg, bgdark, accent, accentdark, color, colordark, accentonwindow, profilepath, skiptheme):
    #dict, string, string, string, string, string, bool

    def color_to_rgb(hexcode, includefourth=False):
        redc, greenc, bluec = tuple(int(hexcode[i:i+2], 16) for i in (1, 3, 5)) #Dodge the # character

        return [redc, greenc, bluec] if includefourth == False else [redc, greenc, bluec, 1]

    #Chromium and co.
    if os.path.isdir(profilepath + "/Default/Extensions/aghfnjkcakhmadgdomlmlhhaocbkloab"):
        try:
            shutil.rmtree(profilepath + "/Default/Extensions/aghfnjkcakhmadgdomlmlhhaocbkloab")
        except Exception as e:
            raise SolsticeChromiumException(_("Failed to prepare to update a profile dependency: %s") % e)
    if skiptheme == False:
        if accentonwindow == True:
            preferencedict["extensions"]["settings"]["aghfnjkcakhmadgdomlmlhhaocbkloab"]["manifest"]["theme"]["colors"]["bookmark_text"] = [0, 0, 0] if utils.color_is_light(bg) == True else [255, 255, 255] #Bookmark's text
            preferencedict["extensions"]["settings"]["aghfnjkcakhmadgdomlmlhhaocbkloab"]["manifest"]["theme"]["colors"]["button_background"] = color_to_rgb(accent) #Titlebar buttons (unused)
            preferencedict["extensions"]["settings"]["aghfnjkcakhmadgdomlmlhhaocbkloab"]["manifest"]["theme"]["colors"]["frame"] = color_to_rgb(accent) #Titlebar
            preferencedict["extensions"]["settings"]["aghfnjkcakhmadgdomlmlhhaocbkloab"]["manifest"]["theme"]["colors"]["frame_inactive"] = color_to_rgb(accent) #Titlebar (inactive)
            preferencedict["extensions"]["settings"]["aghfnjkcakhmadgdomlmlhhaocbkloab"]["manifest"]["theme"]["colors"]["ntp_background"] = color_to_rgb(bg) #Self-explanatory
            preferencedict["extensions"]["settings"]["aghfnjkcakhmadgdomlmlhhaocbkloab"]["manifest"]["theme"]["colors"]["ntp_link"] = [0, 0, 0] if utils.color_is_light(bg) == True else [255, 255, 255] #NTP link (unused)
            preferencedict["extensions"]["settings"]["aghfnjkcakhmadgdomlmlhhaocbkloab"]["manifest"]["theme"]["colors"]["ntp_text"] = [0, 0, 0] if utils.color_is_light(bg) == True else [255, 255, 255] #NTP item-text
            preferencedict["extensions"]["settings"]["aghfnjkcakhmadgdomlmlhhaocbkloab"]["manifest"]["theme"]["colors"]["omnibox_background"] = color_to_rgb(utils.color_filter(bg, 15.3)) if utils.color_is_light(bg) == True else color_to_rgb(utils.color_filter(bg, -23.0)) #Omnibox
            preferencedict["extensions"]["settings"]["aghfnjkcakhmadgdomlmlhhaocbkloab"]["manifest"]["theme"]["colors"]["omnibox_text"] = [0, 0, 0] if utils.color_is_light(bg) == True else [255, 255, 255] #Omnibox text
            preferencedict["extensions"]["settings"]["aghfnjkcakhmadgdomlmlhhaocbkloab"]["manifest"]["theme"]["colors"]["tab_background_text"] = [0, 0, 0] if utils.color_is_light(accent) == True else [255, 255, 255] #Titlebar text
            preferencedict["extensions"]["settings"]["aghfnjkcakhmadgdomlmlhhaocbkloab"]["manifest"]["theme"]["colors"]["tab_background_text_inactive"] = [0, 0, 0] if utils.color_is_light(accent) == True else [255, 255, 255] #Titlebar text (inactive)
            preferencedict["extensions"]["settings"]["aghfnjkcakhmadgdomlmlhhaocbkloab"]["manifest"]["theme"]["colors"]["tab_text"] = [0, 0, 0] if utils.color_is_light(bg) == True else [255, 255, 255] #Active tab's text
            preferencedict["extensions"]["settings"]["aghfnjkcakhmadgdomlmlhhaocbkloab"]["manifest"]["theme"]["colors"]["toolbar"] = color_to_rgb(bg) #Toolbar
            preferencedict["extensions"]["settings"]["aghfnjkcakhmadgdomlmlhhaocbkloab"]["manifest"]["theme"]["colors"]["toolbar_button_icon"] = [0, 0, 0] if utils.color_is_light(bg) == True else [255, 255, 255] #Toolbar icons
            preferencedict["extensions"]["settings"]["aghfnjkcakhmadgdomlmlhhaocbkloab"]["manifest"]["theme"]["colors"]["toolbar_text"] = [0, 0, 0] if utils.color_is_light(bg) == True else [255, 255, 255] #Toolbar text
        else:
            preferencedict["extensions"]["settings"]["aghfnjkcakhmadgdomlmlhhaocbkloab"]["manifest"]["theme"]["colors"]["bookmark_text"] = [0, 0, 0] if utils.color_is_light(accent) == True else [255, 255, 255]
            preferencedict["extensions"]["settings"]["aghfnjkcakhmadgdomlmlhhaocbkloab"]["manifest"]["theme"]["colors"]["button_background"] = color_to_rgb(bg)
            preferencedict["extensions"]["settings"]["aghfnjkcakhmadgdomlmlhhaocbkloab"]["manifest"]["theme"]["colors"]["frame"] = color_to_rgb(bg)
            preferencedict["extensions"]["settings"]["aghfnjkcakhmadgdomlmlhhaocbkloab"]["manifest"]["theme"]["colors"]["frame_inactive"] = color_to_rgb(bg)
            preferencedict["extensions"]["settings"]["aghfnjkcakhmadgdomlmlhhaocbkloab"]["manifest"]["theme"]["colors"]["ntp_background"] = color_to_rgb(accent)
            preferencedict["extensions"]["settings"]["aghfnjkcakhmadgdomlmlhhaocbkloab"]["manifest"]["theme"]["colors"]["ntp_link"] = [0, 0, 0] if utils.color_is_light(accent) == True else [255, 255, 255]
            preferencedict["extensions"]["settings"]["aghfnjkcakhmadgdomlmlhhaocbkloab"]["manifest"]["theme"]["colors"]["ntp_text"] = [0, 0, 0] if utils.color_is_light(accent) == True else [255, 255, 255]
            preferencedict["extensions"]["settings"]["aghfnjkcakhmadgdomlmlhhaocbkloab"]["manifest"]["theme"]["colors"]["omnibox_background"] = color_to_rgb(bg)
            preferencedict["extensions"]["settings"]["aghfnjkcakhmadgdomlmlhhaocbkloab"]["manifest"]["theme"]["colors"]["omnibox_text"] = [0, 0, 0] if utils.color_is_light(bg) == True else [255, 255, 255]
            preferencedict["extensions"]["settings"]["aghfnjkcakhmadgdomlmlhhaocbkloab"]["manifest"]["theme"]["colors"]["tab_background_text"] = [0, 0, 0] if utils.color_is_light(bg) == True else [255, 255, 255]
            preferencedict["extensions"]["settings"]["aghfnjkcakhmadgdomlmlhhaocbkloab"]["manifest"]["theme"]["colors"]["tab_background_text_inactive"] = [0, 0, 0] if utils.color_is_light(bg) == True else [255, 255, 255]
            preferencedict["extensions"]["settings"]["aghfnjkcakhmadgdomlmlhhaocbkloab"]["manifest"]["theme"]["colors"]["tab_text"] = [0, 0, 0] if utils.color_is_light(accent) == True else [255, 255, 255]
            preferencedict["extensions"]["settings"]["aghfnjkcakhmadgdomlmlhhaocbkloab"]["manifest"]["theme"]["colors"]["toolbar"] = color_to_rgb(accent)
            preferencedict["extensions"]["settings"]["aghfnjkcakhmadgdomlmlhhaocbkloab"]["manifest"]["theme"]["colors"]["toolbar_button_icon"] = [0, 0, 0] if utils.color_is_light(accent) == True else [255, 255, 255]
            preferencedict["extensions"]["settings"]["aghfnjkcakhmadgdomlmlhhaocbkloab"]["manifest"]["theme"]["colors"]["toolbar_text"] = [0, 0, 0] if utils.color_is_light(accent) == True else [255, 255, 255]

        # Update the fake theme accordingly
        if not os.path.isdir(profilepath + "/Default/Extensions"):
            try:
                os.mkdir(profilepath + "/Default/Extensions")
            except Exception as e:
                raise SolsticeChromiumException(_("Failed to create the profile's Chromium Extensions folder: %s") % e)
        for i in ["/Default/Extensions/aghfnjkcakhmadgdomlmlhhaocbkloab", "/Default/Extensions/aghfnjkcakhmadgdomlmlhhaocbkloab/99_0"]:
            try:
                os.mkdir(profilepath + i)
            except Exception as e:
                raise SolsticeChromiumException(_("Failed to create a profile dependency folder: %s") % e)
        try:
            with open(profilepath + "/Default/Extensions/aghfnjkcakhmadgdomlmlhhaocbkloab/99_0/manifest.json", 'w') as fp:
                result = {"key": "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAqxThvdYeWk6kwfNo+/HoqQSkL6iBx48w28vEPXHdhJo8OHMxS7D+1W1nhUsv4hOnb1CM2TlP/Nh9G+1Z32R9r6RmVxD1Anq9ZTZpK7VHVUxExGR4X9+TYHKWk8VGAjSBmutvayf0i0gCEkh7Pdc68ex4M0ypKGFWxBzxqw2uQ/4BLMVB/9KZJwXOC5LcaBNgq2Q74J3Dd3a90OzFXh+vC9zIyDueu3/K4F6u5bXgsgviAGIrUm7YbGhLDMxuW81zvYMlLtkA4XDDnhgk88s0G/5OwoMEyU6YdMq9R795NHsI0bPUMOOgUsPT5cytKRcQMegMassBe9EB+ktTl9CloQIDAQAB", \
                    "manifest_version": 3, "name": "Solstice", "theme": {}, "version": "99"}
                fp.write(json.dumps(result, separators=(',', ':')))
        except Exception as exceptionstr:
            raise SolsticeChromiumException(_("Failed to prepare a profile dependency"))

    #Vivaldi
    # Ensure 'colour' usage doesn't camoflague in the tab/dialogs colour
    coloradaptive = ("#000000" if utils.color_is_light(color) else "#FFFFFF") if not utils.are_colours_different(color, bg) else color
    coloradaptivedark = ("#000000" if utils.color_is_light(colordark) else "#FFFFFF") if not utils.are_colours_different(colordark, bgdark) else colordark
    bgprivate = utils.color_filter(color, -70.0)
    preferencedict["vivaldi"]["themes"]["system"][0]["accentOnWindow"] = accentonwindow
    preferencedict["vivaldi"]["themes"]["system"][1]["accentOnWindow"] = accentonwindow
    preferencedict["vivaldi"]["themes"]["system"][2]["accentOnWindow"] = False
    preferencedict["vivaldi"]["themes"]["system"][0]["colorAccentBg"] = accent
    preferencedict["vivaldi"]["themes"]["system"][1]["colorAccentBg"] = accentdark
    preferencedict["vivaldi"]["themes"]["system"][2]["colorAccentBg"] = utils.color_filter(color, -46.0)
    preferencedict["vivaldi"]["themes"]["system"][0]["colorBg"] = bg
    preferencedict["vivaldi"]["themes"]["system"][1]["colorBg"] = bgdark
    preferencedict["vivaldi"]["themes"]["system"][2]["colorBg"] = bgprivate
    preferencedict["vivaldi"]["themes"]["system"][0]["colorHighlightBg"] = coloradaptive
    preferencedict["vivaldi"]["themes"]["system"][1]["colorHighlightBg"] = coloradaptivedark
    preferencedict["vivaldi"]["themes"]["system"][2]["colorHighlightBg"] = color
    preferencedict["vivaldi"]["themes"]["system"][0]["colorWindowBg"] = accent if accentonwindow else bg
    preferencedict["vivaldi"]["themes"]["system"][1]["colorWindowBg"] = accentdark if accentonwindow else bgdark
    preferencedict["vivaldi"]["themes"]["system"][2]["colorWindowBg"] = bgprivate
    #Now set text colours where appropriate
    # Normal foregrounds
    preferencedict["vivaldi"]["themes"]["system"][0]["colorFg"] = "#000000" if utils.color_is_light(bg) else "#FFFFFF"
    preferencedict["vivaldi"]["themes"]["system"][1]["colorFg"] = "#000000" if utils.color_is_light(bgdark) else "#FFFFFF"
    # Private foregrounds
    preferencedict["vivaldi"]["themes"]["system"][2]["colorFg"] = "#000000" if utils.color_is_light(bgprivate) else "#FFFFFF"

    #Return the modified Preferences
    return preferencedict


#Local State
def chromi_update_local_state(profilepath):
    #string, string, bool
    if not os.path.isdir(profilepath):
        raise SolsticeChromiumException(_("The profile %s does not exist") % profilepath.split("/")[-1])

    LocalStateFile = "%s/Local State" % profilepath

    result = {}
    if os.path.isfile(LocalStateFile): #Load old Preferences into variable if one exists
        with open(LocalStateFile, 'r') as fp:
            result = json.loads(fp.read())
    with open("/usr/share/solstice/chromium/Local State", 'r') as fp: #Also load default local state, so we can patch
        result = utils.dict_recurupdate(result, json.loads(fp.read()))

    #Remove profile cache from Local State
    result = change_profile_name_ls(profilepath, True, result)

    #Save to the Local State
    try:
        with open(LocalStateFile, 'w') as fp:
            fp.write(json.dumps(result, separators=(',', ':'))) # Also a minified json
    except Exception as exceptionstr:
        raise SolsticeChromiumException(_("Failed to write to Local State"))


#Start Page
def chromi_add_startpage(profilepath, name, website):
    #dict, string, string
    if not os.path.isdir(profilepath):
        raise SolsticeChromiumException(_("The profile %s does not exist") % profilepath.split("/")[-1])

    #First, open default Bookmarks file
    with open("/usr/share/solstice/chromium/Bookmarks", 'r') as fp:
        result = json.loads(fp.read())

    #Then tweak the values
    result["roots"]["bookmark_bar"]["children"][0]["children"][0]["meta_info"]["Thumbnail"] = "data:image/gif;base64,R0lGODlhAQABAIAAAP///wAAACH5BAEAAAAALAAAAAABAAEAAAICRAEAOw=="
    result["roots"]["bookmark_bar"]["children"][0]["children"][0]["name"] = _("%s") % name
    result["roots"]["bookmark_bar"]["children"][0]["children"][0]["url"] = website

    #Then write to Bookmarks
    try:
        with open("%s/Default/Bookmarks" % profilepath, 'w') as fp:
            fp.write(json.dumps(result, separators=(',', ':'))) # Also a minified json
    except Exception as exceptionstr:
        raise SolsticeChromiumException(_("Failed to write to Bookmarks"))


#Finishing touches
def chromi_finishing_touches(profilepath):
    #string, string
    if not os.path.isdir(profilepath):
        raise SolsticeChromiumException(_("The profile %s does not exist") % profilepath.split("/")[-1])

    with open("%s/First Run" % profilepath, 'w') as fp:
        pass #Skips the initial Welcome to Google Chrome dialog
