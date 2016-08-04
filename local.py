import os
"""
    The class that sepecifies what happens on the local side
"""
class Local():
    def __init__(self, root):
        self.root = root

    #get the local path of a file or dir object
    def get_path(self, obj):
        directory = "%s%s" % (self.root,obj.path)
        path = "%s%s" % (directory,obj.name)
        return (directory, path)

    #returns true if the local path exists
    def exists(self, obj):
        if "/" in obj.name:
            print("warning: some 'person' has put a forward slash in a name!\t dir: %s file: %s" % (obj.path, obj.name))
        d,p = self.get_path(obj)
        return (obj.path and os.path.exists(p))

    def mkdir(self, obj):
        d,p = self.get_path(obj)
        if obj.path: 
            os.mkdir(p)

