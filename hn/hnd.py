# Daemon program which does most of the work

import os
import oi

from .commands import Commands
from .workers import HNWorker
from .workers import WatchWorker
from .workers import NotifyWorker


def main():
    program = oi.Program('my program', 'ipc:///tmp/oi-qixdlkfuep.sock')

    hn_worker = HNWorker(program)
    watch_worker = WatchWorker(program)

    # Show notifications when new stories are found
    notify_worker = NotifyWorker(program)
    notify_worker.do(lambda story: os.system(
        'terminal-notifier -title "{}" -message "{}" -open {}'.format(
            title='New story',
            message=u'{}'.format(story['title']),
            url=story['url']
        )
    ))

    # Add workers to our program
    program.workers.append(hn_worker)
    program.workers.append(watch_worker)
    program.workers.append(notify_worker)

    # Register commands on the program
    c = Commands(program)
    program.add_command('top', lambda: c.which('top'),   'show top stories')
    program.add_command('new', lambda: c.which('new'),   'show new stories')
    program.add_command('ask', lambda: c.which('ask'),   'show ask stories')
    program.add_command('jobs', lambda: c.which('jobs'), 'show jobs stories')
    program.add_command('show', lambda: c.which('show'), 'show(show) stories')

    program.add_command('ping', c.ping, 'ping HN')
    program.add_command('user', c.user, 'show user profile')
    program.add_command('open', c.open, 'show in browser')
    program.run()

if __name__ == '__main__':
    main()
