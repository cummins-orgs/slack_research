import json
import glob
import argparse
import os
import re
import itertools

# Read the command line arguments to find out where the export data is
parser = argparse.ArgumentParser(description='Extract message metadata from a Slack data export, to then be used by a d3.js animation.')
parser.add_argument('C:\Users\user\Documents\code testing', metavar='DIR', type=str,
                   help='the path to the directory of chat files downloaded from https://my.slack.com/services/export')
arguments = parser.parse_args()   
if not os.path.isfile(os.path.join(arguments.chat_export_dir, 'users.json')):
    print 'I couldn\'t find a users.json file in the chat_export_dir you specified. Bye!'
    sys.exit(0)

# Load the users file, for details about all the people we want to look at
users = json.load(open(os.path.join(arguments.chat_export_dir, 'users.json'), 'rb'))

# channels = ['general', 'product-team', 'watercooler', 'competitors', 'science', 'design-userresearch', 'goals-objectives']
channels = glob.glob(os.path.join(arguments.chat_export_dir, '*'))
channels = [c for c in channels if os.path.isdir(c)]
# channels = [os.path.basename(c) for c in channels]

print 'I\'m going to look for messages in all these channels:'
print channels

# Get rid of deleted people and bots
users = [u for u in users if not u.get('is_bot', False) and not u.get('deleted', False) and 
         not u.get('is_ultra_restricted', False)]

# Get their user_ids, because we work on those rather than names or whatever
user_ids = [user['id'] for user in users]

messages = []

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


# TODO: be less hacky, ha.
communication_maps = []
for channel in channels[:]:
    communication_map = []
    daily_log_files = glob.glob(os.path.join('%s/*.json' % channel))
    print 'Found %d days of logs for `%s` channel' % (len(daily_log_files), channel)
    for log_file in daily_log_files:
        daily_comms_map = {u: {v: 0 for v in user_ids if u != v} for u in user_ids}
        chats = json.load(open(log_file, 'rb'))
        convo = None
        for m, message in enumerate(chats):
            if (not convo) or convo.ended:
                convo = Conversation(message, possible_participants=user_ids)
                continue
            joining_convo = convo.add_to_conversation(message, True)
            if m == len(chats) - 1 or not joining_convo :
                for pair in convo.pairs:
                    daily_comms_map[pair[0]][pair[1]] += 1 # this pair had a chat!
                    daily_comms_map[pair[1]][pair[0]] += 1 # same pair, reversed :|
                convo = Conversation(message, possible_participants=user_ids) # then a new conversation was started by this message
        communication_map.append({
                'date': os.path.basename(log_file)[:-5],
                'edges': daily_comms_map,
                'channel': channel
            })
    communication_maps.append(communication_map)

alldates = []
for communication_map in communication_maps:    
    alldates.extend([m['date'] for m in communication_map])
alldates = set(alldates)
alldates = list(alldates)
alldates = sorted(alldates)
# alldates is time-ascending list of every day messages happened

# Now unify accross channels, to get a picture over the entire Slack group.
# We count daily and cumulative, so that we can see the daily changes or the
#   long terms trends on the animation.
unified_communication_map = []
cumulative_comms_map = {u: {v: 0 for v in user_ids if u != v} for u in user_ids}
for d, date in enumerate(alldates):
    
    # Limit to recent years (delete these 2 lines for full history):
    if not ('2015' in date or '2016' in date):
        continue
        
    daily_comms_map = {u: {v: 0 for v in user_ids if u != v} for u in user_ids}
    for communication_map in communication_maps:
        for day in communication_map:
            if day['date'] == date:
                for u in user_ids:
                    for v in user_ids:
                        if u != v:
                            daily_comms_map[u][v] += day['edges'][u][v]
                            cumulative_comms_map[u][v] += day['edges'][u][v]
                            daily_comms_map[v][u] += day['edges'][u][v]
                            cumulative_comms_map[v][u] += day['edges'][u][v]
                            
    # Normalise so that every pair's communication strength is relative to the
    #   maximum strength on that day. Removes the effect of "quiet-days" from 
    #   the animation, so it doesn't jump around so much.
    max_today = 0.00001
    max_to_today = 0.00001
    for p1 in daily_comms_map:
        for p2 in daily_comms_map[p1]:
            max_today = float(max(daily_comms_map[p1][p2], max_today))
            max_to_today = float(max(cumulative_comms_map[p1][p2], max_to_today))
    unified_communication_map.append({
            'date': date,
            'edges': {u: {v: daily_comms_map[u][v] / (max_today) for v in daily_comms_map[u]} for u in daily_comms_map},
            'cumulative_edges': {u: {v: cumulative_comms_map[u][v] / (max_to_today) for v in cumulative_comms_map[u]} for u in cumulative_comms_map}
        })

# Write out the file for the animation code to read
json.dump(unified_communication_map, open('chat_data.json', 'wb'))
json.dump(users, open('users.json', 'wb'))
print 'Hey, I wrote the output file to chat_data.json'
print 'You might now want to look at the animation.'
print 'type: \n python -m SimpleHTTPServer 8002 \n and press enter'
print 'Then open your Browser to http://localhost:8002 to see the animation'
print 'Bye!'



