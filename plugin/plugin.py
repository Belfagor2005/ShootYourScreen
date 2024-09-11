# -*- coding: utf-8 -*-

# ##########################################
# maintainer: <plnick@vuplus-support.org> #
# #    http://www.vuplus-support.org      ##
# ##########################################

# This plugin is free software, you are allowed to
# modify it (if you keep the license),
# but you are not allowed to distribute/publish
# it without source code (this version and your modifications).
# This means you also have to distribute
# source code of your modifications.

# camera icon is taken from oxygen icon theme for KDE 4

# modified by Smokey 25-5-2015
# in this version it's possible to choose from several buttons to make a screen shot.
# a Dutch translation file is added, and some translations have changed in the other translation files.

# modified by Smokey 27-12-2016
# this version icludes the modification for 'FreezeFrame' that shadowrider made.
# the Dutch and German translations are updated.

# modified by Smokey 24-04-2017
# buttons 'Info' and 'EPG' added to the choice list.

# modified by Smokey 10-09-2024
# all remake for py3 and major fix from @lululla

from Components.AVSwitch import AVSwitch
from Components.ActionMap import ActionMap
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.config import (
    config,
    getConfigListEntry,
    ConfigSubsection,
    ConfigSelection,
    ConfigEnableDisable,
    ConfigYesNo,
)
from Plugins.Plugin import PluginDescriptor
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Components.MenuList import MenuList
from Tools.Notifications import AddNotification
import enigma
import os
from enigma import (
    eActionMap,
    loadPic,
    getDesktop,
    ePicLoad,
)
from os import (
    remove,
    listdir,
    path,
    makedirs,
)
from datetime import datetime
from time import time as systime

from . import _


size_w = getDesktop(0).size().width()
size_h = getDesktop(0).size().height()


def getMountedDevs():

    from Tools.Directories import resolveFilename, SCOPE_MEDIA
    from Components.Harddisk import harddiskmanager

    def handleMountpoint(loc):
        mp = loc[0]
        desc = loc[1]
        return (mp, desc + ' (' + mp + ')')

    mountedDevs = [(resolveFilename(SCOPE_MEDIA, 'hdd'), _('Harddisk')),
                   (resolveFilename(SCOPE_MEDIA, 'usb'), _('USB Device'))]
    mountedDevs += [(p.mountpoint, _(p.description) if p.description else '') for p in harddiskmanager.getMountedPartitions(True)]
    mountedDevs = [path for path in mountedDevs if os.path.isdir(path[0]) and os.access(path[0], os.W_OK | os.X_OK)]
    netDir = resolveFilename(SCOPE_MEDIA, 'net')
    if os.path.isdir(netDir):
        mountedDevs += [(os.path.join(netDir, p), _('Network mount')) for p in os.listdir(netDir)]
    mountedDevs += [(os.path.join('/', 'tmp'), _('Tmp Folder'))]
    mountedDevs = list(map(handleMountpoint, mountedDevs))
    return mountedDevs


pluginversion = _("Version:") + " 0.3"
config.plugins.shootyourscreen = ConfigSubsection()
config.plugins.shootyourscreen.enable = ConfigEnableDisable(default=False)
config.plugins.shootyourscreen.freezeframe = ConfigEnableDisable(default=False)
config.plugins.shootyourscreen.allways_save = ConfigEnableDisable(default=False)
config.plugins.shootyourscreen.switchhelp = ConfigYesNo(default=False)
# config.plugins.shootyourscreen.path = ConfigSelection(default="/tmp", choices=[("/media/hdd"), ("/media/usb"), ("/media/hdd1"), ("/media/usb1"), ("/tmp", "/tmp")])
config.plugins.shootyourscreen.path = ConfigSelection(choices=getMountedDevs())
config.plugins.shootyourscreen.pictureformat = ConfigSelection(default="-j", choices=[("-j", "jpg"), ("-p", "png"), ("bmp", "bmp")])
config.plugins.shootyourscreen.jpegquality = ConfigSelection(default="100", choices=[("10"), ("20"), ("40"), ("60"), ("80"), ("100")])
config.plugins.shootyourscreen.picturetype = ConfigSelection(default="all", choices=[("all", "OSD + Video"), ("-v", "Video"), ("-o", "OSD")])
config.plugins.shootyourscreen.picturesize = ConfigSelection(default="default", choices=[("default", _("Skin resolution")), ("-r 480", "480"), ("-r 576", "576"), ("-r 720", "720"), ("-r 1280", "1280"), ("-r 1920", "1920")])
config.plugins.shootyourscreen.timeout = ConfigSelection(default="3", choices=[("1", "1 sec"), ("3", "3 sec"), ("5", "5 sec"), ("10", "10 sec"), ("off", _("no message")), ("0", _("no timeout"))])
config.plugins.shootyourscreen.buttonchoice = ConfigSelection(default="138", choices=[("113", _("Mute")), ("138", _("Help")), ("358", " Info"), ("362", _("Timer")), ("365", _("EPG")), ("370", _("SUBTITLE")), ("377", _("TV")), ("385", _("Radio")), ("388", _("Text")), ("392", _("Audio")), ("398", _("Red")), ("399", _("Green")), ("400", _("Yellow")), ("401", _("Blue"))])
config.plugins.shootyourscreen.dummy = ConfigSelection(default="1", choices=[("1", " ")])


class getScreenshot:
    def __init__(self, session):
        self.ScreenshotConsole = Console()
        self.previousflag = 0
        self.session = session
        eActionMap.getInstance().bindAction('', -0x7FFFFFFF, self.screenshotKey)

    def screenshotKey(self, key, flag):
        selectedbutton = int(config.plugins.shootyourscreen.buttonchoice.value)
        if config.plugins.shootyourscreen.enable.value:
            if key == selectedbutton:
                if not config.plugins.shootyourscreen.switchhelp.value:
                    if flag == 3:
                        self.previousflag = flag
                        self.grabScreenshot()
                        return 1
                    if self.previousflag == 3 and flag == 1:
                        self.previousflag = 0
                        return 1
                else:
                    if flag == 0:
                        return 1
                    if flag == 3:
                        self.previousflag = flag
                        return 0
                    if flag == 1 and self.previousflag == 0:
                        self.grabScreenshot()
                        return 1
                    if self.previousflag == 3 and flag == 1:
                        self.previousflag = 0
                        return 0
        return 0

    def grabScreenshot(self, ret=None):
        filename = self.getFilename()
        print("[ShootYourScreen] grab screenshot to %s" % filename)
        # dreamboxctl screenshot -f /tmp/screenshot.jpg  # this command for dreambox cvs
        cmd = "grab"
        if not config.plugins.shootyourscreen.picturetype.value == "all":
            cmdoptiontype = " " + str(config.plugins.shootyourscreen.picturetype.value)
            cmd += cmdoptiontype
        if not config.plugins.shootyourscreen.picturesize.value == "default":
            cmdoptionsize = " " + str(config.plugins.shootyourscreen.picturesize.value)
            cmd += cmdoptionsize
        if not config.plugins.shootyourscreen.pictureformat.value == "bmp":
            cmdoptionformat = " " + str(config.plugins.shootyourscreen.pictureformat.value)
            cmd += cmdoptionformat
            if config.plugins.shootyourscreen.pictureformat.value == "-j":
                if config.plugins.shootyourscreen.freezeframe.value:
                    cmd += " 100"
                else:
                    cmdoptionquality = " " + str(config.plugins.shootyourscreen.jpegquality.value)
                    cmd += cmdoptionquality
        cmd += " %s" % filename
        print('ScreenshotConsole cmd:', cmd)

        extra_args = (filename)
        self.ScreenshotConsole.ePopen(cmd, self.gotScreenshot, extra_args)
        # popen(cmd, self.gotScreenshot, extra_args)

    def gotScreenshot(self, result, retval, extra_args=None):
        noscreen = True
        if extra_args is not None:
            filename = extra_args
            if config.plugins.shootyourscreen.freezeframe.value:
                noscreen = False
                self.session.open(FreezeFrame, filename)
        else:
            filename = ""

        if not config.plugins.shootyourscreen.timeout.value == "off" and noscreen:
            msg_text = None
            messagetimeout = int(config.plugins.shootyourscreen.timeout.value)
            if retval == 0:
                msg_text = _("Screenshot successfully saved as:\n%s") % filename
                msg_type = MessageBox.TYPE_INFO
            else:
                msg_text = _("Grabbing Screenshot failed !!!")
                msg_type = MessageBox.TYPE_ERROR
            if msg_text:
                AddNotification(MessageBox, msg_text, msg_type, timeout=messagetimeout)
        else:
            pass

    def getFilename(self):
        now = systime()
        now = datetime.fromtimestamp(now)
        now = now.strftime("%Y-%m-%d_%H-%M-%S")

        screenshottime = "screenshot_" + now
        if config.plugins.shootyourscreen.pictureformat.value == "-j":
            fileextension = ".jpg"
        elif config.plugins.shootyourscreen.pictureformat.value == "bmp":
            fileextension = ".bmp"
        elif config.plugins.shootyourscreen.pictureformat.value == "-p":
            fileextension = ".png"

        picturepath = self.getPicturePath()
        if picturepath.endswith('/'):
            screenshotfile = picturepath + screenshottime + fileextension
        else:
            screenshotfile = picturepath + '/' + screenshottime + fileextension
        return screenshotfile

    def getPicturePath(self):
        picturepath = config.plugins.shootyourscreen.path.value
        if picturepath.endswith('/'):
            picturepath = picturepath + 'screenshots'
        else:
            picturepath = picturepath + '/screenshots'
        try:
            if (path.exists(picturepath) is False):
                makedirs(picturepath)
        except OSError:
            self.session.open(MessageBox, _("Sorry, your device for screenshots is not writeable.\n\nPlease choose another one."), MessageBox.TYPE_INFO, timeout=10)
        return picturepath


class sgrabberFilesScreen(Screen):

    skin = '''<screen name="sgrabberFilesScreen" position="center,center" size="1280,720" title="Screenshot Files" flags="wfNoBorder">
                <widget name="menu" position="42,72" size="600,500" scrollbarMode="showOnDemand" transparent="1" zPosition="2" font="Regular; 30" itemHeight="50" />
                <widget name="info" position="44,581" zPosition="4" size="1189,55" font="Regular;28" foregroundColor="yellow" transparent="1" halign="center" valign="center" />
                <eLabel backgroundColor="#00ffff00" position="638,680" size="300,6" zPosition="12" />
                <eLabel backgroundColor="#000000ff" position="939,680" size="300,6" zPosition="12" />
                <widget name="ButtonYellowtext" position="638,640" size="300,45" zPosition="11" font="Regular; 30" valign="center" halign="center" backgroundColor="background" transparent="1" foregroundColor="white" />
                <widget name="ButtonBluetext" position="939,640" size="300,45" zPosition="11" font="Regular; 30" valign="center" halign="center" backgroundColor="background" transparent="1" foregroundColor="white" />
            </screen>'''

    def __init__(self, session):
        self.skin = sgrabberFilesScreen.skin
        Screen.__init__(self, session)
        list = []
        self['menu'] = MenuList(list)
        self['ButtonBluetext'] = Label(_('Preview'))
        self['ButtonYellowtext'] = Label(_('Delete'))
        self['info'] = Label()

        self.folder = config.plugins.shootyourscreen.path.value + '/screenshots/'
        ''''
        # if config.plugins.sgrabber.storedir.value == 'tmp':
            # self.folder = '/tmp/screenshots/'
        # elif config.plugins.sgrabber.storedir.value == 'usb':
            # self.folder = '/media/usb/screenshots/'
        # else:
            # self.folder = '/media/hdd/screenshots/'
        '''
        self['actions'] = ActionMap(['SetupActions', 'ColorActions'], {'yellow': self.removefile,
                                                                       'blue': self.onFileAction,
                                                                       'ok': self.onFileAction,
                                                                       'cancel': self.close}, -2)
        self.fillplgfolders()

    def removefile(self):
        self['info'].setText('')
        try:
            fname = self['menu'].getCurrent()
            filename = self.folder + fname
            remove(filename)
            self.fillplgfolders()
        except:
            self['info'].setText('unable to delete file')

    def onFileAction(self):
        self['info'].setText('')
        try:
            fname = self['menu'].getCurrent()
            filename = self.folder + fname
            self.session.open(PiconsPreview, filename)
        except TypeError as e:
            self['info'].setText('unable to preview file')
            print('error:', e)

    def fillplgfolders(self):
        self['info'].setText('')
        plgfolders = []
        fullpath = []
        print("112"), self.folder
        if path.exists(self.folder):
            for x in listdir(self.folder):
                if path.isfile(self.folder + x):
                    if x.endswith('.jpg') or x.endswith('.png') or x.endswith('.bmp') or x.endswith('.gif'):
                        plgfolders.append(x)
                        fullpath.append(x)

        self['menu'].setList(plgfolders)
        self.fullpath = fullpath


class PiconsPreview(Screen):

    skin = '<screen flags="wfNoBorder" position="0,0" size="%d,%d" title="PiconsPreview" backgroundColor="#00000000">' % (size_w, size_h)
    skin += '<widget name="pixmap" position="0,0" size="%d,%d" zPosition="1" alphatest="on" />' % (size_w, size_h)
    skin += '</screen>'

    def __init__(self, session, previewPng=None):
        self.skin = PiconsPreview.skin
        Screen.__init__(self, session)
        self.session = session
        self.Scale = AVSwitch().getFramebufferScale()
        self.PicLoad = ePicLoad()
        self.previewPng = previewPng
        self['pixmap'] = Pixmap()
        try:
            self.PicLoad.PictureData.get().append(self.DecodePicture)
        except:
            self.PicLoad_conn = self.PicLoad.PictureData.connect(self.DecodePicture)
        self['actions'] = ActionMap(['OkCancelActions',
                                     'ColorActions'], {'ok': self.close,
                                                       'cancel': self.close,
                                                       'blue': self.close}, -1)
        self.onLayoutFinish.append(self.ShowPicture)

    def ShowPicture(self):
        myicon = self.previewPng
        if size_w == 2560:
            png = loadPic(myicon, 2560, 1440, 0, 0, 0, 1)
        elif size_w == 1920:
            png = loadPic(myicon, 1920, 1080, 0, 0, 0, 1)
        else:
            png = loadPic(myicon, 1280, 720, 0, 0, 0, 1)
        self["pixmap"].instance.setPixmap(png)

    def DecodePicture(self, PicInfo=None):
        ptr = self.PicLoad.getData()
        if ptr is not None:
            self['pixmap'].instance.setPixmap(ptr)


class FreezeFrame(Screen):

    skin = """
            <screen position="center,center" size="%d,%d" title="ShootYourScreen for Enigma2" flags="wfNoBorder">
                <widget name="freeze_pic" position="0,0" size="%d,%d" alphatest="on"/>
                <widget name="info" position="%d,%d" size="400,30" valign="center" halign="center" zPosition="99" font="Regular;22"/>
            </screen>""" % (size_w, size_h, size_w, size_h, size_w / 2 - 200, size_h - 40)

    def __init__(self, session, filename=None):
        self.session = session
        self.filename = filename
        Screen.__init__(self, session)
        self.pic = False
        self.PicLoad = ePicLoad()
        self.PicLoad.PictureData.get().append(self.DecodeAction)
        self["freeze_pic"] = Pixmap()
        self["info"] = Label(_("Save with RECORD-Button"))
        eActionMap.getInstance().bindAction('', 0x7FFFFFFF, self.exitx)
        self.onShown.append(self.setWindowTitle)

    def setWindowTitle(self):
        self.running = True
        self.setTitle(_("ShootYourScreen for Enigma2 STB - %s") % pluginversion)
        if config.plugins.shootyourscreen.allways_save.value:
            self["info"].hide()
        if self.filename:
            sc = AVSwitch().getFramebufferScale()
            self.PicLoad.setPara((size_w, size_h, sc[0], sc[1], False, 1, '#00000000'))
            self.updatePic()

    def updatePic(self):
        try:
            self.PicLoad.startDecode(self.filename)
        except:
            self.exitx()

    def DecodeAction(self, picInfo=None):
        ptr = self.PicLoad.getData()
        if ptr is not None:
            self["freeze_pic"].instance.setPixmap(ptr)

    def exitx(self, key=0, flag=0):
        if str(flag) == "0":
            eActionMap.getInstance().unbindAction('', self.exitx)
            saving = None
            if not config.plugins.shootyourscreen.allways_save.value:
                if str(key) != "167":
                    try:
                        remove(self.filename)
                    except:
                        pass
                else:
                    saving = 1
            else:
                saving = 1
            if saving and not config.plugins.shootyourscreen.timeout.value == "off":
                messagetimeout = int(config.plugins.shootyourscreen.timeout.value)
                msg_text = _("Screenshot successfully saved as:\n%s") % self.filename
                AddNotification(MessageBox, msg_text, MessageBox.TYPE_INFO, timeout=messagetimeout)
            self.close()


class ShootYourScreenConfig(Screen, ConfigListScreen):
    skin = """
            <screen position="center,center" size="950,700" title="ShootYourScreen for Enigma2 STB">
                <widget name="config" position="10,36" size="930,575" itemHeight="50" scrollbarMode="showOnDemand" />
                <widget name="buttonred" position="20,630" size="200,50" valign="center" halign="center" zPosition="2" foregroundColor="white" font="Regular; 28" />
                <widget name="buttongreen" position="240,631" size="200,50" valign="center" halign="center" zPosition="2" foregroundColor="white" font="Regular; 28" />
                <widget name="buttonyellow" position="460,630" size="200,50" valign="center" halign="center" zPosition="2" foregroundColor="white" font="Regular; 28" />
                <widget name="buttonblue" position="695,630" size="250,50" valign="center" halign="center" zPosition="2" foregroundColor="white" font="Regular; 28" />
                <eLabel backgroundColor="#00ff0000" position="20,680" size="200,6" zPosition="12" />
                <eLabel backgroundColor="#0000ff00" position="240,680" size="200,6" zPosition="12" />
                <eLabel backgroundColor="#00ffff00" position="460,680" size="200,6" zPosition="12" />
                <eLabel backgroundColor="#000000ff" position="695,680" size="250,6" zPosition="12" />
            </screen>"""

    def __init__(self, session):
        self.session = session
        Screen.__init__(self, session)
        self.createConfigList()
        ConfigListScreen.__init__(self, self.list, session=self.session, on_change=self.changedEntry)
        self["buttonred"] = Label(_("Exit"))
        self["buttongreen"] = Label(_("Save"))
        self["buttonyellow"] = Label(_("Default"))
        self["buttonblue"] = Label(_("View Screenshot"))
        self["setupActions"] = ActionMap(["SetupActions", "ColorActions"],
                                         {"green": self.keyGreen,
                                          "red": self.cancel,
                                          "yellow": self.revert,
                                          "blue": self.FilesScreen,
                                          "cancel": self.cancel,
                                          "ok": self.keyGreen}, -2)
        self.onShown.append(self.setWindowTitle)

    def FilesScreen(self):
        self.session.open(sgrabberFilesScreen)

    def setWindowTitle(self):
        self.setTitle(_("ShootYourScreen for Enigma2 STB - %s") % pluginversion)

    def createConfigList(self):
        self.list = []
        self.list.append(getConfigListEntry(_("Enable ShootYourScreen :"), config.plugins.shootyourscreen.enable))
        if config.plugins.shootyourscreen.enable.value is True:
            self.list.append(getConfigListEntry(_("Show on screen :"), config.plugins.shootyourscreen.freezeframe))
            self.list.append(getConfigListEntry(_("Screenshot of :"), config.plugins.shootyourscreen.picturetype))
            self.list.append(getConfigListEntry(_("Format for screenshots :"), config.plugins.shootyourscreen.pictureformat))
            if not config.plugins.shootyourscreen.freezeframe.value:
                if config.plugins.shootyourscreen.pictureformat.value == "-j":
                    self.list.append(getConfigListEntry(_("Quality of jpg picture :"), config.plugins.shootyourscreen.jpegquality))
            else:
                self.list.append(getConfigListEntry(_("Allways save :"), config.plugins.shootyourscreen.allways_save))
            self.list.append(getConfigListEntry(_("Picture size (width) :"), config.plugins.shootyourscreen.picturesize))
            self.list.append(getConfigListEntry(_("Path for screenshots :"), config.plugins.shootyourscreen.path))
            self.list.append(getConfigListEntry(_("Select a button to take a screenshot :"), config.plugins.shootyourscreen.buttonchoice))
            check = config.plugins.shootyourscreen.buttonchoice.value

            if check == "113":
                buttonname = ("Mute")
            elif check == "138":
                buttonname = ("Help")
            elif check == "358":
                buttonname = ("Info")
            elif check == "362":
                buttonname = ("Timer")
            elif check == "365":
                buttonname = ("EPG")
            elif check == "370":
                buttonname = ("SUBTITLE")
            elif check == "377":
                buttonname = ("TV")
            elif check == "385":
                buttonname = ("Radio")
            elif check == "388":
                buttonname = ("Text")
            elif check == "392":
                buttonname = ("Audio")
            elif check == "398":
                buttonname = ("Red")
            elif check == "399":
                buttonname = ("Green")
            elif check == "400":
                buttonname = ("Yellow")
            elif check == "401":
                buttonname = ("Blue")

            if check == '398' or check == '399' or check == '400':
                self.list.append(getConfigListEntry(_("Only button ' ") + buttonname + _(" long ' can be used."), config.plugins.shootyourscreen.dummy))
                config.plugins.shootyourscreen.switchhelp.setValue(0)
            else:
                self.list.append(getConfigListEntry(_("Use the ' ") + buttonname + _(" ' button instead of ' ") + buttonname + _(" long:"), config.plugins.shootyourscreen.switchhelp))
            self.list.append(getConfigListEntry(_("Timeout for info message :"), config.plugins.shootyourscreen.timeout))

    def changedEntry(self):
        self.createConfigList()
        self["config"].setList(self.list)

    def save(self):
        for x in self["config"].list:
            x[1].save()
        self.changedEntry()

    def keyGreen(self):
        self.save()
        self.close(False, self.session)

    def cancel(self):
        if self["config"].isChanged():
            self.session.openWithCallback(self.cancelConfirm, MessageBox, _("Really close without saving settings?"), MessageBox.TYPE_YESNO, default=True)
        else:
            for x in self["config"].list:
                x[1].cancel()
            self.close(False, self.session)

    def cancelConfirm(self, result):
        if result is None or result is False:
            print("[ShootYourScreen] Cancel not confirmed.")
        else:
            print("[ShootYourScreen] Cancel confirmed. Configchanges will be lost.")
            for x in self["config"].list:
                x[1].cancel()
            self.close(False, self.session)

    def revert(self):
        self.session.openWithCallback(self.keyYellowConfirm, MessageBox, _("Reset ShootYourScreen settings to defaults?"), MessageBox.TYPE_YESNO, timeout=20, default=True)

    def keyYellowConfirm(self, confirmed):
        if not confirmed:
            print("[ShootYourScreen] Reset to defaults not confirmed.")
        else:
            print("[ShootYourScreen] Setting Configuration to defaults.")
            config.plugins.shootyourscreen.enable.setValue(1)
            config.plugins.shootyourscreen.freezeframe.setValue(0)
            config.plugins.shootyourscreen.allways_save.setValue(1)
            config.plugins.shootyourscreen.switchhelp.setValue(0)
            config.plugins.shootyourscreen.path.setValue("/tmp")
            config.plugins.shootyourscreen.pictureformat.setValue("-j")
            config.plugins.shootyourscreen.jpegquality.setValue("100")
            config.plugins.shootyourscreen.picturetype.setValue("all")
            config.plugins.shootyourscreen.picturesize.setValue("default")
            config.plugins.shootyourscreen.timeout.setValue("3")
            config.plugins.shootyourscreen.buttonchoice.setValue("138")
            self.save()


class ConsoleItem:
    def __init__(self, containers, cmd, callback, extra_args, binary=False):
        self.extra_args = extra_args
        self.callback = callback
        self.container = enigma.eConsoleAppContainer()
        self.containers = containers
        self.binary = binary
        self.filename = self.getFilename()

        name = cmd
        if name in containers:
            name = str(cmd) + '@' + hex(id(self))
        self.name = name
        containers[name] = self

        if callback is not None:
            self.appResults = []
            self.container.dataAvail.append(self.dataAvailCB)
        self.container.appClosed.append(self.finishedCB)

        if isinstance(cmd, str):
            cmd = [cmd]
        retval = self.container.execute(*cmd)
        if retval:
            self.finishedCB(retval)
        if callback is None:
            try:
                os.waitpid(self.container.getPID(), 0)
            except:
                pass

    def dataAvailCB(self, data):
        self.appResults.append(data)

    def finishedCB(self, retval):
        print("[Console] finished:", self.name)
        del self.containers[self.name]
        del self.container.dataAvail[:]
        del self.container.appClosed[:]
        self.container = None
        callback = self.callback
        if callback is not None:
            data = b''.join(self.appResults)
            '''
            # try:
                # data = data if self.binary else data.decode('utf-8')
            # except UnicodeDecodeError:
                # print("[Error] Unable to decode data as UTF-8. Handling binary data.")
                # data = data.decode('utf-8', errors='replace')  # O 'ignore' se preferisci ignorare gli errori
            '''
            if not self.binary:
                try:
                    data = data.decode('utf-8')
                except UnicodeDecodeError:
                    print("[Error] Unable to decode as UTF-8. Saving binary data to file.")
                    with open(self.filename, "wb") as f:
                        f.write(data)
                    # data = self.filename
            # data = data if self.binary else data.decode()
            callback(data, retval, self.extra_args)

    def getFilename(self):
        from datetime import datetime
        from time import time as systime
        now = systime()
        now = datetime.fromtimestamp(now)
        now = now.strftime("%Y-%m-%d_%H-%M-%S")

        screenshottime = "screenshot_" + now
        if config.plugins.shootyourscreen.pictureformat.value == "-j":
            fileextension = ".jpg"
        elif config.plugins.shootyourscreen.pictureformat.value == "bmp":
            fileextension = ".bmp"
        elif config.plugins.shootyourscreen.pictureformat.value == "-p":
            fileextension = ".png"

        picturepath = self.getPicturePath()
        if picturepath.endswith('/'):
            screenshotfile = picturepath + screenshottime + fileextension
        else:
            screenshotfile = picturepath + '/' + screenshottime + fileextension
        return screenshotfile

    def getPicturePath(self):
        picturepath = config.plugins.shootyourscreen.path.value
        if picturepath.endswith('/'):
            picturepath = picturepath + 'screenshots'
        else:
            picturepath = picturepath + '/screenshots'
        try:
            if (path.exists(picturepath) is False):
                makedirs(picturepath)
        except OSError:
            self.session.open(MessageBox, _("Sorry, your device for screenshots is not writeable.\n\nPlease choose another one."), MessageBox.TYPE_INFO, timeout=10)
        return picturepath


class Console:
    """
        Console by default will work with strings on callback.
        If binary data required class shoud be initialized with Console(binary=True)
    """

    def __init__(self, binary=False):
        # Still called appContainers because Network.py accesses it to
        # know if there's still stuff running
        self.appContainers = {}
        self.binary = binary

    def ePopen(self, cmd, callback=None, extra_args=[]):
        print("[Console] command:", cmd)
        return ConsoleItem(self.appContainers, cmd, callback, extra_args, self.binary)

    def eBatch(self, cmds, callback, extra_args=[], debug=False):
        self.debug = debug
        cmd = cmds.pop(0)
        self.ePopen(cmd, self.eBatchCB, [cmds, callback, extra_args])

    def eBatchCB(self, data, retval, _extra_args):
        (cmds, callback, extra_args) = _extra_args
        if self.debug:
            print('[eBatch] retval=%s, cmds left=%d, data:\n%s' % (retval, len(cmds), data))
        if cmds:
            cmd = cmds.pop(0)
            self.ePopen(cmd, self.eBatchCB, [cmds, callback, extra_args])
        else:
            callback(extra_args)

    def kill(self, name):
        if name in self.appContainers:
            print("[Console] killing: ", name)
            self.appContainers[name].container.kill()

    def killAll(self):
        for name, item in self.appContainers.items():
            print("[Console] killing: ", name)
            item.container.kill()


def autostart(reason, **kwargs):
    if reason == 0:
        session = kwargs["session"]
        print("[ShootYourScreen] start....")
        getScreenshot(session)


def startSetup(session, **kwargs):
    print("[ShootYourScreen] start configuration")
    session.open(ShootYourScreenConfig)


def Plugins(**kwargs):
    return [PluginDescriptor(where=PluginDescriptor.WHERE_SESSIONSTART, fnc=autostart),
            PluginDescriptor(name="ShootYourScreen Setup", description=_("make Screenshots with your Enigma2 STB"), where=[PluginDescriptor.WHERE_PLUGINMENU, PluginDescriptor.WHERE_EXTENSIONSMENU], icon="shootyourscreen.png", fnc=startSetup)]


'''
# # for cvs insthead
# # dreambox   one
# dreamboxctl screenshot -h
# usage: dreamboxctl screenshot [-h] -f FILENAME [-iw WIDTH] [-ih HEIGHT] [-d DESKTOP] [-m MODE]
# optional arguments:
# -h, --help            show this help message and exit
# -f FILENAME, --filename FILENAME
                    # filename for the screenshot (requires full path)
                    # (default: /tmp/screenshot.png)
# -iw WIDTH, --width WIDTH
                    # image width. 0 for original size (default: 0)
# -ih HEIGHT, --height HEIGHT
                    # image height. 0 for original size (default: 0)
# -d DESKTOP, --desktop DESKTOP
                    # desktop to take a screenshot of. 0 for TV, 1 for display (default: 0)
# -m MODE, --mode MODE  capture mode, values: osd, video, combined (default:combined)
# ====
# # DM 900
# dreamboxctl screenshot -h
# usage: dreamboxctl screenshot [-h] -f FILENAME [-iw WIDTH] [-ih HEIGHT] [-d DESKTOP]
# optional arguments:
# -h, --help            show this help message and exit
# -f FILENAME, --filename FILENAME
                    # filename for the screenshot (requires full path)
                    # (default: /tmp/screenshot.png)
# -iw WIDTH, --width WIDTH
                    # image width. 0 for original size (default: 0)
# -ih HEIGHT, --height HEIGHT
                    # image height. 0 for original size (default: 0)
# -d DESKTOP, --desktop DESKTOP
                    # desktop to take a screenshot of. 0 for TV, 1 for display (default: 0)
'''
