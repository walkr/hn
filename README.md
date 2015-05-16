hn
=========
read HN from the command line

![screenshot](http://i.imgur.com/xxWGfKu.png)


### Install

```shell
make install
```

### Usage

1. Start the daemon
2. Use the command line interface

```shell
# Start the daemon
$ hncd

# Use the cli interface
$ hnctl
ctl >
ctl > ping              # ping HN site
ctl > top               # show top stories
ctl > open 1            # open story <1> in browser
ctl > new               # show new stories
ctl > user pg           # show user <pg>
ctl > help              # show help
ctl > help user         # show help for command <user>
ctl > quit

# You can also invoke a command directly w/o the loop
$ hnctl top
$ hnctl open 1
```