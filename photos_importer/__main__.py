#!/usr/bin/env python


import time
import Queue
import subprocess
from threading import Thread, Timer
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

# NOTE: sortphotos is in the ugly "src" package
from src.sortphotos import sortPhotos

def main(args=None):
    import argparse

    # sortphotos arguments
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter,
                                     description='Sort files (primarily photos and videos) into folders by date\nusing EXIF and other metadata')
    parser.add_argument('src_dir', type=str, help='source directory')
    parser.add_argument('dest_dir', type=str, help='destination directory')
    parser.add_argument('-r', '--recursive', action='store_true', help='search src_dir recursively')
    parser.add_argument('-c', '--copy', action='store_true', help='copy files instead of move')
    parser.add_argument('-s', '--silent', action='store_true', help='don\'t display parsing details.')
    parser.add_argument('-t', '--test', action='store_true', help='run a test.  files will not be moved/copied\ninstead you will just a list of would happen')
    parser.add_argument('--sort', type=str, default='%Y/%m-%b',
                        help="choose destination folder structure using datetime format \n\
    https://docs.python.org/2/library/datetime.html#strftime-and-strptime-behavior. \n\
    Use forward slashes / to indicate subdirectory(ies) (independent of your OS convention). \n\
    The default is '%%Y/%%m-%%b', which separates by year then month \n\
    with both the month number and name (e.g., 2012/02-Feb).")
    parser.add_argument('--rename', type=str, default=None,
                        help="rename file using format codes \n\
    https://docs.python.org/2/library/datetime.html#strftime-and-strptime-behavior. \n\
    default is None which just uses original filename")
    parser.add_argument('--keep-duplicates', action='store_true',
                        help='If file is a duplicate keep it anyway (after renaming).')
    parser.add_argument('--day-begins', type=int, default=0, help='hour of day that new day begins (0-23), \n\
    defaults to 0 which corresponds to midnight.  Useful for grouping pictures with previous day.')
    parser.add_argument('--ignore-groups', type=str, nargs='+',
                    default=[],
                    help='a list of tag groups that will be ignored for date informations.\n\
    list of groups and tags here: http://www.sno.phy.queensu.ca/~phil/exiftool/TagNames/\n\
    by default the group \'File\' is ignored which contains file timestamp data')
    parser.add_argument('--ignore-tags', type=str, nargs='+',
                    default=[],
                    help='a list of tags that will be ignored for date informations.\n\
    list of groups and tags here: http://www.sno.phy.queensu.ca/~phil/exiftool/TagNames/\n\
    the full tag name needs to be included (e.g., EXIF:CreateDate)')
    parser.add_argument('--use-only-groups', type=str, nargs='+',
                    default=None,
                    help='specify a restricted set of groups to search for date information\n\
    e.g., EXIF')
    parser.add_argument('--use-only-tags', type=str, nargs='+',
                    default=None,
                    help='specify a restricted set of tags to search for date information\n\
    e.g., EXIF:CreateDate')

    # watcher arguments
    parser.add_argument('--delay', type=int, default=60, help='delay for synchronizing \n\
    after observing last modification (in seconds)')
    parser.add_argument('--prune-empty', action='store_true',
                        default=True,
                        help='prune empty directories.')

    # parse command line arguments
    args = parser.parse_args()

    def prune_dir(d):
        # traverse root directory, and list directories as dirs and files as files
        for root, dirs, files in os.walk(d):
            for sd in dirs:
                fsd = os.path.join(d, sd)
                prune_dir(fsd)
                try:
                    os.rmdir(fsd)
                except OSError as ex:
                    if ex.errno == errno.ENOTEMPTY:
                        print("%s not empty: cannot prune" % fsd)

    class MyHandler(PatternMatchingEventHandler):
        patterns = ["*.jpg",
                    "*.jpeg",
                    "*.png",
                    "*.gif",
                    "*.3fr",
                    "*.ari",
                    "*.arw",
                    "*.bay",
                    "*.crw",
                    "*.cr2",
                    "*.cap",
                    "*.data",
                    "*.dcs",
                    "*.dcr",
                    "*.dng",
                    "*.drf",
                    "*.eip",
                    "*.erf",
                    "*.fff",
                    "*.iiq",
                    "*.k25",
                    "*.mdc",
                    "*.mef",
                    "*.mos",
                    "*.mrw",
                    "*.nef",
                    "*.nrw",
                    "*.obm",
                    "*.orf",
                    "*.pef",
                    "*.ptx",
                    "*.pxn",
                    "*.r3d",
                    "*.raf",
                    "*.raw",
                    "*.rwl",
                    "*.rw2",
                    "*.rwz",
                    "*.sr2",
                    "*.srf",
                    "*.srw",
                    "*.tif",
                    "*.x3f"]
        case_sensitive = False

        def __init__(self, *args, **kwargs):
            self.timeout = kwargs.pop('time_interval', 0.4)
            super(MyHandler, self).__init__(*args, **kwargs)
            self.event_queue = Queue.Queue()
            self.timer_thread = Thread(target=self.timer_loop)
            self.timer_thread.daemon = True
            self.timer_thread.start()
            self.timer = None
            self.synchronizing = False

        def on_created(self, event):
            self.event_queue.put(event)

        def on_modified(self, event):
            self.event_queue.put(event)

        def timer_loop(self):
            events = []
            while True:
                try:
                    event = self.event_queue.get(timeout=self.timeout)
                    events.append(event)
                except Queue.Empty:
                    # when no more events are received, process all the
                    # `events` as only one
                    if events:
                        print("detected modifications in files/dirs")
                        if self.timer:
                            print("reseting timer")
                            self.timer.cancel()

                        if not self.synchronizing:
                            print("scheduling synchronization in %d seconds" % args.delay)
                            self.timer = Timer(args.delay, self.synchronize)
                            self.timer.start()

                        events = []

        """
        Synchronize photos between two directories
        """
        def synchronize(self):
            if not self.synchronizing:
                self.synchronizing = True

                print("synchronizing photos %s -> %s" % (args.src_dir, args.dest_dir))
                sortPhotos(args.src_dir, args.dest_dir, args.sort, args.rename, args.recursive,
                    args.copy, args.test, not args.keep_duplicates, args.day_begins,
                    args.ignore_groups, args.ignore_tags, args.use_only_groups,
                    args.use_only_tags, not args.silent)

                if args.prune_empty:
                    prune_dir(args.src_dir)

                self.synchronizing = False

    observer = Observer()
    observer.schedule(MyHandler(),
                      path=args.src_dir if args.src_dir else '.',
                      recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()

if __name__ == '__main__':
    main()
