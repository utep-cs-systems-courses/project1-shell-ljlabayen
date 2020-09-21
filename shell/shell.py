#! /usr/bin/env python3

import sys, os, re

def exec_cmd(args):
    if '>' in args:
        output_redir(args)
    elif '<' in args:
        input_redir(args)

    elif "/" in args[0]:
        try:
            os.execve(args[0], args, os.environ)
        except FileNotFoundError:
            pass

    else:
        for dir in re.split(":", os.environ["PATH"]):
            program = "%s/%s" % (dir, args[0])
            try:
                os.execve(program, args, os.environ)
            except FileNotFoundError:
                pass

    os.write(2, ("command %s not found \n" % (args[0])).encode())
    sys.exit(1)


def output_redir(args):
    i = args.index('>')
    os.close(1)  # close fd1
    os.open(args[i+1], os.O_CREAT | os.O_WRONLY) # open file for write
    os.set_inheritable(1, True)
    args.remove(args[i + 1])
    args.remove('>')
    exec_redir(args)

def input_redir(args):
    i = args.index('<')
    os.close(0) # close fd0
    os.open(args[i + 1], os.O_RDONLY) # open file for read
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

def commands(args):
    if args[0].lower == "exit":
        sys.exit()

    elif args[0] == "cd":
        try:
            if len(args) == 2:
                os.chdir(args[1])
        except FileNotFoundError:
            os.write(2, ("The directory " + args[1] + " does not exist.").encode())
        except:
            os.write(2, ("Invalid directory").encode())

    elif "|" in args:
        pipe_cmd(args)
        pass
    else:
        pid = os.getpid()
        rc = os.fork()
        wait = True

        if "&" in args:
            args.remove("&")
            wait = False
        if rc < 0:
            os.write(2, ("fork failed, returning %d\n" % rc).encode())
            sys.exit(1)
        elif rc == 0:
            exec_cmd(args)
            sys.exit(0)
        else:
            if wait:
                result = os.wait()
                if result[1] != 0 and result[1] != 256:
                    os.write(2, ("Program terminated with exit code: %d\n" % result[1]).encode())

def main():
    while 1:
         prompt = '$ '
         if 'PS1' in os.environ:
             prompt = os.environ['PS1']

         os.write(1, prompt.encode())
         input = os.read(0, 10000)

         lines = re.split(b"\n", input) # separate commands on new line

         if lines:
             for line in lines:
                line = line.decode()
                if len(line.split()) > 0:
                    commands(line.split())
         break

if __name__ == "__main__":
 main()