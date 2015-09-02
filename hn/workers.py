# Workers are threads which are performing the heavy work

import oi
import re
import time
import functools
import requests
import logging

from . import compat
from . import reltime
from . import endpoints
from . import defaults

logging.getLogger("requests").setLevel(logging.WARNING)


class BaseWorker(oi.worker.Worker):
    """ Subclass this worker """

    def __init__(self, program, **kwargs):
        super(BaseWorker, self).__init__(**kwargs)
        self.program = program


class HNWorker(BaseWorker):
    """ A worker to check for new stories on HN periodically
    and store them in the program state """

    def __init__(self, program, **kwargs):
        super(HNWorker, self).__init__(program, **kwargs)

        # Story indices per category
        self.program.state.top = []
        self.program.state.new = []
        self.program.state.ask = []
        self.program.state.jobs = []
        self.program.state.show = []
        self.program.state.notified = []

        # Stories collection
        self.program.state.stories = {}

    def put_stories(self, kind, ids, limit):

        def enhance(story, kind):
            story['via'] = kind
            story['hostname'] = compat.urlparse(story.get('url', '')).hostname
            story['time'] = reltime.since_now(int(story['time']))
            story['descendants'] = story.get('descendants', 0)
            story.pop('kids', None)
            return story

        # Clear old stories so that the story collection will not grow forever
        self.program.state.stories = {
            key: story for key, story in self.program.state.stories.items()
            if story['via'] != kind
        }

        # Fetch each story in the id list and add it to the collection
        for i in ids[:limit]:
            story = requests.get(endpoints.STORY.format(i)).json()
            story = enhance(story, kind)
            self.program.state.stories[i] = story

    def run(self):
        """ Get data from endpoints, store it, then wait. Repeat. """

        urls = {
            'top': endpoints.TOP,
            'new': endpoints.NEW,
            'ask': endpoints.ASK,
            'jobs': endpoints.JOBS,
            'show': endpoints.SHOW,
        }

        while True:
            # Get stories for each category and store them
            limit = 15
            for name, url in urls.items():
                logging.debug('Getting stories for section {}'.format(name))
                ids = requests.get(url).json()
                setattr(self.program.state, name, ids[:limit])
                self.put_stories(name, ids, limit)

            # Sleep for a little bit
            try:
                interval = int(
                    self.program.config.getint('settings', 'interval'))
            except:
                interval = defaults.DEFAULTS['settings']['interval']

            logging.debug('HNWorker will sleep for {}s'.format(interval))
            time.sleep(interval)


class WatchWorker(BaseWorker):
    """ Watch for certain patterns in the data then put those stories
    in the watch_queue so other threads can to do something with them """

    class Watch(object):
        """ An object to keep track of new and seen stories """
        NOTIFIED_LIMIT = 1000

        def __init__(self):
            self.notified = []  # stories for which notifis were trigere
            self.new_queue = compat.Queue()

        def get(self):
            """ Get a story from the queue """
            return self.new_queue.get()

        def put(self, story):
            """ Add a story to the queue only if a notification has not
            been sent for it """

            if story['id'] not in self.notified:
                return self.new_queue.put(story)

        def mark_notified(self, story):
            """ Mark that a notifcation was sent for this story """

            if story['id'] not in self.notified:
                self.notified.append(story['id'])

            # Don't overgrow list
            if len(self.notified) > self.NOTIFIED_LIMIT:
                self.notified = self.notified[-self.NOTIFIED_LIMIT:]

        def was_notified(self, story):
            """ Was a notifcation already sent for this story """
            return story['id'] in self.notified

    # --------

    def __init__(self, program, **kwargs):
        super(WatchWorker, self).__init__(program, **kwargs)
        self.program.state.watch = self.Watch()

    def run(self):

        # Dont enter loop if watch is false
        try:
            watch = self.program.config.getboolean('watch.worker', 'watch')
        except:
            watch = defaults.DEFAULTS['watch.worker']['watch']

        if not watch:
            logging.debug('Nothing to watch. Exit thread.')
            return

        while True:
            logging.debug('WatchWorker will look for patterns')
            # Trim notifications
            if len(self.program.state.notified) > 300:
                self.program.state.notified = self.program.state.notified[-300:]

            # Read patterns to look for in the story titles
            try:
                patterns = self.program.config.get('watch.worker', 'regexes')
            except:
                patterns = defaults.DEFAULTS['watch.worker']['regexes']

            patterns = [p.strip() for p in patterns.split(',')]
            patterns = [p for p in patterns if p]
            logging.debug('Watch patterns: {}'.format(patterns))

            # When a pattern is found, add the story to the watch_new_queue
            for pat in patterns:
                for story in self.program.state.stories.values():

                    if self.program.state.watch.was_notified(story):
                        continue

                    if re.search(pat, story['title'], flags=re.I):
                        logging.debug('Found watch pattern {}'.format(pat))
                        self.program.state.watch.put(story)

            # Wait a little
            interval = 5
            logging.debug('WatchWorker will sleep for {}s'.format(interval))
            time.sleep(interval)


class NotifyWorker(BaseWorker):
    """ Show notifications """

    def __init__(self, program, **kwargs):
        super(NotifyWorker, self).__init__(program, **kwargs)
        self.registered = []

    def do(self, function):
        """ Do something when data comes in """

        def make_new_fun(fun):
            """ Make a new function which catches all errors """
            @functools.wraps(fun)
            def wrapper(*args, **kwargs):
                try:
                    return fun(*args, **kwargs)
                except Exception as e:
                    logging.debug('NotifyWorker.do error: {}'.format(e))
            return wrapper

        self.registered.append(make_new_fun(function))

    def run(self):
        """ Take items from the watch queue then process them """

        try:
            notify = self.program.config.getboolean('notify.worker', 'notify')
        except:
            notify = defaults.DEFAULTS['notify.worker']['notify']

        if not notify:
            logging.debug('No notify. Exit thread.')
            return

        while True:
            logging.debug('Getting a new story from queue')

            # Take new stories, mark them as seen and do some work
            story = self.program.state.watch.get()
            self.program.state.watch.mark_notified(story)

            logging.debug('Do notifications for story {}'.format(story['id']))

            for function in self.registered:
                function(story)

            # Wait a little
            interval = 5
            logging.debug('NotifyWorker will sleep for {}s'.format(interval))
            time.sleep(interval)
