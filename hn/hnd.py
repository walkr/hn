import oi
import time
import requests

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
        ids = getattr(self.program.state, kind)
        return ''.join([
            self.show(i, s) for i, s in enumerate(ids)
        ])

    def top(self):
        """ Show top stories """
        return self.which('top')

    def new(self):
        """ Show new stories """
        return self.which('new')

    def show(self, index, storyid=None):
        """ Show story """
        layout = """
        {index}. {title}
        {url}
        {score} points by {by} {time} | {descendants}
        """
        return layout.format(index=index, **self.program.state.stories[storyid])

    def user(self, username='None'):
        """ Show a username """
        layout = """
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


class HNWorker(oi.worker.Worker):
    """ A worker to check the stories on HN periodically """

    def __init__(self, program, **kwargs):
        super(HNWorker, self).__init__(**kwargs)
        self.program = program

        self.program.state.top = []
        self.program.state.new = []
        self.program.state.stories = {}

    def put_stories(self, ids, limit):
        for i in ids[:limit]:
            story = requests.get(STORY.format(i)).json()
            story.pop('kids', None)
            self.program.state.stories[i] = story

    def run(self):
        while True:
            # Get top stories
            top = requests.get(TOP).json()
            self.program.state.top = top[:10]
            self.put_stories(top, 10)

            # Get new stories
            new = requests.get(NEW).json()
            self.program.state.new = new[:10]
            self.put_stories(new, 10)

            # Sleep for a little bit
            try:
                interval = int(self.program.config['settings']['interval'])
            except KeyError:
                interval = 60*5
            print('Sleeping for {} sec ...'.format(interval))
            time.sleep(interval)


def main():
    program = oi.Program('my program', 'ipc:///tmp/oi-qixdlkfuep.sock')
    cmds = Commands(program)

    program.add_command('ping', cmds.ping, 'ping HN')
    program.add_command('top', cmds.top, 'show top stories')
    program.add_command('new', cmds.new, 'show new stories')
    program.add_command('user', cmds.user, 'show user profile')
    program.workers.append(HNWorker(program))
    program.run()

if __name__ == '__main__':
    main()
