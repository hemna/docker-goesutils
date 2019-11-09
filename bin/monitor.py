#!/usr/bin/python3
# Script that monitors for GOESproc added files in a directory.
#
import argparse
import concurrent.futures
import os
from oslo_config import cfg
from oslo_context import context
from oslo_log import log
import shutil
import subprocess
import sys
import time
import uuid
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from datetime import datetime
from datetime import tzinfo
from datetime import timedelta

APP = 'monitor'
SCRIPT_DIR="/home/goes/bin"
FONT="%s/Verdana_Bold.ttf" % SCRIPT_DIR


LOG = log.getLogger("goesmonitor")
CONF = cfg.CONF
#CONF.logging_user_identity_format = "%(request_id)s"
CONF.logging_user_identity_format = ""


conf = cfg.ConfigOpts()
opts = [cfg.StrOpt('file'),
        cfg.StrOpt('dir')]
conf.register_cli_opts(opts)
conf(sys.argv[1:])

context.RequestContext(request_id=uuid.uuid4())
executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)

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

    def __init__(self, source_file):
        self.source = source_file
        #context.RequestContext(request_id=uuid.uuid4())

    def _collect_info(self):
        context.RequestContext(request_id=uuid.uuid4())
        LOG.info("Process %s", self.source)
        basename = os.path.basename(self.source)
        self.dirname = os.path.dirname(self.source)
        base_path = self.dirname.replace("/home/goes/data/goes16", "")
        components = base_path.split('/')
        self.model = components[1]
        self.chan = components[3]
        LOG.debug("Model/Channel = %s/%s", self.model, self.chan)

        time_str = basename.replace(".png","")
        dto = datetime.strptime(time_str, '%Y-%m-%dT-%H-%M-%SZ')
        self.file_time = dto.replace(tzinfo=GMT)
        self.va_date = self.file_time.astimezone(EST)
        self.ca_date = self.file_time.astimezone(PST)

    def _destination(self, state=None):
        date_str = "%Y-%m-%d"
        if state is not None:
            if state == 'va':
                date = self.va_date.strftime(date_str)
            else:
                date = self.ca_date.strftime(date_str)
            destination = ("%s/%s/%s/%s/%s" % (self.process_dir,
                                               self.model,
                                               date,
                                               self.chan, state))
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

    def crop(self, state):
        """ Crop a Full Disc image to cover a specific state. """
        time.sleep(2)
        LOG.info("Crop fd image for '%s'", state)
        dest = self._destination(state)
        self._ensure_src()
        self._ensure_dir(dest)
        newfile_fmt = "%H-%M-%S"
        if state == "va":
            resolution = "1024x768+2100+600"
            newfile_name = "%s.png" % self.va_date.strftime(newfile_fmt)
        else:
            resolution = "1024x768+600+600"
            newfile_name = "%s.png" % self.ca_date.strftime(newfile_fmt)

        newfile = "%s/%s" % (dest, newfile_name)
        if not self.file_exists(newfile):
            crop_cmd = ["/usr/bin/convert", "%s" % self.source,
                        "-crop", '"%s"' % resolution,
                        "+repage", "%s" % newfile]
            self._execute(crop_cmd)
            self.overlay(newfile, state)

    def copy(self, subdest=None):
        """Copy a full disc image to destination. """
        if subdest:
            dest = "%s/%s" % (self._destination(state=None), subdest)
        else:
            dest = self._destination(state=None)

        newfile_fmt = "%H-%M-%S"
        newfile_name = self.file_time.strftime(newfile_fmt)
        dest_file = "%s/%s.png" % (dest, newfile_name)
        LOG.debug("copy image to destination '%s'", dest_file)

        self._ensure_src()
        self._ensure_dir(dest)
        if not self.file_exists(dest_file):
            shutil.copyfile(self.source, dest_file)
            self.overlay(dest_file)

    def resize(self, dest_file):
        # rescale the file down to something manageable in size
        # the raw fd images are 5240x5240
        cmd = ["/usr/bin/convert",
                dest_file,
                "-resize", "25%",
                dest_file]
        self._execute(cmd)

    def animate(self, state=None):
        dest = self._destination(state=state)
        LOG.info("animate directory '%s'", dest)
        file = "%s/animate.gif" % dest
        cmd = ["/usr/bin/convert", "-loop", "0", "-delay", "15",
               "%s/*.png" % dest,
               "%s" % file]
        self._execute(cmd)

    def animate_fd(self):
        dest = "%s/animate" % self._destination(state=None)
        file_webm = "%s/earth.webm" % dest
        file_gif = "%s/earth.gif" % dest
        cmd = ["ffmpeg", "-y",
               "-framerate", "10",
               "-pattern_type", "glob",
               "-i", "'%s/*.png'" % dest,
               "-c:v", "libvpx-vp9",
               #"-b:v", "3M",
               "-b:v", "0",
               "-crf", "15",
               "-c:a", "libvorbis",
               file_webm]
        self._execute(cmd)

        cmd = ["ffmpeg", "-y",
               "-i", file_webm,
               "-loop", "0",
               file_gif]
        self._execute(cmd)

    def overlay(self, image_file, state=None):
        human_date_fmt = "%A %b %e, %Y  %T  %Z"
        if state:
            font_size = "24"
            if state == "va":
                human_date = self.va_date.strftime(human_date_fmt)
            else:
                human_date = self.ca_date.strftime(human_date_fmt)
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
            self.crop('va')
            self.crop('ca')
            self.copy(subdest="animate")

            if animate:
                self.animate(state='va')
                self.animate(state='ca')
                self.animate_fd()
        else:
            # This is an m1 or m2 file
            # We copy and animate
            self.copy()
            if animate:
              self.animate()


class Watcher:
    def __init__(self, dir):
        self.DIRECTORY_TO_WATCH = dir
        LOG.info("Setting up directory observer for %s", dir)
        self.observer = Observer()

    def run(self):
        event_handler = Handler()
        self.observer.schedule(event_handler, self.DIRECTORY_TO_WATCH, recursive=True)
        self.observer.start()
        try:
            while True:
                time.sleep(1)
        except:
            self.observer.stop()
            LOG.error("Error")

        self.observer.join()


class Handler(FileSystemEventHandler):

    executor = None

    def __init__(self):
        super(Handler, self).__init__()

    @staticmethod
    def on_any_event(event):
        global executor
        if event.is_directory:
            return None

        elif event.event_type == 'created':
            # Take any action here when a file is first created.
            LOG.debug("Got create event for '%s'", event.src_path)
            fh = FileHandler(event.src_path)
            time.sleep(1)
            executor.submit(fh.process)


def process_dir(process_dir):
    for dirpath, dnames, fnames in os.walk(process_dir):
        total_files = len(fnames)
        LOG.info
        cnt = 1
        animate=False
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            for f in fnames:
                LOG.info("Process file '%s' (%s of %s)", f, cnt, total_files)
                process_file = "%s/%s" % (dirpath, f)
                fh = FileHandler(process_file)
                if cnt == total_files:
                    animate=True
                executor.submit(fh.process, animate=animate)
                cnt+=1


GMT = Zone(0,False,'GMT')
EST = Zone(-5,False,'EST')
PST = Zone(-8,False,'PST')

if __name__ == '__main__':
    prepare()
    if conf.dir:
        # User wants to process and entire directory
        LOG.info("Process directory '%s'", conf.dir)
        process_dir(conf.dir)
    elif conf.file:
        fh = FileHandler(conf.file)
        fh.process()
    else:
        w = Watcher("/home/goes/data/goes16")
        w.run()
