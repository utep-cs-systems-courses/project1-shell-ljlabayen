#! /usr/bin/env python3

import sys, os, re

def main():
    while 1:
         prompt = '$ '
         if 'PS1' in os.environ:
             prompt = os.environ['PS1']

         cmd = input(prompt)

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
         elif '>' in cmd:
             output_redir(cmd)
         elif '<' in cmd:
             input_redir(cmd)
         elif '|' in cmd:
             pipe_cmd(cmd)
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

     os.write(1, ("%s: Command Not Found!\n" % args[0]).encode())
     sys.exit(1)

    else:
     childpid = os.wait()
def output_redir(args):
    i = args.index('>')
    os.close(1)  # close fd1
    os.open(args[i+1], os.O_CREAT | os.O_WRONLY); # open file for write
    os.set_inheritable(1, True)
    exec_cmd(args[0:i])

def input_redir(args):
    i = args.index('<')
    os.close(0)
    os.open(args[i + 1], os.O_RDONLY);
    os.set_inheritable(0, True)
    exec_cmd(args[0:i])

def pipe_cmd(args):
    r, w = os.pipe()
    for fd in (r, w):
        os.set_inheritable(fd, True)

    commands = [i.strip() for i in re.split('[\x7c]', args)]

    rc = os.fork()

    if rc < 0:  # fork failed
        os.write(2, ("fork failed, returning %d\n" % rc).encode())
        sys.exit(1)

    if rc == 0:  # child
        os.close(1)  # close stdout
        os.dup(w)
        os.set_inheritable(1, True)
        for fd in (r, w):
            os.close(fd)
        exec_cmd(commands[0].split())
    else:
        os.close(0)  # close stdin
        os.dup(r)
        os.set_inheritable(0, True)
        for fd in (w, r):
            os.close(fd)
        exec_cmd(commands[1].split())

if __name__ == "__main__":
 main()