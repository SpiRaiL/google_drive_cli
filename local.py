import os
"""
    The class that sepecifies what happens on the local side
    its currently one object for the entire project. should probably be one for every file. 
"""
class Local():
    def __init__(self, root):
        self.root = root

    #get the local path of a file or dir object
    def get_path(self, obj):
        if not obj.parent:
            directory = "%s/" % (self.root)
        else:
            directory = "%s/" % (obj.parent.local_path)

        path = "%s%s" % (directory,obj.name.replace("/", "%2F") )
        return (directory, path)

    #returns true if the local path exists
    def exists(self, obj):
        #if "/" in obj.name:
        #    print("warning: some 'person' has put a forward slash in a name!\t dir: %s file: %s" % (obj.path, obj.name))
        #    return True #TODO we need to handle this becuse right now it cannot be downloaded
        d,p = self.get_path(obj)
        return (obj.path and os.path.exists(p))

    def mkdir(self, obj):
        d,p = self.get_path(obj)
        if obj.path: 
            os.mkdir(p)

    def create_file(self, obj):
        d,p = self.get_path(obj)
        return open(p + '.incomplete_download','w') #TODO interuptable return open(p + '.download','w')
