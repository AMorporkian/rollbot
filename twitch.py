# For TwitchBot

# List of currently live channels, defaults empty (duh), plus another list of the game they are playing
online = []
games = []


def checkStreams():
    print 'Entering checkStreams'
    global last_update
    global online
    global games
    # Initial new lists of online channels + games, this will replace the existing one when we're done
    online_new = []
    games_new = []
    # Initial API links
    urlt = 'https://api.twitch.tv/kraken/streams?channel='
    last_update = time.time()
    # read streams file
    stramlist = open('stramlist.txt', 'r')
    print 'entering loop'
    while 1:
        # Read a line of the stream list, removing the newline at the end
        read_stream = stramlist.readline()[:-1]
        # if end of list, we're done, now put that API link to use
        if read_stream == '':
            print 'Done reading'
            stramlist.close()
            try:
                print 'Checking Twitch'
                datat = json.load(urllib2.urlopen(urlt))
            except:
                print 'Something went wrong checking Twitch'
                return
            for i in range(0, len(datat["streams"])):
                # Set some default values for these variables
                # Partly just in case, partly because I don't know python
                display_name = "SomethingBroke"
                stream_title = "Something broke"
                game_playing = "Something broke"
                site = "Twitch"
                # Streams only show up if online, so get info
                display_name = datat["streams"][i]["channel"]["display_name"]
                stream_title = datat["streams"][i]["channel"]["status"]
                game_playing = datat["streams"][i]["game"]
                list_name = display_name + " (" + "http://twitch.tv/" + display_name + ")"
                link = "http://twitch.tv/" + display_name
                online_new.append(list_name)
                games_new.append(game_playing)
                # if stream is in the CURRENT online list playing the same game, nothing to announce
                # if stream is in the CURRENT online list and their game doesn't match, announce new game
                if list_name in online and games[online.index(list_name)] != game_playing:
                    announceStream(None, list_name, stream_title, game_playing, site, link, 0, 1)
                # if stream is NOT in the CURRENT online list, they just went live, announce
                elif list_name not in online:
                    announceStream(None, display_name, stream_title, game_playing, site, link, 0, 0)
            # replace the online/game list with the ones we just made
            print 'list swap time\nonline: ' + str(len(online)) + '\nonlinenew: ' + str(len(online_new)) + '\n'
            online = online_new
            games = games_new
            return
        # back to reading the file, check which site t/h the channel is and get name
        site = read_stream.split(' ')[0]
        name = read_stream.split(' ')[1]
        # append the channel name to the appropriate API link
        if site == 't':
            urlt = urlt + name + ","


def announceStream(chan, name, title, game, site, link, viewers, form):
    # form 0 = Just went live, 1 = changed games, 2 = random stream
    # Freaky unicode characters will break things, so don't display the title in that case
    if not title:
        title = "Untitled Broadcast"
    if not game:
        game = "nothing"
    try:
        title = "\"" + title + "\""
    except:
        title = "(error in title)"
    title = title.replace('\n', '')
    title = title.replace('\r', '')
    if form == 0:
        for i in range(0, len(channel)):
            sendmsg(channel[i], name + " just went live on " + site + " playing " + game + " - " + title + " - " + link)
    if form == 1:
        for k in range(0, len(channel)):
            sendmsg(channel[k], name + " switched games to " + game + " - " + title + " - " + link)
    if form == 2:
        sendmsg(chan, name + " playing " + game + " for " + str(viewers) + " viewers - " + title + " - " + link)


