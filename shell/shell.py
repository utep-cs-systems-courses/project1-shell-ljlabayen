#! /usr/bin/env python3

import sys, os, re

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
    args.remove(args[i + 1])
    args.remove('>')
    exec_redir(args)

def input_redir(args):
    i = args.index('<')
    os.close(0)
    os.open(args[i + 1], os.O_RDONLY); # open file for read
    os.set_inheritable(0, True)
    args.remove(args[i + 1])
    args.remove('<')
    exec_redir(args)

def exec_redir(args):
    for dir in re.split(":", os.environ["PATH"]):  # try each directory in the path
        program = "%s/%s" % (dir, args[0])
        try:
            os.execve(program, args, os.environ)  # try to exec program
        except FileNotFoundError:  # ...expected
            pass  # ...fail quietly

def pipe_cmd(args):
    left = args[0:args.index("|")]
    right = args[args.index("|") + 1:]

    pr, pw = os.pipe()
    rc = os.fork()

    if rc < 0:
        os.write(2, ("fork failed, returning %d\n" % rc).encode())
        sys.exit(1)
    elif rc == 0:
        os.close(1)
        os.dup(pw)
        os.set_inheritable(1, True)
        for fd in (pr, pw):
            os.close(fd)
        exec_cmd(left)
        os.write(2, ("Could not execute").encode())
        sys.exit(1)
    else:
        os.close(0)
        os.dup(pr)
        os.set_inheritable(0, True)
        for fd in (pw, pr):
            os.close(fd)
        if "|" in right:
            pipe_cmd(right)
        exec_cmd(right)
        os.write(2, ("Could not execute").encode())
        sys.exit(1)

def commands(command):
    if command[0] == 'exit':
        sys.exit()

    elif command[0] == 'cd':
        try:
            if len(command) == 2:
                os.chdir(command[1])
        except FileNotFoundError:
            os.write(2, ("The directory " + command[1] + " does not exist.").encode())
        except:
            os.write(2, ("Please enter a valid directory").encode())

    elif "|" in command:
        pipe_cmd(command)
        pass
    else:
        pid = os.getpid()
        rc = os.fork()

        if rc < 0:
            os.write(2, ("fork failed, returning %d\n" % rc).encode())
            sys.exit(1)
        elif rc == 0:  # child
            exec_cmd(command)
            sys.exit(0)
        else:  # parent (forked ok)
            if "&" not in command:
                val = os.wait()
                if val[1] != 0 and val[1] != 256:
                    os.write(1, ("Program terminated with exit code: %d\n" % val[1]).encode())

def main():
    while 1:
         prompt = '$ '
         if 'PS1' in os.environ:
             prompt = os.environ['PS1']

         os.write(1, prompt.encode())
         args = os.read(0, 10000)

         if len(args) == 0:
             break
         args = args.decode().split("\n") # separate commands
         if not args:
             continue
         for arg in args:
             commands(arg.split())

if __name__ == "__main__":
 main()