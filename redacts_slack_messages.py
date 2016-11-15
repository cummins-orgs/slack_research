import json
import sys
import argparse
import os.path
import glob
import re
import itertools
import datetime
import os
import hashlib

SALT = '<RANDOM STRING HERE>'
WHITELISTED_KEYS = ['text', 'type', 'ts', 'user', 'attachments', 'file', 'comment']

parser = argparse.ArgumentParser(description='Remove message content from Slack export chat files to redact them. Keep user-to-user info.')
parser.add_argument('chat_export_dir', metavar='DIR', type=str,
                   help='the path to the directory of chat files downloaded from https://my.slack.com/services/export')
parser.add_argument('chat_redact_dir', metavar='REDACTDIR', type=str,
                   help='the path to the directory of you want the redacted chat files to go to')
parser.add_argument('channel_name', metavar='CHANNEL', type=str,
                    help='the name of the channel from which to extract/redact messages')
parser.add_argument('start_date', metavar='FROM', type=str,
                    help='the yyyy-mm-dd date you want to start the collection from')
parser.add_argument('end_date', metavar='TO', type=str,
                    help='the yyyy-mm-dd date you want to end the collection at')
arguments = parser.parse_args()
if not os.path.isfile(os.path.join(arguments.chat_export_dir, 'users.json')):
    print 'I couldn\'t find a users.json file in the chat_export_dir you specified. Bye!'
    sys.exit(0)

if not os.path.isdir(os.path.join(arguments.chat_export_dir, arguments.channel_name)):
    print 'I couldn\'t find a folder for the channel you specified. Bye!'
    sys.exit(0)

start = datetime.datetime.strptime(arguments.start_date, '%Y-%m-%d')
end = datetime.datetime.strptime(arguments.end_date, '%Y-%m-%d')
if not end > start:
    print 'The start_date has to be before the end_date, I\'m afraid! Bye!'
    sys.exit(0)

def hash_tag(tag):
    prefix, id, suffix = re.search(r'(.*[UT])([\w]+)(.*)', tag).groups()
    return prefix + hashlib.sha256(SALT + id).hexdigest() + suffix

def tagged_people(message_text):
    '''
    Extract user_ids from @mentioned in a message.
    '''
    regexr = re.compile('(<@U[\w]{8,8}>)')
    unnamed_tags = regexr.findall(message_text)
    regexr = re.compile('(<@U[\w]{8,8}\|)')
    named_tags = regexr.findall(message_text)
    return [hash_tag(tag) for tag in set(unnamed_tags).union(named_tags)]

daily_log_files = glob.glob(os.path.join(arguments.chat_export_dir, '%s/*.json' % arguments.channel_name))
try:
    os.mkdir(os.path.join(arguments.chat_redact_dir, arguments.channel_name))
except:
    pass

for log_file in daily_log_files:
    log_date = datetime.datetime.strptime(os.path.basename(log_file)[:-5], '%Y-%m-%d')
    if log_date > start and log_date < end:
        chats = json.load(open(log_file, 'rb'))
        redacted_chats = []
        for chat in chats:
            redacted_chat = {key: val for key, val in chat.items() if key in WHITELISTED_KEYS}
            if 'user' in redacted_chat:
                redacted_chat['user'] = hash_tag(redacted_chat['user'])
            if 'text' in redacted_chat:
                ppl = tagged_people(redacted_chat['text'])
                redacted_chat['text'] = "redacted " + " ".join(ppl)
            if 'comment' in redacted_chat:
                ppl = tagged_people(redacted_chat['comment']['comment'])
                redacted_chat['comment']['comment'] = "redacted " + " ".join(ppl)
            if 'file' in redacted_chat:
                redacted_chat['file'] = {'redacted': "true"}
            if 'attachments' in redacted_chat:
                redacted_chat['attachments'] = {'redacted': "true"}
            redacted_chats.append(redacted_chat)

        json.dump(redacted_chats, open(os.path.join(arguments.chat_redact_dir, arguments.channel_name, os.path.basename(log_file)), 'wb'), indent=2)

