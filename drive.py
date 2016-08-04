from __future__ import print_function
from drive_object import File_object
from local import Local

import httplib2
import io, os
from apiclient import discovery, http
import oauth2client
from oauth2client import client
from oauth2client import tools

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# rm ~/.credentials/drive-python-quickstart.json

SCOPES = 'https://www.googleapis.com/auth/drive'                    #Full, permissive scope to access all of a user's files. Request this scope only when it is strictly necessary.
#SCOPES = 'https://www.googleapis.com/auth/drive.readonly'           #Allows read-only access to file metadata and file content
#SCOPES = 'https://www.googleapis.com/auth/drive.appfolder'          #Allows access to the Application Data folder
#SCOPES = 'https://www.googleapis.com/auth/drive.file'               #Per-file access to files created or opened by the app
#SCOPES = 'https://www.googleapis.com/auth/drive.install'            #Special scope used to let users approve installation of an app.
#SCOPES = 'https://www.googleapis.com/auth/drive.metadata'           #Allows read-write access to file metadata, but does not allow any access to read, download, write or upload file content. Does not support file creation, trashing or deletion. Also does not allow changing folders or sharing in order to prevent access escalation.
#SCOPES = 'https://www.googleapis.com/auth/drive.metadata.readonly'  #Allows read-only access to file metadata, but does not allow any access to read or download file content
#SCOPES = 'https://www.googleapis.com/auth/drive.photos.readonly'    #Allows read-only access to all photos. The spaces parameter must be set to photos.
#SCOPES = 'https://www.googleapis.com/auth/drive.scripts'            #Allows access to Apps Script files

CLIENT_SECRET_FILE = 'client_id.json'
APPLICATION_NAME = 'Drive cli backup using API Python'
LOCAL_BACKUP_DIRECTORY = "../gdrive"
DRIVE_ROOT_DIR = "00 GDRIVE_NEW" #the drive directory we will synconsize

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

        self.local=Local(LOCAL_BACKUP_DIRECTORY)

        self.check_interrupt = False
        self.check_ready = True
        self.check_counters = []

        self.sync_queue = []
        self.check_prioity_depth = 1 #the depth to check for files before procuessing the sync queue

    """ 
        functions using the google drive API 
    """

    def get_credentials(self):

        if not os.path.exists(CLIENT_SECRET_FILE):
            print("the credentials file is missing. follow the tutorial in the readme so you know what to do")
            exit()
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


    #search file by name
    def search(self, q_function, result_limit = 1000, contains= False, trash=False):

        page_token = None
        self.file_list = []
        while True: #has to loop through pages to get all the results
            result_list = self.service.files().list(
                q=q_function,
                spaces='drive',
                fields='nextPageToken, files(id, name, mimeType, trashed, parents)',
                pageToken=page_token)
            #print("result list: %s" % result_list)
            response = result_list.execute()
            for file in response.get('files', []):
                f = File_object(self,file)
                if trash or not f.trashed:
                    self.file_list.append(f)

            page_token = response.get('nextPageToken', None)
            if page_token is None:
                break
            else:
                pass
                #print ("found: %s files" % len(self.file_list))
            if len(self.file_list) > result_limit:
                print ("file limit reached")
                break

        #print ("files found: %s" % len(self.file_list))
        return self.file_list

    #the plan here it to make an interupperable downloader
    class downloader():
        def __init__(self, service, file_id, export = None):
            if export is None:
	        self.request = service.files().get_media(fileId=file_id)
            else:
                self.request = service.files().export_media(fileId=file_id, mimeType=export)

	    self.done = True

        def start(self, file_handle = None, first_process = True):
            if file_handle is None: 
                self.file_handle = io.BytesIO()
            else:
	        self.file_handle = file_handle

	    self.downloader = http.MediaIoBaseDownload(self.file_handle, self.request)
	    self.done = False
	    self.status = None

            print("starting download")
            if first_process: self.process()

        #needs to be called on a while loop in order to pull big files
        def process(self):
    	    self.status, self.done = self.downloader.next_chunk()
    	    print("Download %d%%." % int(self.status.progress() * 100))

    def download(self, *args, **kargs):
        return self.downloader(self.service, *args, **kargs)

    #def download(self, file_id):
    #    request = self.service.files().get_media(fileId=file_id)
    #    fh = io.BytesIO()
    #    downloader = http.MediaIoBaseDownload(fh, request)
    #    done = False
    #    while done is False:
    #		status, done = downloader.next_chunk()
    #		print("Download %d%%." % int(status.progress() * 100))

    #def export(self, file_id, mimeType):
    #    request = self.service.files().export_media(fileId=file_id, mimeType=mimeType)
    #    fh = io.BytesIO()
    #    downloader = http.MediaIoBaseDownload(fh, request)
    #    done = False
    #    while done is False:
    #        status, done = downloader.next_chunk()
    #        print("Download %d%%." % int(status.progress() * 100))


    """ 
        api wrappers

        these call the above fuctions and do not use the api directly
    """
    
    """
        wait for ready is used in threading. It stops multiple threaded callsed to the drive api
    """
    def wait_for_ready(self):

        if self.check_ready: return

        print("stoppping background check")
        self.check_interrupt = True

        counter = 0
        while not self.check_ready:
            counter += 1
        if counter:
            print('wait counter: %s' % counter)

        self.check_interrupt = False
        #self.check_ready = True # redundant


    #gets the root of the tree to be replicated
    def get_root(self, name=None):
        results = self.search_name(DRIVE_ROOT_DIR)
        self.root = results[0]
        self.root.set_parent(None) # needed for local lookup
        return self.root

    def search_name(self, name, contains= False, **kargs):
        #resolve wild cards
        if contains: contains = ' contains '
        else: contains = "="

        return self.search( "name%s'%s'" % (contains, name), **kargs)


    def ls(self, obj, *args, **kargs):
        if obj.folder:
            results = self.search("'%s' in parents" % obj.id)
            results.sort(key=lambda x: (not x.folder,x.name), reverse=False)
            for i in results:
                i.set_parent(obj)
                i.check_local()
            return results
        else:
            return None 

    def __str__(self):
        return self.as_string()

    def process_sync_queue(self):
        while not self.check_interrupt and self.sync_queue:
            pwd = self.sync_queue.pop(0)
            pwd.sync()

    def check(self, directory, depth = None, force = False, silent = True, pull=False, dirs_only=False):
        self.check_ready = False
        objects = [directory,]
        object_pointer = 0

        #quick object for counting files
        class counter():
            def __init__(self, depth):
                self.depth = depth
                self.folders = 0
                self.new_folders = 0
                self.new = 0
                self.files = 0
                self.same = 0 #TODO report changed files
                self.different = 0

        self.check_counters = [ counter(0) ]

        while not self.check_interrupt and object_pointer < len(objects):

            pwd = objects[object_pointer]
            #print(pwd)

            if pwd == directory:
                pwd.check_depth = 0
            else:
                pwd.check_depth = pwd.parent.check_depth + 1

            if depth and pwd.check_depth > depth: break

            if pwd.check_depth > self.check_prioity_depth and self.sync_queue:
                self.process_sync_queue()
                
            #check and increase list sizes
            if len(self.check_counters) < pwd.check_depth:
                self.check_counters.append(counter(depth = pwd.check_depth)) 

            if pwd.folder:
                self.check_counters[pwd.check_depth-1].folders += 1
                if not pwd.check_local():
                    self.check_counters[pwd.check_depth-1].new_folders += 1
                    if pull:
                        pwd.pull = True
                        self.sync_queue.append(pwd)

            else:
                self.check_counters[pwd.check_depth-1].files += 1
                if pwd.check_local():
                    self.check_counters[pwd.check_depth-1].same += 1
                else:
                    #self.check_counters[pwd.check_depth-1].different += 1
                    self.check_counters[pwd.check_depth-1].new += 1
                    if pull and not dirs_only:
                        pwd.pull = True
                        self.sync_queue.append(pwd)

            ls = pwd.ls(force = force)

            
            if ls:
                for f in ls:
                    objects.append(f)

            object_pointer+=1

        if not silent:
            print("files found at depth: %s" % self.check_counters)

        #needs to be here as well so it is processed if ALL checks have been made
        self.process_sync_queue()

        self.check_ready = True

    def as_string(self):
        string = "\n" 

        string += "Syncronisation queue has %s tasks left\n" % len(self.sync_queue)

        if self.check_ready:    string+="file check complete\n"
        else:                   string+="checking for files\n"

        if self.check_counters:
            for i,c in enumerate(self.check_counters):
                string += "depth %s: \t%s folders (%s new) \t %s files (%s exists, %s new)\n" % (
                        i, c.folders, c.new_folders, c.files, c.same, c.new)
        return string
        
        
