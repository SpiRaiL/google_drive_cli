"""
    Google drive python cli
    initial instrucitons from
    https://developers.google.com/drive/v3/web/quickstart/python

    classes:
    
        File_object - handler for a file both on drive and on local
        Drive - handler for the connection to google drive
        Local - handler for the connection to local files
"""

from drive import Drive

import thread
import traceback
import sys

class CLI():
    def __init__(self, drive):
        self.options = {
            '':         [self.do_nothing,       ''], 
            'q':        [self.end_run,          ''],
            'exit':     [self.end_run,          'quit the cli'],
            'pwd':      [self.show_pwd,         'print the working directory'],
            'ls':       [self.show_ls,          'list the file in this dir'], 
            'cd':       [self.change_dir,       '[search option] change directory'], 
            'details':  [self.details,          '[search option] print the file details'], 
            'check':    [self.background_check, 'Recursivly check for new files'],
            'pull':     [self.background_pull,  'Recursivly download new files'],
            'report':   [self.report,           'report on background check and download'],
            'log':      [self.log,              'print check and pull log'],
            'help':     [self.help,             'print this list'],
                }

        self.auto_check = True
        self.prompt = " H> " 
        self.drive = drive
        self.root =  g.get_root() 
        self.pwd =  self.root
        self.ui = []
        self.show_ls()
        print("type help to see command list")
        #self.background_check()

    def help(self):
        string = ""
        for o,v in self.options.iteritems():
            text = v[1]
            if o:
                string += "\t" 
                if not text:
                    string += ("%s, " % o)
                else:
                    string += "%s :\t%s\n" % (o,text)
        print (string)

    def report(self):
        failed = "failed" in self.ui 
        print(self.drive.as_string(failed))

    def do_nothing(self):
        pass

    def log(self):
        last = None
        for i in self.ui:
            if isinstance(i,int): last = i
        self.drive.print_log(last = last)
        self.drive.echo(True)

    def echo_on(self):
        self.drive.echo(True)

    def background_pull(self):
        dirs = ("dirs" in self.ui) or ("directories" in self.ui)
        after = "after" in self.ui 
        self.background_check(pull=True, dirs_only = dirs, )
        self.drive.echo(True)

    """
        runs check on the drive as a seperate thread that that builds up the file structure in the back ground
    """
    def background_check(self, stop = None, depth = None, force = None, pull=False, dirs_only=False):
        if depth is None:
            for i in self.ui:
                if isinstance(i,int): depth = i

        if stop is None: stop = "stop" in self.ui 
        if force is None: force = "force" in self.ui 

        if "auto_off" in self.ui: self.auto_check = False
        if "auto_on" in self.ui: self.auto_check = True

        def threadded_check():
            try:
                self.drive.check( self.pwd, depth = depth, pull=pull,dirs_only=dirs_only)
            except KeyboardInterrupt: #abort with contorl C
                pass
            except Exception, err:
                exc_info = sys.exc_info()
                traceback.print_exception(*exc_info)

            self.drive.check_ready = True

        self.drive.wait_for_ready()

        if not stop and self.auto_check:
            print("starting background check")
            thread.start_new_thread(threadded_check, ())


    def details(self):
        self.background_check(stop=True)
        f = self.select_file()
        if f: print(f.as_string(details = True))
        self.background_check()

    def change_dir(self):
        self.background_check(stop=True)

        new_dir =  self.select_file() 
        if new_dir is not None: 
            self.pwd = new_dir
            print("changing to: %s" % self.pwd)
            self.show_ls(tab=1,new_line = 1)
        else:
            print("no dir matched")

        self.background_check()

    def select_file(self):

        if len(self.ui) < 2: return None
        else: next_dir = "%s" % self.ui[1]

        if "/" in next_dir: return self.root

        if ".." in next_dir:
            if self.pwd.parent is None: print("no parent")
            return self.pwd.parent

        if next_dir[0] == '.':
            return self.pwd

        ls = self.pwd.ls()
        
        if ls is None: 
            print("No sub files or folders")
            return None

        for i in ls:
            if next_dir.lower() in i.name.lower():
                #print("found %s (matched %s)"  % (i.name,next_dir))
                return i

        return None


    def show_ls(self, tab=1, *args, **kargs):
        force = "force" in self.ui
        self.background_check(stop=True)
        print(self.pwd.ls_string(force = force, tab = tab, *args, **kargs))

    def show_pwd(self):
        print("%s" % self.pwd.pwd_string())

    def end_run(self):
        self.end = True
        
    def run(self):
        self.end = False
        while not self.end :
            self.ui = raw_input(self.prompt).split()
            self.drive.echo(False)

            if not self.ui: continue

            # make ints out of int arguements
            if self.ui[0] != "cd":
                for i,v in enumerate(self.ui):
                    try:
                        self.ui[i] = int(v)
                    except:
                        pass

            #print(self.ui)

            try:
                #get function by name, then pull out first element in the self.options. 
                #This is where the function is
                function = self.options[self.ui[0]][0]
            except:
                print("command unknown")
                function = None

            if function: function()

if __name__ == '__main__':
    g = Drive()
    c = CLI(g)
#    c.show_pwd()
    c.run()
