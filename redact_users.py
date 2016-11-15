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
WHITELISTED_KEYS = ['deleted', 'status', 'is_bot']

users = json.load(open("users.json", 'rb'))
output_file = "users_redacted.json"

def hash_tag(tag):
    prefix, id, suffix = re.search(r'(.*[UT])([\w]+)(.*)', tag).groups()
    return prefix + hashlib.sha256(SALT + id).hexdigest() + suffix

def redacter(user_file):
	redacted_user_file = []
	for profile in user_file:
		#print profile
		profile = dict(profile)
		redacted_profile = {}
		#print profile
		for key, value in profile.iteritems():

			#print (key, value)
			if key == "name":
				profile[key] = "redacted"
				redacted_profile[key] = profile[key]

			elif key == "real_name":
				profile[key] = "redacted"
				redacted_profile[key] = profile[key]

			elif key == "first_name":
				profile[key] = "redacted"
				redacted_profile[key] = profile[key]

			elif key == "last_name":
				profile[key] = "redacted"
				redacted_profile[key] = profile[key]

			elif key == "image_24":
				profile[key] = "redacted"
				redacted_profile[key] = profile[key]

			elif key == "image_32":
				profile[key] = "redacted"
				redacted_profile[key] = profile[key]

			elif key == "image_48":
				profile[key] = "redacted"
				redacted_profile[key] = profile[key]

			elif key == "image_72":
				profile[key] = "redacted"
				redacted_profile[key] = profile[key]

			elif key == "image_192":
				profile[key] = "redacted"
				redacted_profile[key] = profile[key]

			elif key == "image_512":
				profile[key] = "redacted"

			elif key == "image_original":
				profile[key] = "redacted"
				redacted_profile[key] = profile[key]

			elif key == "email":
				profile[key] = "redacted"

				redacted_profile[key] = profile[key]

			elif key == "phone":
				profile[key] = "redacted"

			elif key == "skype":
				profile[key] = "redacted"

				redacted_profile[key] = profile[key]

			elif key == "real_name_normalized":
				profile[key] = "redacted"

				redacted_profile[key] = profile[key]

			elif key == "id":
				profile[key] = hash_tag(profile[key])

				redacted_profile[key] = profile[key]

			elif key == "team_id":
				profile[key] = hash_tag(profile[key])

				redacted_profile[key] = profile[key]

			elif type(profile[key]) == dict:
				pass

			elif key in WHITELISTED_KEYS:
				redacted_profile[key] = profile[key]
			else:
				print 'skipping', key
		redacted_user_file.append(redacted_profile)
	#print redacted_user_file
	return redacted_user_file

json.dump(redacter(users), open(output_file, 'wb'), indent=2)
        #json.dump(users, open(os.path.join(arguments.chat_redact_dir, arguments.channel_name, os.path.basename(log_file)), 'wb'), indent=2)




"""



for profile in users:

	if "first_name" in profile:
		#firstname = profile["first_name"]
		profile["first_name"] = "redacted"


	if "last_name" in profile:
		#lastname = profile["last_name"]
		profile["last_name"] = "redacted"

	if "real_name" in profile:
		#realname = users["real_name"]
		profile["real_name"] = "redacted"

	if "image_24" in profile:
		#firstname = users["first_name"]
		profile["image_24"] = "redacted"

	if "image_48" in profile:
		#firstname = users["first_name"]
		profile["image_48"] = "redacted"

	if "image_72" in profile:
		#firstname = users["first_name"]
		profile["image_72"] = "redacted"

	if "email" in profile:
		#firstname = users["first_name"]
		profile["email"] = "redacted"



print users


#with open("redacted_users.json") as output_file:
	#json.dump(users, open(output_file, 'wb')

"""



