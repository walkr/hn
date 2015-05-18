hn
=========
read HN from the command line

![travis-ci](https://travis-ci.org/walkr/hn.svg)

![screenshot](http://i.imgur.com/xxWGfKu.png)

**Features**

* Modular, "daemon" + ctl
* Daemon can watch for regexes in stories and trigger notifications (currently broken on OSX) or do any other type of work

### Install

```shell
$ make install
```

### Usage

1. Start the daemon
2. Use the command line interface

```shell
# Start the daemon
$ hnd

# OR start the daemon with a config file (see example config file)
$ hnd --config hn/hn.conf

# Use the command line interface
$ hnctl
ctl >
ctl > top               # show top stories
ctl > new               # show new stories
ctl > ask               # show ask stories
ctl > jobs              # show jobs stories
ctl > show              # show "show hn" stories

ctl > ping              # ping HN site
ctl > open 1            # open story <1> in browser
ctl > user pg           # show user <pg>
ctl > help              # show help
ctl > help user         # show help for command <user>
ctl > quit              # quit

# You can also invoke a command directly w/o the loop
$ hnctl top
$ hnctl open 1
```

MIT Licensed