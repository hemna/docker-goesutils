#!/usr/bin/python3
#
# Script that monitors for GOESproc added files in a directory.
#
# This works with the http://github.com/hemna/docker-goestools app
# that uses goestools to process data from a goes receiver
# https://github.com/pietern/goestools
#
# This app supports the GeosEast and GoesWest satellites.
# Features:
#  * Watches for new files in watchdirectories
#  * Crops full disc images based upon supported regions
#  * Creates animated gifs of images and regions
#
import argparse
import concurrent.futures
from flask import Flask
import os
from oslo_config import cfg
from oslo_context import context
from oslo_log import log
import shutil
import subprocess
import sys
import time
import threading
import uuid
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from datetime import datetime
from datetime import tzinfo
from datetime import timedelta

APP = 'monitor'
SCRIPT_DIR="/home/goes/bin"
FONT="%s/Verdana_Bold.ttf" % SCRIPT_DIR
PID_FILE="/home/goes/monitor.pid"

# Config for the supported satellites
# TODO(waboring): add support for goes-west images for cropping.
satellites = {
    'goes-east': {
        'watchdir': '/home/goes/data/goes-east',
        'crop': {
            'ca': "1024x768+600+600",
            'va': "1024x768+2100+600",
            'usa': "2424x1424+720+280",
        }
    },
    'goes-west': {
        'watchdir': '/home/goes/data/goes-west',
        'crop': {
            'ca': '',
            'va': '',
            'usa': '',
        }
    },
}

LOG = log.getLogger("goesmonitor")
CONF = cfg.CONF
#CONF.logging_user_identity_format = "%(request_id)s"
CONF.logging_user_identity_format = ""


conf = cfg.ConfigOpts()
opts = [cfg.StrOpt('file'),
        cfg.StrOpt('dir'),
        cfg.BoolOpt('force'),
        cfg.BoolOpt('goeseast'),
        cfg.BoolOpt('goeswest'),
        ]
conf.register_cli_opts(opts)
conf(sys.argv[1:])

# For the log output
context.RequestContext(request_id=uuid.uuid4())

# For starting threads to handle each new file discovered
# not specifying max_workers means use each cpu
executor = concurrent.futures.ThreadPoolExecutor()

def prepare():
    log.register_options(CONF)

    extra_log_level_defaults = [
        'watchdog=ERROR',
        'monitor=INFO'
    ]

    CONF(sys.argv[1:3], project=APP, version='1.0')
    log.setup(CONF, APP)
    log.getLogger('watchdog').setLevel(log.ERROR)


class Zone(tzinfo):
    def __init__(self,offset,isdst,name):
        self.offset = offset
        self.isdst = isdst
        self.name = name
    def utcoffset(self, dt):
        return timedelta(hours=self.offset) + self.dst(dt)
    def dst(self, dt):
            return timedelta(hours=1) if self.isdst else timedelta(0)
    def tzname(self,dt):
         return self.name


class FileHandler(object):
    source = None
    gmt_time = None
    process_dir = "/home/goes/data/processed"

    def __init__(self, new_file, satellite):
        LOG.info("FH for : %s from %s", new_file, satellite)
        context.RequestContext(request_id=uuid.uuid4())
        LOG.info("FH for : %s from %s", new_file, satellite)
        self.source = new_file
        self.satellite = satellite
        self.satellite_dir = satellite['watchdir']

    def _collect_info(self):
        context.RequestContext(request_id=uuid.uuid4())
        LOG.info("Process %s", self.source)
        basename = os.path.basename(self.source)
        self.dirname = os.path.dirname(self.source)
        base_path = self.dirname.replace(self.satellite_dir, "")
        components = base_path.split('/')
        self.model = components[1]
        self.chan = components[3]
        LOG.debug("Model/Channel = %s/%s", self.model, self.chan)

        time_str = basename.replace(".png","")
        dto = datetime.strptime(time_str, '%Y-%m-%dT-%H-%M-%SZ')
        self.file_time = dto.replace(tzinfo=GMT)
        self.va_date = self.file_time.astimezone(EST)
        self.ca_date = self.file_time.astimezone(PST)
        self.gmt_date = self.file_time.astimezone(GMT)

    def _destination(self, region=None):
        date_str = "%Y-%m-%d"
        if region is not None:
            if region == 'va':
                date = self.va_date.strftime(date_str)
            elif region == 'ca':
                date = self.ca_date.strftime(date_str)
            else:
                date = self.gmt_date.strftime(date_str)

            destination = ("%s/%s/%s/%s/%s" % (self.process_dir,
                                               self.model,
                                               date,
                                               self.chan, region))
        else:
            date = self.file_time.strftime(date_str)
            destination = ("%s/%s/%s/%s" % (self.process_dir,
                                            self.model,
                                            date,
                                            self.chan))

        return destination

    def _ensure_src(self):
        LOG.debug("make sure '%s' exists", self.source)
        # make sure the source file exists and is written to the fs
        while not os.path.exists(self.source):
            LOG.debug("'%s' isn't ready yet", self.source)
            time.sleep(1)

    def _ensure_dir(self, destination):
        LOG.debug("make sure '%s' exists", destination)
        os.makedirs(destination, exist_ok = True)

    def file_exists(self, destination):
        if os.path.exists(destination):
            return True
        else:
            return False

    def _execute(self, cmd):
        command = ' '.join(cmd)
        LOG.info("EXEC '%s'", command)
        try:
            out = subprocess.run(command, shell=True, check=False,
                                 encoding="utf-8",
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            if len(out.stdout):
                LOG.debug("OUT = '%s'", out.stdout.encode('utf-8'))
            if len(out.stderr):
                LOG.warn("ERR = '%s'", out.stderr.encode('utf-8'))

        except Exception as ex:
            LOG.exception("FAIL %s", ex)

    def crop(self, region):
        """ Crop a Full Disc image to cover a specific region. """
        time.sleep(2)
        LOG.info("Crop fd image for '%s'", region)
        dest = self._destination(region)
        self._ensure_src()
        self._ensure_dir(dest)
        newfile_fmt = "%H-%M-%S"
        if region == "va":
            resolution = self.satellite['crop']['va']
            newfile_name = "%s.png" % self.va_date.strftime(newfile_fmt)
        elif region == "ca":
            resolution = self.satellite['crop']['ca']
            newfile_name = "%s.png" % self.ca_date.strftime(newfile_fmt)
        elif region == 'usa':
            resolution = self.satellite['crop']['usa']
            newfile_name = "%s.png" % self.gmt_date.strftime(newfile_fmt)


        newfile = "%s/%s" % (dest, newfile_name)
        if not self.file_exists(newfile):
            crop_cmd = ["/usr/bin/convert", "%s" % self.source,
                        "-crop", '"%s"' % resolution,
                        "+repage", "%s" % newfile]
            self._execute(crop_cmd)
            self.overlay(newfile, region)

    def copy(self, subdest=None, overlay=True, resize=False):
        """Copy a full disc image to destination. """
        if subdest:
            dest = "%s/%s" % (self._destination(region=None), subdest)
        else:
            dest = self._destination(region=None)

        newfile_fmt = "%H-%M-%S"
        newfile_name = self.file_time.strftime(newfile_fmt)
        dest_file = "%s/%s.png" % (dest, newfile_name)
        LOG.debug("copy image to destination '%s'", dest_file)

        self._ensure_src()
        self._ensure_dir(dest)
        if not self.file_exists(dest_file):
            shutil.copyfile(self.source, dest_file)
            if resize:
                self.resize(dest_file)

            if overlay:
                self.overlay(dest_file)

    def resize(self, dest_file):
        # rescale the file down to something manageable in size
        # the raw fd images are 5240x5240
        cmd = ["/usr/bin/convert",
                dest_file,
                "-resize", "25%",
                dest_file]
        self._execute(cmd)

    def animate(self, region=None):
        dest = self._destination(region=region)
        LOG.info("animate directory '%s'", dest)
        dest_file = "%s/animate.gif" % dest
        self._animated_gif("%s/*.png" % dest,
                           "%s" % dest_file)

    def _animated_gif(self, source, destination):
        cmd = ["/usr/bin/convert", "-loop", "0", "-delay", "15",
               "%s" % source,
               "%s" % destination]
        self._execute(cmd)

    def animate_fd(self):
        dest = "%s/animate" % self._destination(region=None)
        file_webm = "%s/earth.webm" % dest
        file_gif = "%s/earth.gif" % dest

        self._animated_gif("%s/*.png" % dest,
                           file_gif)
        #cmd = ["ffmpeg", "-y",
        #       "-framerate", "10",
        #       "-pattern_type", "glob",
        #       "-i", "'%s/*.png'" % dest,
        #       "-c:v", "libvpx-vp9",
        #       #"-b:v", "3M",
        #       "-b:v", "0",
        #       "-crf", "15",
        #       "-c:a", "libvorbis",
        #       file_webm]
        #self._execute(cmd)

        #cmd = ["ffmpeg", "-y",
        #       "-i", file_webm,
        #       "-loop", "0",
        #       file_gif]
        #self._execute(cmd)

    def overlay(self, image_file, region=None):
        human_date_fmt = "%A %b %e, %Y  %T  %Z"
        if region:
            font_size = "24"
            if region == "va":
                human_date = self.va_date.strftime(human_date_fmt)
            elif region == "ca":
                human_date = self.ca_date.strftime(human_date_fmt)
            elif region == "usa":
                human_date = self.gmt_date.strftime(human_date_fmt)
        else:
            font_size = "12"
            human_date = self.file_time.strftime(human_date_fmt)

        cmd = ["/usr/bin/convert",
               image_file,
               "-quality", "90",
               "-font", FONT,
               "-fill", '"#0004"', "-draw", "'rectangle 0,2000,2560,1820'",
               "-pointsize", font_size, "-gravity", "southwest",
               "-fill", "white", "-gravity", "southwest", "-annotate", "+2+10", '"%s"' % human_date,
               "-fill", "white", "-gravity", "southeast", "-annotate", "+2+10", '"wx.hemna.com"',
               image_file]
        self._execute(cmd)

    def process(self, animate=True):
        self._collect_info()
        if self.model == 'fd':
            # We want to crop for both CA and VA
            self.crop(region='va')
            self.crop(region='ca')
            self.crop(region='usa')
            self.copy(subdest="animate", overlay=False, resize=True)

            if animate:
                self.animate(region='va')
                self.animate(region='ca')
                self.animate(region='usa')
                self.animate_fd()
        else:
            # This is an m1 or m2 file
            # We copy and animate
            self.copy()
            if animate:
              self.animate()

class MyHandler(object):
    satellite_dir = ''

    def __init__(self, satellite):
        self.satellite = satellite

    def handle_event(self, event):
        global executor
        if event.is_directory:
            return None

        elif event.event_type == 'created':
            # Take any action here when a file is first created.
            LOG.debug("Got create event for '%s'", event.src_path)
            try:
                fh = FileHandler(new_file=event.src_path,
                                 satellite=self.satellite)
            except Exception as ex:
                LOG.exception("Failed to create FileHandler ", ex)

            LOG.debug("Start thread to process it.")
            executor.submit(fh.process)


class GoesEastHandler(FileSystemEventHandler):

    @staticmethod
    def on_any_event(event):
        ret = None
        try:
            h = MyHandler(satellites['goes-east'])
            ret = h.handle_event(event)
        except Exception as ex:
            print(ex)

        return ret

class GoesWestHandler(FileSystemEventHandler):

    @staticmethod
    def on_any_event(event):
        h = MyHandler(satellites['goes-west'])
        return h.handle_event(event)


class Watcher:

    def __init__(self, satellite_name):
        global satellites
        self.satellite_name = satellite_name
        self.satellite_dir = satellites[satellite_name]['watchdir']
        LOG.info("Setting up directory observer for %s", self.satellite_dir)
        self.observer = Observer()

    def run(self):
        if self.satellite_name == 'goes-east':
            event_handler = GoesEastHandler()
        if self.satellite_name == 'goes-west':
            event_handler = GoesWestHandler()

        self.observer.schedule(event_handler, self.satellite_dir, recursive=True)
        self.observer.start()
        try:
            while True:
                time.sleep(1)
        except:
            self.observer.stop()
            LOG.error("Error")

        self.observer.join()


def process_dir(process_dir):

    satellite = None
    for entry in process_dir.split('/'):
        if entry.startswith('goes-'):
            satellite = entry
            break;

    for dirpath, dnames, fnames in os.walk(process_dir):
        total_files = len(fnames)
        cnt = 1
        animate=False
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            for f in fnames:
                LOG.info("Process file '%s' (%s of %s)", f, cnt, total_files)
                process_file = "%s/%s" % (dirpath, f)
                fh = FileHandler(new_file=process_file,
                                 satellite=satellites[satellite])

                if cnt == total_files:
                    animate=True
                executor.submit(fh.process, animate=animate)
                cnt+=1


def _write_pid():
    pid = str(os.getpid())
    f = open(PID_FILE, 'w')
    f.write(pid)
    f.close()

def _rm_pid():
    os.remove(PID_FILE)


GMT = Zone(0,False,'GMT')
EST = Zone(-5,False,'EST')
PST = Zone(-8,False,'PST')

app = Flask(__name__)
@app.route("/healthcheck")
def main():
    return "yes"

if __name__ == '__main__':
    _write_pid()
    prepare()
    if conf.dir:
        # User wants to process and entire directory
        LOG.info("Process directory '%s'", conf.dir)
        # Now launch the watcher(s)
        process_dir(conf.dir)
    elif conf.file:
        print("SAT_DIR=%s" % sat_dir)
        fh = FileHandler(new_file=conf.file,
                         satellite=satellites['goes-east'])
        fh.process()
    else:
        # Now launch the watcher(s)
        if not conf.goeseast and not conf.goeswest:
            LOG.error("You must specify a satellite to watch")
            sys.exit(1)

        # launch the healthcheck flask first
        threading.Thread(target=app.run).start()

        if conf.goeseast:
            east = Watcher(satellite_name='goes-east')
            east.run()
            #threading.Thread(target=east.run).start()

        #if conf.goeswest:
        #    west = Watcher(satellite_dir=satellites['goes-west']['watchdir'])
        #    threading.Thread(target=west.run).start()

    _rm_pid()
