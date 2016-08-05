
direct_mime_types = [
#Documents   
    'text/html', # HTML    
    'text/plain', # Plain text  
    'application/rtf', # Rich text   
    'application/pdf', # PDF  
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document', # MS Word document    
#Spreadsheets    
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', # MS Excel    
    'application/x-vnd.oasis.opendocument.spreadsheet', # Open Office sheet   
    'application/pdf', # PDF  
    'CSV (first sheet only)  text/csv', # 
#Drawings    
    'image/jpeg', # JPEG    
    'image/png', # PNG  
    'image/svg+xml', # SVG  
    'application/pdf', # PDF  
#Presentations
    'application/vnd.openxmlformats-officedocument.presentationml.presentation', # MS PowerPoint   
    'application/pdf', # PDF  
    'text/plain', # Plain text  
#Apps Scripts    
    'application/vnd.google-apps.script+json', # JSON    
    ]

mimetype_map = { 
        'application/vnd.google-apps.audio' :       None, #
        'application/vnd.google-apps.document' :    
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document', #    Google Docs to ms word
        'application/vnd.google-apps.drawing' :     'image/svg+xml', # Google Drawing to SVG 
        'application/vnd.google-apps.file' :        None, #    Google Drive file
        'application/vnd.google-apps.folder' :      None, #  Google Drive folder
        'application/vnd.google-apps.form' :        None, #    Google Forms
        'application/vnd.google-apps.fusiontable' : None, # Google Fusion Tables
        'application/vnd.google-apps.map Google' :  None, # My Maps
        'application/vnd.google-apps.photo' :       'image/png', #photo to png
        'application/vnd.google-apps.presentation' :
            'application/vnd.openxmlformats-officedocument.presentationml.presentation', #    Google Slides to MS PowerPoint 
        'application/vnd.google-apps.script' :      None, #  Google Apps Scripts
        'application/vnd.google-apps.sites' :       None, #   Google Sites
        'application/vnd.google-apps.spreadsheet' : 
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', # Google Sheets to MS spreadsheet
            
        'application/vnd.google-apps.unknown' :     None, # 
        'application/vnd.google-apps.video' :       None, #   
        }

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
        self.children = None

        #resolved path in the file tree
        self.dir = "" 
        self.path = "" 
        self.local_dir = "" 
        self.local_path = "" 

        self.pull = False
        self.push = False
        self.file_handle = None
        self.downloader = None
        self.error = None

    #ls wrapper so ls can be called on an oject and its children will be returned
    def ls(self, force = False, *args, **kargs):
        if not self.children or force:
            self.children = self.drive.ls(self,*args, **kargs)
        return self.children

    def ls_string(self, *args, **kargs):
        ls = self.ls(*args, **kargs)
        if not ls: return "Folder is empty"
        string = ""
        for i in ls:
            string += "%s\n" % (i.as_string(*args,**kargs))

        return string

    def pwd_string(self):
        if not self.parent: return "/"
        return self.parent.path

    def __str__(self):
        return self.as_string()
        
    def as_string(self, tab = 0, details=False, json=False, *args, **kargs):
        string = ""
        if json: string += "%s\t " % self.json
        if details: string += "id: %s\n" % self.id
        if details: string += "mimeType: %s\n" % self.mimeType
        #if details: string += "trashed %s\n" % self.trashed
        if details: string += "parent: %s\n" % self.parent
        if details: string += "parents: %s\n" % self.parents
        if details: string += "path: %s\n" % self.path
        if details: string += "local_path:%s\n" % self.local_path
        if details: string += "local_dir: %s\n" % self.local_dir
        if self.folder: string += "D " 
        else: string += "\t" 
        if not self.check_local(): string += "N "
        string += "\t"*tab
        string += "%s\t " % self.name
        if details and self.error: string += "erorr: %s\n" % self.error

        #string += "%s\t " % self.local_path
        return string

    # sets the parent oject that caled LS to this object in order to build up a folder structure
    def set_parent(self, parent):
        self.parent = parent
        if not parent: self.dir = "/"
        else: self.dir = parent.path + "/"

        self.path = self.dir + self.name

        self.local_dir, self.local_path  = self.local.get_path(self)

    # check if the local file exists
    def check_local(self):
        return self.local.exists(self)

    #pull the file down from the server and replace the current one
    def sync(self):
        if self.pull: self.do_pull()
        elif self.push: self.do_push()

    def do_pull(self):
        if self.folder:
            #print("adding folder: %s" % self)
            self.local.mkdir(self)
        else:
            #print("syncing file: %s" % self.as_string(details = True))
            if self.downloader is None:
                #determine if its a raw download or an export
                if self.mimeType in direct_mime_types: export_type = None
                elif self.mimeType in mimetype_map:
                    export_type = mimetype_map[self.mimeType]
                else: export_type = None

                #start a new downloader
                self.downloader = self.drive.download(self.id, export = export_type)

            self.file_handle = self.local.create_file(self)

            self.downloader.start(self.file_handle)

            #continue with / resume interupped download
            #while not self.downloader.done: self.downloader.process()
            #self.file_handle.close()

    def complete_pull(self):
        self.local.complete_file(self)



    def do_push(self):
        #TODO
        pass

