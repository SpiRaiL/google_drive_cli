# instructions from: # https://developers.google.com/drive/v3/web/quickstart/python

from __future__ import print_function
import httplib2
import os

from apiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/drive-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/drive.metadata.readonly'
CLIENT_SECRET_FILE = 'drive_backup/client_id.json'
APPLICATION_NAME = 'Drive API Python Quickstart'

"""
    an object for a particular file or folder in google drive
"""
class Drive_object():
    def __init__(self, json):
        self.json = json
        self.id = json.get('id')
        self.name = json.get('name')
        self.mimeType = json.get('mimeType')
        self.trashed = json.get('trashed')
        self.parents= json.get('parents')

    def as_string(self):
        string = ""
        #string += "%s\t " % self.json
        string += "%s\t " % self.id
        string += "%s\t " % self.mimeType
        string += "%s\t " % self.trashed
        string += "%s\t " % self.parents
        string += "%s\t " % self.name
        return string

"""
    the connection and commands to google drive
"""
class Drive():
    """Shows basic usage of the Google Drive API.

    Creates a Google Drive API service object and outputs the names and IDs
    for up to 10 files.
    """
    def __init__(self):
        credentials = self.get_credentials()
        http = credentials.authorize(httplib2.Http())
        self.service = discovery.build('drive', 'v3', http=http)

    def get_credentials(self):
        """Gets valid user credentials from storage.
    
        If nothing has been stored, or if the stored credentials are invalid,
        the OAuth2 flow is completed to obtain the new credentials.
    
        Returns:
            Credentials, the obtained credential.
        """
        home_dir = os.path.expanduser('~')
        credential_dir = os.path.join(home_dir, '.credentials')
        if not os.path.exists(credential_dir):
            os.makedirs(credential_dir)
        credential_path = os.path.join(credential_dir,
                                       'drive-python-quickstart.json')
    
        store = oauth2client.file.Storage(credential_path)
        credentials = store.get()
        if not credentials or credentials.invalid:
            flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
            flow.user_agent = APPLICATION_NAME
            if flags:
                credentials = tools.run_flow(flow, store, flags)
            else: # Needed only for compatibility with Python 2.6
                credentials = tools.run(flow, store)
            print('Storing credentials to ' + credential_path)
        return credentials


    #gets the root of the tree to be replicated
    def get_root(self, name=None):
        if name is None:
            name = "00 GDRIVE_NEW"
        results = self.search_name(name)
        result = results[0].id
        return result

    def search_name(self, name, contains= False, **kargs):
        #resolve wild cards
        if contains: contains = ' contains '
        else: contains = "="

        return self.search( "name%s'%s'" % (contains, name), **kargs)

    #search file by name
    def search(self, q_function, result_limit = 1000, contains= False, trash=False):

        page_token = None
        self.file_list = []
        while True: #has to loop through pages to get all the results
            response = self.service.files().list(
                q=q_function,
                spaces='drive',
                fields='nextPageToken, files(id, name, mimeType, trashed, parents)',
                pageToken=page_token).execute()
            for file in response.get('files', []):
                f = Drive_object(file)
                if trash or not f.trashed:
                    self.file_list.append(f)

            page_token = response.get('nextPageToken', None)
            if page_token is None:
                break;
            else:
                print ("found: %s files" % len(self.file_list))
            if len(self.file_list) > result_limit:
                print ("file limit reached")
                break;

        print ("files found: %s" % len(self.file_list))
        return self.file_list

    def list_dir(self, id):
        return self.search("'%s' in parents" % id)

    @staticmethod
    def as_string(objects):
        string = ""
        for i in objects:
            string += "%s\n" % i.as_string()
        return string
    

if __name__ == '__main__':
    g = Drive()
    root =  g.get_root() 

    result = g.list_dir(root)
    print(Drive.as_string(result))

    #import pprint
    #pp = pprint.PrettyPrinter(indent=4)
    #pp.pprint( result ) 

