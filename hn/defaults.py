# Default config options when no config file
# is provided to the daemon

DEFAULTS = {
    'settings': {
        'interval': 60*5
    },
    'watch.worker': {
        'watch': False,
        'regexex': ''
    },
    'notify.worker': {
        'notify': False
    }
}
