#1. Check dropbox directory loseit for new files
#2. For any file found load it and parse.
#   Calories marked as Exercice = -calories
#   Add all calories
#   Push to beeminder/calories for day corresponding for file name

"""
Backs up and restores a settings file to Dropbox.
This is an example app for API v2.
"""

import sys
import dropbox
import re
import os
import datetime
import pandas as pd
import sys
import ConfigParser
import datetime
import urllib
import urllib2
import requests
import sys
import simplejson
import time
import beesight
if sys.version_info[0] < 3:
    from StringIO import StringIO
else:
    from io import StringIO
#from dropbox.exceptions import ApiError, AuthError

# Add OAuth2 access token here.
# You can generate one for yourself in the App Console.
# See <https://blogs.dropbox.com/developers/2014/05/generate-an-access-token-for-your-own-account/>
TOKEN = 'uGooD_CJ_tQAAAAAAAAes1TYaG6_6XgNHn1WrW6XAhAUfAtMwfY8wiVbm57FCi2M'

LOCALFILE = 'c:\deck.txt'
BACKUPPATH = '/loseit/deck.txt'
BASMET = 2000


# Change the text string in LOCALFILE to be new_content
# @param new_content is a string
def change_local_file(new_content):
    print("Changing contents of " + LOCALFILE + " on local machine...")
    with open(LOCALFILE, 'wb') as f:
        f.write(new_content)

# Restore the local and Dropbox files to a certain revision
def restore(rev=None):
    # Restore the file on Dropbox to a certain revision
    print("Restoring " + BACKUPPATH + " to revision " + rev + " on Dropbox...")
    dbx.files_restore(BACKUPPATH, rev)

    # Download the specific revision of the file at BACKUPPATH to LOCALFILE
    print("Downloading current " + BACKUPPATH + " from Dropbox, overwriting " + LOCALFILE + "...")
    dbx.files_download_to_file(LOCALFILE, BACKUPPATH, rev)

# Look at all of the available revisions on Dropbox, and return the oldest one
def select_revision():
    # Get the revisions for a file (and sort by the datetime object, "server_modified")
    print("Finding available revisions on Dropbox...")
    revisions = sorted(dbx.files_list_revisions(BACKUPPATH, limit=30).entries,
                       key=lambda entry: entry.server_modified)

    for revision in revisions:
        print(revision.rev, revision.server_modified)

    # Return the oldest revision (first entry, because revisions was sorted oldest:newest)
    return revisions[0].rev

if __name__ == '__main__':
    # Check for an access token
    if (len(TOKEN) == 0):
        sys.exit("ERROR: Looks like you didn't add your access token. Open up backup-and-restore-example.py in a text editor and paste in your token in line 14.")

    # Create an instance of a Dropbox class, which can make requests to the API.
    #print("Creating a Dropbox object...")
    dbx = dropbox.Dropbox(TOKEN)

    # Check that the access token is valid
    try:
        dbx.users_get_current_account()
    except AuthError as err:
        sys.exit("ERROR: Invalid access token; try re-generating an access token from the app console on the web.")

    files = dbx.files_list_folder('/loseit')

    for i in range(0,len(files.entries)):
        cur_name = files.entries[i].name
        if "Daily Report" in cur_name:
            match = re.search(r'\d{8}', cur_name)
            date = time.mktime(datetime.datetime.strptime(match.group(),"%Y%m%d").timetuple())
            try:
                metadata,f  = dbx.files_download("/loseit/" + cur_name)
            except dropbox.exceptions.HttpError as err:
                print('*** HTTP error', err)
            data = StringIO(f.content)
            df = pd.read_csv(data, sep=",")
            df.update(0-df.where(df['Type']=='Exercise')['Calories'], overwrite=True)
            calo=BASMET-df['Calories'].sum()
            new_datapoint = {'timestamp': date, 'value': calo, 'comment': "loseit_script_entry"}
            beesight.post_beeminder_entry(new_datapoint)
            dbx.files_delete("/loseit/" + cur_name)
  #  print(files)
    print("Done!")