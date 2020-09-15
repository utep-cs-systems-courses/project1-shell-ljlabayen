#! /usr/bin/env python3

import sys, os, re

def main():
 while 1:
     cmd = input('$ ')
     args = cmd.split()
     if 'exit' in cmd:
        exit(1)
     elif  'help' in cmd:
        os.write(1, ("HELP SECTION\n").encode())
     elif 'cd' in cmd:
         if '..' in args[1]:
             os.chdir('..')
             os.write(1, os.getcwd().encode())
         else:
             os.chdir(args[1])
             os.write(1, os.getcwd().encode())
     elif 'ls' in cmd:
         for file in os.listdir():
             print(file)
     else:
         exec_cmd(args)

def exec_cmd(args):

 pid = os.getpid()
 rc = os.fork()

 if rc < 0:
     os.write(2, ("fork failed, returning %d\n" % rc).encode())
     sys.exit(1)

 elif rc == 0:
     for dir in re.split(":", os.environ['PATH']):
         program = "%s/%s" % (dir, args[0])
         try:
             os.execve(program, args, os.environ)
         except FileNotFoundError:
             pass

     os.write(1, ("%s: Command Not Found\n" % args[0]).encode())
     sys.exit(1)

 else:
     childpid = os.wait()

if __name__ == "__main__":
 main()