# Workers are threads which are performing the heavy work

import oi
import re
import time
import functools
import requests

from . import compat
from . import reltime
from . import endpoints
from . import defaults


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
            story['hostname'] = compat.urlparse(story['url']).hostname
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
                ids = requests.get(url).json()
                setattr(self.program.state, name, ids[:limit])
                self.put_stories(name, ids, limit)

            # Sleep for a little bit
            try:
                interval = int(
                    self.program.config.getint('settings', 'interval'))
            except:
                interval = defaults['settings']['interval']
            time.sleep(interval)


class WatchWorker(BaseWorker):
    """ Watch for certain patterns in the data then put those stories
    in the watch_queue so other threads can to do something with them """

    def __init__(self, program, **kwargs):
        super(WatchWorker, self).__init__(program, **kwargs)

        self.program.state.watch_seen_queue = compat.Queue()  # stories seen
        self.program.state.watch_new_queue = compat.Queue()  # new stories

    def run(self):

        # Dont enter loop if watch is false
        try:
            watch = self.program.config.getboolean('watch.worker', 'watch')
        except:
            watch = defaults['watch.worker']['watch']

        if not watch:
            return

        while True:

            # Trim notifications
            if len(self.program.state.notified) > 300:
                self.program.state.notified = self.program.state.notified[-300:]

            # Read patterns to look for in the story titles
            try:
                patterns = self.program.config.get('watch.worker', 'regexes')
            except:
                patterns = defaults['watch.worker']['regexes']

            patterns = [p.strip() for p in patterns.split(',')]
            patterns = [p for p in patterns if p]

            # When a pattern is found, add the story to the watch_new_queue
            for pat in patterns:
                for story in self.program.state.stories.values():
                    if re.search(pat, story['title'], flags=re.I):
                        if story not in self.program.state.watch_seen_queue:
                            self.program.state.watch_new_queue.add(story)

            # Wait a little
            time.sleep(10)


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
                except:
                    pass
            return wrapper

        self.registered.append(make_new_fun(function))

    def run(self):
        """ Take items from the watch queue then process them """

        try:
            notify = self.program.config.getboolean('notify.worker', 'notify')
        except:
            notify = defaults['notify.worker']['notify']

        if not notify:
            return

        while True:

            # Take new stories, mark them as seen and do some work
            for story in self.program.state.watch_new_queue:
                self.program.state.watch_seen_queue.add(story)
                for function in self.registered:
                        function(story)

            time.sleep(3)
