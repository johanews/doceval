import os
import re


def scan_dir(dir):
    """
    Recursively search a directory for all its python
    files.

    :param dir: the directory
    :return: a list of all the python files contained
    in this directory
    """
    assert os.path.isdir(dir)
    files = []
    for (dirpath, dirnames, filenames) in os.walk(dir):
        for file in filenames:
            if file.endswith('.py'):
                files.append(dirpath + "/" + file)
    return files


def evaluate(files):
    """
    Scan each file from the input list, searching for
    undocumented methods using regex matching.

    :param files: the list of files
    :return: a dictionary of the methods in each file
    that are not documented
    """
    check_doc = False
    preceding = ()
    undoc_fun = {}
    fun_count = 0

    fun_regex = r'def\s(\w+\(\w*\)):'
    doc_regex = r'"""'

    for file in files:
        undoc_fun[file] = {}

        for i, line in enumerate(open(file)):
            if bool(line.strip()):
                if check_doc:
                    match = re.search(doc_regex, line)
                    if not match:
                        fun = {preceding[0]: preceding[1]}
                        undoc_fun[file].update(fun)
                match = re.search(fun_regex, line)
                if match:
                    fun_count = fun_count + 1
                    preceding = (match.group(1), i + 1)
                    check_doc = True
                else:
                    check_doc = False

        if not bool(undoc_fun[file]):
            del undoc_fun[file]

    print(undoc_fun)


def main():
    path = os.getcwd()
    assert os.path.isdir(path)
    evaluate(scan_dir(path))


if __name__ == "__main__":
    main()
