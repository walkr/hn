import oi
import time
import requests
import webbrowser

from . import compat
from . import reltime


# Endpoints

NEW = 'https://hacker-news.firebaseio.com/v0/newstories.json'
TOP = 'https://hacker-news.firebaseio.com/v0/topstories.json'
STORY = 'https://hacker-news.firebaseio.com/v0/item/{}.json'
USER = 'https://hacker-news.firebaseio.com/v0/user/{}.json'


class Commands(object):

    def __init__(self, program):
        self.program = program

    def which(self, kind):
        """ Show stories of `kind` """
        self.program.state.last_viewed = kind
        ids = getattr(self.program.state, kind)
        return ''.join([
            self.show(i+1, s) for i, s in enumerate(ids)
        ])

    def top(self):
        """ Show top stories """
        return self.which('top')

    def new(self):
        """ Show new stories """
        return self.which('new')

    def show(self, index, storyid=None):
        """ Show story """
        layout = u"""
        {index:2n}. {title} - ({hostname})
            {score} points by {by} {time} ago | {descendants} comments
        """
        data = self.program.state.stories[storyid]
        return layout.format(index=index, **data)

    def user(self, username='None'):
        """ Show a username """
        layout = u"""
        user: {id}
        created: {created}
        karma: {karma}
        about: {about}
        """
        userdata = requests.get(USER.format(username)).json()
        return layout.format(**userdata) if userdata else 'user not found'

    def ping(self):
        """ Check if HN site status """
        res = requests.get('https://news.ycombinator.com/news')
        return res.status_code

    def open(self, index):
        """ Open story from the latest viewed list by index """
        index = int(index.strip())
        index -= 1
        kind = self.program.state.last_viewed
        storyid = getattr(self.program.state, kind)[index]
        data = self.program.state.stories[storyid]
        webbrowser.open(data['url'])


class HNWorker(oi.worker.Worker):
    """ A worker to check the stories on HN periodically """

    def __init__(self, program, **kwargs):
        super(HNWorker, self).__init__(**kwargs)
        self.program = program

        self.program.state.top = []
        self.program.state.new = []
        self.program.state.stories = {}

    def put_stories(self, ids, limit):

        def fix(data):
            data['hostname'] = compat.urlparse(data['url']).hostname
            data['time'] = reltime.since_now(int(data['time']))
            data['descendants'] = data.get('descendants', 0)
            data.pop('kids', None)
            return data

        # Fetch each story in the id list
        for i in ids[:limit]:
            story = requests.get(STORY.format(i)).json()
            story = fix(story)
            self.program.state.stories[i] = story

    def run(self):
        while True:

            limit = 15
            # Get top stories
            top = requests.get(TOP).json()
            self.program.state.top = top[:limit]
            self.put_stories(top, limit)

            # Get new stories
            new = requests.get(NEW).json()
            self.program.state.new = new[:limit]
            self.put_stories(new, limit)

            # Sleep for a little bit
            try:
                interval = int(self.program.config['settings']['interval'])
            except KeyError:
                interval = 60*5
            time.sleep(interval)


def main():
    program = oi.Program('my program', 'ipc:///tmp/oi-qixdlkfuep.sock')
    cmds = Commands(program)

    program.add_command('ping', cmds.ping, 'ping HN')
    program.add_command('top', cmds.top, 'show top stories')
    program.add_command('new', cmds.new, 'show new stories')
    program.add_command('user', cmds.user, 'show user profile')
    program.add_command('open', cmds.open, 'show in browser')
    program.workers.append(HNWorker(program))
    program.run()

if __name__ == '__main__':
    main()
