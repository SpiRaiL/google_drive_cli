
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
        self.path = "" 
        self.local_dir = "" 
        self.local_path = "" 

        self.pull = False
        self.push = False

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
        return self.path + self.name

    def __str__(self):
        return self.as_string()
        
    def as_string(self, tab = 0, details=False, json=False, *args, **kargs):
        string = ""
        if json: string += "%s\t " % self.json
        if details: string += "%s\t " % self.id
        if details: string += "%s\t " % self.mimeType
        if details: string += "%s\t " % self.trashed
        if details: string += "%s\t " % self.parents
        if self.folder: string += "D " 
        else: string += "\t" 
        if not self.check_local(): string += "N "
        string += "\t"*tab
        string += "%s\t " % self.name

        #string += "%s\t " % self.local_path
        return string

    # sets the parent oject that caled LS to this object in order to build up a folder structure
    def set_parent(self, parent):
        self.parent = parent
        self.path += parent.path + parent.name + "/"
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
            print("adding folder: %s" % self)
            self.local.mkdir(self)
        else:
            print("syncing file: %s" % self)
            if not self.check_local():
                #self.drive.download(self.id)
                self.drive.export(self.id, self.mimeType)

    def do_push(self):
        #TODO
        pass

