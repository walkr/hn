# This modules implents the logic for the commands
# supported by the daemon program

import requests
import webbrowser

from . import endpoints


class Commands(object):
    """ The commands supported by the daemon """

    def __init__(self, program):
        self.program = program

    def _render(self, index, storyid=None):
        """ Render a story """

        layout = u"""
        {index:2n}. {title} - ({hostname})
            {score} points by {by} {time} ago | {descendants} comments
        """
        data = self.program.state.stories[storyid]
        return layout.format(index=index, **data)

    # ----------------------------------------------

    def which(self, section):
        """ Render stories from `section` (top, new, ask, show, etc) """

        self.program.state.last_viewed = section
        ids = getattr(self.program.state, section)
        return ''.join([
            self._render(i+1, s) for i, s in enumerate(ids)
        ])

    def user(self, username='None'):
        """ Render a user's profile """

        layout = u"""
        user: {id}
        created: {created}
        karma: {karma}
        about: {about}
        """
        userdata = requests.get(endpoints.USER.format(username)).json()
        return layout.format(**userdata) if userdata else 'user not found'

    def ping(self):
        """ Check HN site status """

        res = requests.get('https://news.ycombinator.com/news')
        return res.status_code

    def open(self, index):
        """ Open in browser a story with `index`
        from the latest viewed section """

        index = int(index.strip())
        index -= 1
        section = self.program.state.last_viewed
        storyid = getattr(self.program.state, section)[index]
        data = self.program.state.stories[storyid]
        webbrowser.open(data['url'])
