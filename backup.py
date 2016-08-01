"""
    Google drive python cli
    initial instrucitons from
    https://developers.google.com/drive/v3/web/quickstart/python

    classes:
    
        File_object - handler for a file both on drive and on local
        Drive - handler for the connection to google drive
        Local - handler for the connection to local files
"""

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
class File_object():
    def __init__(self, drive, json):
        #backwards link to the drive object
        self.drive = drive 

        #reference to local object
        if self.drive and self.drive.local: 
            self.local = self.drive.local
        else:
            self.local = None

        self.json = json
        self.id = json.get('id')
        self.name = json.get('name')

        self.mimeType = json.get('mimeType')
        self.folder = (self.mimeType == 'application/vnd.google-apps.folder')

        self.trashed = json.get('trashed')
        self.parents= json.get('parents')
        self.parent = None

        #self.check_local()

        #resolved path in the file tree
        self.path = "" 
        self.local_path = "" 

    #ls wrapper so ls can be called on an oject and its children will be returned
    def ls(self,*args, **kargs):
        return self.drive.ls(self,*args, **kargs)

    def ls_string(self, *args, **kargs):
        return self.drive.as_string(self.ls(),*args, **kargs)

    def pwd_string(self):
        return self.path + self.name

    def __str__(self):
        return self.as_string()
        
    def as_string(self, details=False, json=False):
        string = ""
        if json: string += "%s\t " % self.json
        if details: string += "%s\t " % self.id
        if details: string += "%s\t " % self.mimeType
        if details: string += "%s\t " % self.trashed
        if details: string += "%s\t " % self.parents
        if self.folder: string += "D " 
        else: string += "\t" 
        if not self.local: string += "N "
        #string += "%s\t " % self.local_path
        string += "%s\t " % self.name
        return string

    # sets the parent oject that caled LS to this object in order to build up a folder structure
    def set_parent(self, parent):
        self.parent = parent
        self.path += parent.path + parent.name + "/"
        self.local_path = "%s%s" % (self.local.root,self.path)

    # check if the local file exists
    def check_local(self):
        #if not self.path: return False
        self.local = (self.path and os.path.exists(self.local_path))
        return self.local

class Local():
    def __init__(self, root):
        self.root = root

"""
    the connection and commands to google drive
"""
class Drive():
    """Shows basic usage of the Google Drive API.

    Creates a Google Drive API service object and outputs the names and IDs
    for up to 10 files.
    """
    def __init__(self, local=None):
        credentials = self.get_credentials()
        http = credentials.authorize(httplib2.Http())
        self.service = discovery.build('drive', 'v3', http=http)

        self.local=Local(local)

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
        self.root = results[0]
        return self.root

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
                f = File_object(self,file)
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

    def ls(self, obj):
        if obj.folder:
            results = self.search("'%s' in parents" % obj.id)
            results.sort(key=lambda x: (not x.folder,x.name), reverse=False)
            #results.sort(key=lambda x: (x.folder,x.name), reverse=False)
            for i in results:
                i.set_parent(obj)
                i.check_local()
            return results
        else:
            return None 

    def __str__(self):
        return self.as_string()
        
    def as_string(self, objects = None, tab=0, new_line=0):
        if objects is None:
            objects = self.file_list

        string = "%s" % "\n"*new_line #precedeing new lines

        for i in objects:
            string += "%s%s\n" % ("\t"*tab, i.as_string())
        return string

class CLI():
    def __init__(self, drive):
        self.options = {
            'q': self.end_run,
            'exit': self.end_run,
            'pwd': self.show_pwd, 
            'ls': self.show_ls, 
            'cd': self.change_dir, 
            '': self.do_nothing, 

                }

        self.prompt = " D > " 
        self.drive = drive
        self.pwd =  g.get_root() 
        self.show_ls()

    def do_nothing(self):
        pass

    def change_dir(self):
        if ".." in self.next_dir:
            if self.pwd.parent is None:
                print("no parent")
                return
            print("changing to: %s" % self.pwd.name)
            self.pwd = self.pwd.parent
            self.show_ls(tab=1,new_line = 1)

            return

        #get the list
        ls = self.pwd.ls()
        
        if ls is None:
            print("failed to get dirs")
            

        for i in ls:
            #print("checking: %s in %s" % ( self.next_dir.lower(), i.name.lower()))
            if self.next_dir.lower() in i.name.lower():
                print("changing to %s (matched %s)"  % (i.name,self.next_dir))
                self.pwd = i

                self.show_ls(tab=1,new_line = 1)
                return

        print("no dir matched")


    def show_ls(self, *args, **kargs):
        print(self.pwd.ls_string(*args, **kargs))

    def show_pwd(self):
        print("%s" % self.pwd.pwd_string())

    def end_run(self):
        self.end = True
        
    def run(self):
        self.end = False
        while not self.end :
            ui = raw_input(self.prompt)

            if len(ui)>2 and ui[:2] == 'cd':
                self.next_dir = ui[3:]
                ui = ui[:2]

            try:
                function = self.options[ui]
            except:
                print("command unknonw")
                function = None

            if function: function()

if __name__ == '__main__':
    local = "gdrive_humans/"
    g = Drive(local = local)
    c = CLI(g)
    c.show_pwd()
    c.run()

    #result = root.ls()
    #print(Drive.as_string(result))

    #for i in result:
    #    print(i.as_string())
    #    print(Drive.as_string(i.ls(),tab=1))

