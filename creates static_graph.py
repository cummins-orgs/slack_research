import networkx as nx
import json
import sys
import argparse
import os.path
import matplotlib.pyplot as plt
import glob
import re
import itertools
import random

parser = argparse.ArgumentParser(description='Make a force directed graph of people talking in your public Slack channels.')
parser.add_argument('chat_export_dir', metavar='DIR', type=str,
                   help='the path to the directory of chat files downloaded from https://my.slack.com/services/export')
arguments = parser.parse_args()   
if not os.path.isfile(os.path.join(arguments.chat_export_dir, 'users.json')):
    print 'I couldn\'t find a users.json file in the chat_export_dir you specified. Bye!'
    sys.exit(0)

users = json.load(open(os.path.join(arguments.chat_export_dir, 'users.json'), 'rb'))

humans = [u for u in users if not u.get('is_bot', False) and not u.get('deleted', False) and not u.get('is_ultra_restricted', False)]

G = nx.DiGraph()

for human in humans:
    G.add_node(str(human['id']), color=random.choice(['r','g','b']))

for human in humans:
    for friend in humans:
        if human==friend:
            # Dont link them to themself
            continue
        G.add_edge(human['id'], friend['id'], weight=0)

users = {h['id']: h for h in humans}

channels = glob.glob(os.path.join(arguments.chat_export_dir, '*'))
channels = [c for c in channels if os.path.isdir(c)]

class Conversation(object):
    '''
    A Conversation is a group of messages. 
    This is a very basic implementation, which thinks that a message is part of
    a conversation if it happened within some number of seconds of the previous
    message in the same channel. 
    '''
    def __init__(self, starting_message, possible_participants=[], relaxation_time=300):
        # Make sure this Conversation is being started by a human
        if not 'user' in starting_message:
            self.ended = True
            return
        self.participants = set([starting_message['user']])
        self.most_recent_timestamp = float(starting_message['ts'])
        self.ended = False
        self.relaxation_time = relaxation_time
        self.possible_participants = possible_participants
        self.no_bots()
    
    def no_bots(self):
        '''
        Get rid of none-users!
        '''
        self.participants.intersection_update(self.possible_participants)
    
    def add_to_conversation(self, message, endifnot=True):
        '''
        Check if this message is part of this conversation. Update the convo
        participants if so, else optionally end the conversation (you probably
        want to do this because you're iterating through messages in ascending
        timestamp order!)
        Returns true if the message contributed to conversation, false if not.
        '''
        if float(message['ts']) - self.most_recent_timestamp < self.relaxation_time:
            self.most_recent_timestamp = float(message['ts'])
            if 'user' in message: self.participants.add(message['user'])  # The person who said the message is part of this conversation
            if 'comment' in message: self.participants.add(message['comment']['user']) # Commentors username is in a different place, for whatever reason
            if 'text' in message:
                tags = tagged_people(message['text']) # People @mentioned in the message are part of the conversation
                if tags: self.participants = self.participants.union([t[2:-1] for t in tags])
            if message.get('subtype', None) == 'file_comment': # People @mentioned in comments are predictably listed somewhere else
                tags = tagged_people(message['comment']['comment']) 
                if tags: self.participants = self.participants.union([t[2:-1] for t in tags])
            self.no_bots() 
            return True # Message was part of convo
        if endifnot: self.ended = True # Convo is over, because new message wasn't deemed part of this convo.
        self.no_bots()
        return False # Message was not part of convo!
    
    @property
    def pairs(self):
        '''
        Every relationship within the conversation.
        '''
        self.no_bots()
        return itertools.combinations(self.participants, 2)

def tagged_people(message_text):
    '''
    Extract user_ids from @mentioned in a message.
    Returns like <@U12345678> so you might want to do tagged_people('...')[2:-1]
    after this to just get U12345678, maybe.
    '''
    regexr = re.compile('(<@U[\w]{8,8}>)')
    unnamed_tags = regexr.findall(message_text)
    regexr = re.compile('(<@U[\w]{8,8}\|)')
    named_tags = regexr.findall(message_text)
    if unnamed_tags and named_tags:
        return set(unnamed_tags).union(named_tags)
    elif unnamed_tags:
        return set(unnamed_tags)
    elif named_tags:
        return set(named_tags)
    else:
        return None


for channel in channels:
    daily_log_files = glob.glob(os.path.join('%s/*.json' % channel))
    print 'Found %d days of logs for `%s` channel' % (len(daily_log_files), channel)
    for log_file in daily_log_files:
        chats = json.load(open(log_file, 'rb'))
        convo = None
        for m, message in enumerate(chats):
            if (not convo) or convo.ended:
                convo = Conversation(message, possible_participants=users)
                continue
            joining_convo = convo.add_to_conversation(message, True)
            if m == len(chats) - 1 or not joining_convo :
                for pair in convo.pairs:
                    G[pair[0]][pair[1]]['weight'] += 1 # They conversed, so make this a stronger graph edge.
                convo = Conversation(message, possible_participants=users) # then a new conversation was started by this message

fig = plt.figure(0)
pos = nx.spring_layout(G)
nx.draw_networkx(G, pos)
plt.title('')
plt.savefig('graph.png')




































