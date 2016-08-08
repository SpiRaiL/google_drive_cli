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

        if obj.local_extension:
            path += "." + obj.local_extension

        return (directory, path)

    #returns true if the local path exists
    def exists(self, obj):
        d,p = self.get_path(obj)
        return (obj.path and os.path.exists(p))

    def mkdir(self, obj):
        d,p = self.get_path(obj)
        if obj.path: 
            os.mkdir(p)

    def create_file(self, obj):
        d,p = self.get_path(obj)
        return open(p + '.incomplete_download','w') 

    def complete_file(self, obj):
        d,p = self.get_path(obj)
        os.rename(p + '.incomplete_download', p)
