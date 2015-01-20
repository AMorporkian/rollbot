#!/usr/bin/python
# -*- coding: latin-1 -*-
# import os, sys

# Import what's needed.
import random

import socket, string, os, time
import json
import re
from logbook import Logger
import inspect


def command(method):  # A decorator to automatically register and add commands to the bot.
    method.is_command = True
    return method


class RollBot:
    CONFIG_LOCATION = "./config.json"

    def __init__(self):
        self.command_list = {}
        self.logger = Logger('RollBot', level=2)
        self.logger.info("RollBot started.")

        for name, method in inspect.getmembers(self.__class__, predicate=inspect.ismethod):
            if getattr(method, "is_command", False):
                self.command_list[name] = getattr(self, name)
                self.logger.info("Added '{}' as a command.", name)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.last_ping = None
        self.registered = False
        with open(self.CONFIG_LOCATION) as f:
            self.config = json.load(f)
        self.nick = self.config['botnick']
        self.command_prefix = self.config['prefix']

    def send_message(self, channel, message):
        message_template = "PRIVMSG {} :{}"
        self.send_raw(message_template.format(channel, message))

    def send_ping(self, ping_message):
        message_template = "PONG : {}"
        self.send_raw(message_template.format(ping_message))
        self.update_ping_time()

    def join_channel(self, channel):
        message_template = "JOIN {}"
        self.send_raw(message_template.format(channel))

    def leave_channel(self, channel):
        message_template = "PART {}"
        self.send_raw(message_template.format(channel))

    def connect(self):
        server_information = (self.config['server'], self.config['port'])
        self.socket.connect(server_information)
        self.send_raw("PASS " + self.config['password'])
        self.send_raw("USER {} {} {} :{}".format(self.nick, self.nick, self.nick, "rollbot"))
        self.send_raw("NICK " + self.nick)
        self.run_loop()

    def get_message_from_server(self):
        message = ""
        current_character = self.socket.recv(1)
        while current_character != "\n":
            message += current_character
            current_character = self.socket.recv(1)
        return message

    def run_loop(self):
        message_regex = r"^(?:[:](?P<prefix>\S+) )" \
                        r"?(?P<type>\S+)" \
                        r"(?: (?!:)(?P<destination>.+?))" \
                        r"?(?: [:](?P<message>.+))?$"  # Extracts all appropriate groups from a raw IRC message
        compiled_message = re.compile(message_regex)

        while True:
            try:
                message = self.get_message_from_server()
                self.logger.debug("Received server message: {}", message)
                parsed_message = compiled_message.finditer(message)
                message_dict = [m.groupdict() for m in parsed_message][0]  # Extract all the named groups into a dict
                source_nick = ""
                if "!" in message_dict['prefix']:  # Is the prefix from a nickname?
                    source_nick = message_dict['prefix'].split("!")[0]  # If so, extract the nickname from the prefix.

                if message_dict['type'] == "PING":
                    self.send_ping(message_dict['message'])

                if message_dict['type'] == "PRIVMSG":
                    self.handle_message(source_nick, message_dict['destination'], message_dict['message'])

                if message_dict['type'] == "001":  # Registration confirmation message
                    self.registered = True
                    self.logger.info("{} connected to server successfully.", self.nick)
                    for channel in self.config['channel']:
                        self.logger.info("Attempting to join {}", channel)
                        self.join_channel(channel)

            except socket.timeout:
                self.logger.error("Disconnected. Attempting to reconnect.")
                self.socket.close()
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.connect()

    def handle_message(self, source, destination, message):
        is_command = message.startswith(self.config['prefix'])
        if is_command:
            self.handle_command(source, destination, message)

    def handle_command(self, source, destination, message):
        split_message = message[1:].split()
        command_key = split_message[0].lower()
        arguments = split_message[1:]
        reply_to = destination
        if destination == self.nick:
            reply_to = source  # If it's a private message, reply to the source. Otherwise it's a channel message and reply there.
        if command_key in self.command_list:
            self.logger.info("Received command '{}' from {}", command_key, source)
            return_message = self.command_list[command_key](source, reply_to, *arguments)
            if return_message is not None:
                if isinstance(return_message, basestring):  # Is it a string?
                    self.send_message(reply_to, return_message)  # If so, just send it along.
                else:  # Otherwise it's a list or a tuple
                    for message in return_message:  # So let's loop over them all
                        self.send_message(reply_to, message)  # And send them.
        else:
            combined_command = self.command_prefix + command_key
            self.send_message(reply_to, "Sorry, {} isn't a recognized command.".format(combined_command))

    def send_raw(self, message):
        return self.socket.send((message + "\n").encode("utf-8"))

    def update_ping_time(self):
        self.last_ping = time.time()

    # Commands
    @command
    def about(self, source, reply_to, *args):
        return "Hi my name is {} and currently turtlemansam is holding me hostage. " \
               "If anyone could 934-992-8144 and tell me a joke to help pass the time, " \
               "that would be great.".format(self.nick)

    @command
    def commands(self, source, reply_to, *args):
        return "Available commands: {}".format(", ".join(sorted(self.command_list.keys())))

    @command
    def netsplit(self, source, reply_to, *args):
        return "technically we all netsplit http://pastebin.com/mPanErhR"

    @command
    def weather(self, source, reply_to, *args):
        return "look out your goddamn window"

    @command
    def insult(self, source, reply_to, insultee=None, *args):
        if insultee is None:
            return "Who shall I insult?"
        else:
            with open("insults.txt") as f:
                insult = random.choice(list(f))
            messages = ("You're a pretty cool guy, {}".format(insultee),
                        insult)
            return messages

    @command
    def tagpro(self, source, reply_to, *args):
        random_idea = "I wish tagpro was {}"
        with open("iWishTagProWas.txt") as f:
            return random_idea.format(random.choice(list(f)))


if __name__ == "__main__":
    bot = RollBot()
    bot.connect()

"""

# Main Commands

def commands(nick, chan, msg):
    # handling pivate messages
    if msg.split(" ")[2] == botnick:
        chan = nick

    # define command
    command = msg.split(" ")[3]

    # get argument, only if it exists
    if len(msg.split(" ")) == 4:
        argument = None
    else:
        argument = msg.split(" ")[4]

    # Command: About
    # Command: commands
    # Command: owner commands
    elif (command == ":" + prefix + "owner"):
        sendmsg(chan, "join, part, quit")
    # Command: Help
    elif (command == ":" + prefix + "help"):
        if argument == None:
            sendmsg(chan, "Which command would you like help with?")
        elif argument == "mods":
            sendmsg(chan, "|mods - Notifies in-game moderators")
        elif argument == "netsplit":
            sendmsg(chan, "|netsplit - technically...")
        elif argument == "weather":
            sendmsg(chan, "|weather - Accurently predicts the weather in your area")
        elif argument == "insult":
            sendmsg(chan, "|insult - Send a mean insult to any user. Takes 1 argument")
        elif argument == "tagpro":
            sendmsg(chan, "|tagpro - Have me respond with what kind of game I wish TagPro was")
        elif argument == "flirt":
            sendmsg(chan, "|flirt - Sends a cheesy flirt message to the channel")
        elif argument == "fortune":
            sendmsg(chan, "|fortune - Have me accurently predict your fortune")
        elif argument == "ISITALLCAPSHOUR":
            sendmsg(chan, "|ISITALLCAPSHOUR - Checks if it's all caps hour (1 o'clock EST)")
        elif argument == "rate":
            sendmsg(chan, "|rate - Rate any user based on their nick. Takes 1 argument")
        elif argument == "streams":
            sendmsg(chan, "|streams - Checks if any approved streamers are currently online")
        elif argument == "commands":
            sendmsg(chan, "|commands - Recieve a list of all commands")
        elif argument == "about":
            sendmsg(chan, "|about - Learn about me and my owner!")
        elif argument == "help":
            sendmsg(chan, "|help - Recieve more info about any command")
        else:
            sendmsg(chan, "Sorry! That's not a command you dumb fuck")

    # Trigger: hey
    elif ircmsg.find(":" + "hey " + botnick or ":" + "hello " + botnick or ":" + "hi " + botnick) != -1:
        sendmsg(chan, "Hey " + nick + "!")
    # Trigger: hi
    elif ircmsg.find(":" + "hi " + botnick) != -1:
        sendmsg(chan, "Hey " + nick + "!")
    # Command: mods
    elif (command == ":" + "!mods"):
        if chan == nick:
            sendmsg(nick, "Sorry! You must be in a channel to use this command")
        elif chan == "#TPmods":
            ircsock.send("NOTICE " + nick + " :" + nick + ": The mods have recieved your request. Please be patient\n")
            sendmsg("#tagpromods", "Mod request from " + nick + " in " + chan + "!")
            sendmsg("#tagpromods",
                    "Mods: Flail, Hoog, Watball, Corhal, Ly, tim-sanchez, _Ron, Aaron215, JGibbs, Radian, cz, TinkerC, Bull_tagpro, pooppants, turtlemansam, McBride36, deeznutz, bizkut, poopv, Rems, Rambo, bbq, Akiki, TimeMod, rDuude, yo_cat, Virtulis")
        else:
            ircsock.send(
                "NOTICE " + nick + " :" + nick + ": The mods have recieved your request. Please type /join #TPmods and be patient.\n")
            sendmsg("#tagpromods", "Mod request from " + nick + " in " + chan + "!")
            sendmsg("#tagpromods",
                    "Mods: Flail, Hoog, Watball, Corhal, Ly, tim-sanchez, _Ron, Aaron215, JGibbs, Radian, cz, TinkerC, Bull_tagpro, pooppants, turtlemansam, McBride36, deeznutz, bizkut, poopv, Rems, Rambo, bbq, Akiki, TimeMod, rDuude, yo_cat, Virtulis")



    # Trigger: ,
    #elif ircmsg.find(" ,") != -1:
    #	sendmsg(chan, "nice floating comma dickbrain")
    # Trigger: can
    elif ircmsg.find(":" + botnick + " can ") != -1:
        sendmsg(chan, "hey " + nick + " how bout you dont tell me what to do")
    # Trigger: lol
    elif ircmsg.find(":lol " + botnick) != -1:
        sendmsg(chan, "stop laughing at me im not a fucking peanut")
    # Trigger: wat
    #elif (command == ":" + "wat"):
    #	sendmsg(chan, "no u")
    # Command: TagPro
    elif (command == ":" + prefix + "tagpro"):
        sendmsg(chan, "I wish tagpro was " + (random.choice(list(open('iWishTagProWas.txt')))))
    # Command: Flirt
    elif (command == ":" + prefix + "flirt"):
        sendmsg(chan, (random.choice(list(open('flirt.txt')))))
    # Command: fortune
    elif (command == ":" + prefix + "fortune"):
        sendmsg(chan, nick + ", " + (random.choice(list(open('fortune.txt')))))
    # Command: ISITALLCAPSHOUR
    elif (command == ":" + prefix + "ISITALLCAPSHOUR"):
        now = datetime.now()
        if now.hour == 13:
            sendmsg(chan, "YES IT IS, BITCHES")
        else:
            sendmsg(chan, "no " + nick + ", it is not.")
    # Command: rate
    elif (command == ":" + prefix + "rate"):
        if argument == None:
            sendmsg(chan, "Who do you want me to rate?")
        else:
            sendmsg(chan, argument + " has a rating of: %s" % (random.randint(1, 100)))
    # Command: streams
    #elif (command == ":" + prefix + "streams"):
    #	checkStreams()
    #	if not online:
    #		sendmsg(chan, "No TagPro streams online.")
    #	else:
    #		sendmsg(chan, "Currently live: " + ', '.join(online))
    # Trigger: slap
    elif ircmsg.find("slaps " + botnick) != -1:
        sendmsg(chan, "bitch ill slap you right back")
    # Command: roll
    elif (command == ":" + prefix + "roll"):
        sendmsg(chan, "Sorry %s, I can't do that right now." % (nick))
    # Command: !ticket
    elif (command == ":!ticket"):
        sendmsg(chan, "http://support.koalabeast.com/#/appeal")

    # Owner commands
    if nick in owner:
        # quit
        if (command == ":" + prefix + "quit"):
            ircsock.send("QUIT :rollbot's out!\n")
            ircsock.shutdown(1)
            ircsock.close()
            exit()
        # join
        elif (command == ":" + prefix + "join" and argument != None):
            joinchan(argument)
            channel.append(argument)
        # part
        elif (command == ":" + prefix + "part"):
            leavechan(chan)

# lets connect
connect()

while 1:
    try:
        now = time.time()
        ircmsg = ircsock.recv(2048)  # get data
        ircmsg = ircmsg.strip('\n\r')  # remove new lines
        print(ircmsg)

        if ircmsg.find("PING :") > -1:
            ping(ircmsg[6:])

        if ircmsg.find(' PRIVMSG ') != -1:
            nick = ircmsg.split('!')[0][1:]
            comchan = ircmsg.split(' PRIVMSG ')[-1].split(' :')[0]
            commands(nick, comchan, ircmsg)
    except socket.timeout:
        print 'Disconnected'
        ircsock.close()
        ircsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        connect()
"""