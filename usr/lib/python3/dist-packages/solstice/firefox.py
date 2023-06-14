# This file is part of Feren Solstice.
#
# Copyright 2020-2023 Dominic Hayes

from . import utils
import os
import gettext
gettext.install("solstice-python", "/usr/share/locale", names="ngettext")
import shutil

class SolsticeFirefoxException(Exception):
    pass

def update_profile(iteminfo, extrawebsites, profilename, profilepath, darkmode, nocache):
    if not os.path.isdir("%s/chrome" % profilepath):
        try:
            os.mkdir("%s/chrome" % profilepath)
        except Exception as e:
            raise SolsticeFirefoxException(_("Failed to create the profile's chrome folder: %s") % e)

    #First, copy config files over
    for cfile in ["handlers.json", "user.js"]:
        shutil.copy("/usr/share/solstice/firefox/" + cfile, profilepath + "/" + cfile)
    #Configure user.js
    try:
        with open(profilepath + "/user.js", 'r') as fp:
            result = fp.read().splitlines()
        linescounted = 0
        for line in result:
            result[linescounted] = result[linescounted].replace("WEBSITEHERE", iteminfo["website"]).replace("NAMEHERE", iteminfo["name"]).replace("CLEARHISTORY", utils.boolean_to_jsonbool(iteminfo["nohistory"] == True))
            linescounted += 1

        #Set no cache preference
        result = set_profile_nocache(profilepath, nocache, True, result)

        with open(profilepath + "/user.js", 'w') as fp:
            fp.write('\n'.join(result))
    except Exception as e:
        raise SolsticeFirefoxException(_("Configuring user.js failed: %s") % e)

    firefox_set_ui(profilepath, iteminfo["bg"], iteminfo["bgdark"], iteminfo["accent"], iteminfo["accentdark"], iteminfo["color"], iteminfo["colordark"], iteminfo["accentonwindow"])

    #FIXME: Permissions hasn't been done yet as it requires effectively having a whole SQLite writer just to do it


#Profile Name
def change_profile_name(profilepath, itemname, value, patchvar=False, vartopatch={}):
    #string, string
    if not os.path.isdir(profilepath):
        raise SolsticeFirefoxException(_("The profile %s does not exist") % profilepath.split("/")[-1])

    if patchvar == False: #Allow this to also be used in update_profile without causing an additional file-write
        return #No visible profile name value to modify on Firefox's side, far as I know
    else:
        return vartopatch #So spit back out the unmodified variable here to prevent the variable Noneing after this call finishes


#Dark Mode
def set_profile_darkmode(profilepath, value, patchvar=False, vartopatch={}):
    #string, bool
    if not os.path.isdir(profilepath):
        raise SolsticeFirefoxException(_("The profile %s does not exist") % profilepath.split("/")[-1])

    raise SolsticeFirefoxException(_("Dark Mode is not available in Mozilla Firefox and its forks. Developers: Make sure your program checks for the 'darkmodeavailable' value in metadata.") % profilepath.split("/")[-1])


#No Cache
def set_profile_nocache(profilepath, value, patchvar=False, vartopatch=[]):
    #string, bool
    if not os.path.isdir(profilepath):
        raise SolsticeFirefoxException(_("The profile %s does not exist") % profilepath.split("/")[-1])

    valuestoadd = {"browser.cache.disk.enable": "false", "browser.cache.memory.enable": "false"}
    if value == False:
        valuestoadd["browser.cache.disk.enable"] = "true"
        valuestoadd["browser.cache.memory.enable"] = "true"

    if patchvar == False: #Allow this to also be used in update_profile without causing an additional file-write
        with open(profilepath + "/user.js", 'r') as fp:
            result = fp.read().splitlines()
    else:
        result = vartopatch
    linescounted = 0
    for line in result: #Check for and update existing values in user.js
        valuestoaddtmp = valuestoadd.copy()
        for i in valuestoaddtmp:
            if line.startswith('user_pref("' + i + '", '):
                result[linescounted] = 'user_pref("' + i + '", ' + valuestoaddtmp[i] + ");"
                valuestoadd.pop(i) #Remove this value from the 'values to add' list
        linescounted += 1
    for i in valuestoadd: #Add in remaining values to the user.js file
        result.append('user_pref("' + i + '", ' + valuestoaddtmp[i] + ");")

    if patchvar == False: #Allow this to also be used in update_profile without causing an additional file-write
        try:
            with open(profilepath + "/user.js", 'w') as fp:
                fp.write('\n'.join(result))
        except Exception as e:
            raise SolsticeFirefoxException(_("Configuring user.js failed: %s") % e)
    else:
        return result


#Colourise the Firefox interface
def firefox_set_ui(profilepath, bg, bgdark, accent, accentdark, color, colordark, accentonwindow):
    #string, string, string, string, string, string, boolean
    if not os.path.isdir(profilepath):
        raise SolsticeChromiumException(_("The profile %s does not exist") % profilepath.split("/")[-1])

    for cfile in ["userContent.css", "userChrome.css", "ferenChrome.css", "ice.css"]:
        shutil.copy("/usr/share/solstice/firefox/chrome/" + cfile, profilepath + "/chrome/" + cfile)

    # Backgrounds
    if accentonwindow == True:
        lightbg, darkbg = accent, accentdark
        lighttabbg, darktabbg = bg, bgdark
    else:
        lightbg, darkbg = bg, bgdark
        lighttabbg, darktabbg = accent, accentdark
    # Foregrounds
    if utils.color_is_light(lightbg) == True:
        lightfg, lightfgrgb = "black", "rgba(0, 0, 0, "
    else:
        lightfg, lightfgrgb = "white", "rgba(255, 255, 255, "
    if utils.color_is_light(darkbg) == True:
        darkfg, darkfgrgb = "black", "rgba(0, 0, 0, "
    else:
        darkfg, darkfgrgb = "white", "rgba(255, 255, 255, "
    if utils.color_is_light(lighttabbg) == True:
        lighttabfg = "black"
    else:
        lighttabfg = "white"
    if utils.color_is_light(darktabbg) == True:
        darktabfg = "black"
    else:
        darktabfg = "white"
    # Private
    privatebg = utils.color_filter(color, -70.0)
    privatetabbg = utils.color_filter(color, -46.0)
    if utils.color_is_light(privatebg) == True:
        privatefg, privatefgrgb = "black", "rgba(0, 0, 0, "
    else:
        privatefg, privatefgrgb = "white", "rgba(255, 255, 255, "
    if utils.color_is_light(privatetabbg) == True:
        privatetabfg = "black"
    else:
        privatetabfg = "white"
    # Accents
    if utils.color_is_light(color) == True:
        colorfg = "black"
    else:
        colorfg = "white"
    if utils.color_is_light(colordark) == True:
        colorfgdark = "black"
    else:
        colorfgdark = "white"
    # Buttons
    if color == lightbg:
        coloradaptivebg, coloradaptivefg = colorfg, color
    else:
        coloradaptivebg, coloradaptivefg = color, colorfg
    if colordark == darkbg:
        coloradaptivebgdark, coloradaptivefgdark = colorfgdark, colordark
    else:
        coloradaptivebgdark, coloradaptivefgdark = colordark, colorfgdark
    # Write to CSS files
    for i in ["userContent.css", "ice.css"]:
        with open(profilepath + "/chrome/" + i, 'r') as fp:
            result = fp.read().splitlines()
        linescounted = 0
        for line in result:
            result[linescounted] = result[linescounted]\
                .replace("WINDOWBGLIGHT", lightbg)\
                .replace("WINDOWFGLIGHT", lightfg)\
                .replace("TABBGLIGHT", lighttabbg)\
                .replace("TABFGLIGHT", lighttabfg)\
                .replace("TABFG02LIGHT", lightfgrgb + "0.2)")\
                .replace("TABFG03LIGHT", lightfgrgb + "0.3)")\
                .replace("WINDOWBGDARK", darkbg)\
                .replace("WINDOWFGDARK", darkfg)\
                .replace("TABBGDARK", darktabbg)\
                .replace("TABFGDARK", darktabfg)\
                .replace("TABFG02DARK", darkfgrgb + "0.2)")\
                .replace("TABFG03DARK", darkfgrgb + "0.3)")\
                .replace("WINDOWBGPRIVATE", privatebg)\
                .replace("WINDOWFGPRIVATE", privatefg)\
                .replace("TABBGPRIVATE", privatetabbg)\
                .replace("TABFGPRIVATE", privatetabfg)\
                .replace("TABFG02PRIVATE", privatefgrgb + "0.2)")\
                .replace("TABFG03PRIVATE", privatefgrgb + "0.3)")\
                .replace("COLORADAPTIVEBGLIGHT", coloradaptivebg)\
                .replace("COLORADAPTIVEFGLIGHT", coloradaptivefg)\
                .replace("COLORADAPTIVEBGDARK", coloradaptivebgdark)\
                .replace("COLORADAPTIVEFGDARK", coloradaptivefgdark)\
                .replace("COLORBGLIGHT", color)\
                .replace("COLORFGLIGHT", colorfg)\
                .replace("COLORBGDARK", colordark)\
                .replace("COLORFGDARK", colorfgdark)
            if "/* Special condition for adaptivebg - light */" in result[linescounted]:
                if coloradaptivebg == color: #If colours aren't flipped to maintain contrast,
                    result[linescounted-1] = "" #then disable the contrast improver
                    result[linescounted] = ""
                    result[linescounted+1] = ""
                    result[linescounted+2] = ""
            elif "/* Special condition for adaptivebg - dark */" in result[linescounted]:
                if coloradaptivebgdark == colordark:
                    result[linescounted-1] = ""
                    result[linescounted] = ""
                    result[linescounted+1] = ""
                    result[linescounted+2] = ""
            linescounted += 1

        try:
            with open(profilepath + "/chrome/" + i, 'w') as fp:
                fp.write('\n'.join(result))
        except Exception as e:
            raise SolsticeFirefoxException(_("Writing {0} failed: {1}").format(i, e))
