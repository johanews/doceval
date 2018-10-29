import os
import re
import multiprocessing as mp


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


def cls_eval(files):
    """
    Scan each file from the input list, searching for
    undocumented classes.

    :param files: the list of files
    :return: a dict with all the undocumented classes
    in each file
    """
    regex = r'class\s(\w+\([\w.]*\)):'
    evaluate(files, regex)


def fun_eval(files):
    """
    Scan each file from the input list, searching for
    undocumented methods.

    :param files: the list of files
    :return: a dict with all the undocumented methods
    in each file
    """
    regex = r'def\s(\w+\(\w*\)):'
    evaluate(files, regex)


def evaluate(files, regex):
    """
    Scan each file from the input list, searching for
    undocumented code-blocks of the type specified by
    the regex argument.


    :param files: the list of files
    :param regex: the regex
    :return: a dict containing all the code-blocks in
    each file that are not documented
    """
    check_doc = False
    preceding = ()
    undoc_blk = {}
    blk_count = 0

    doc_regex = r'^\s*"""\n'

    for file in files:
        undoc_blk[file] = {}

        for i, line in enumerate(open(file)):
            if bool(line.strip()):
                if check_doc:
                    match = re.search(doc_regex, line)
                    if not match:
                        fun = {preceding[0]: preceding[1]}
                        undoc_blk[file].update(fun)
                match = re.search(regex, line)
                if match:
                    blk_count = blk_count + 1
                    preceding = (match.group(1), i + 1)
                    check_doc = True
                else:
                    check_doc = False

        if not bool(undoc_blk[file]):
            del undoc_blk[file]

    print(undoc_blk)


def main():
    path = os.getcwd()
    assert os.path.isdir(path)
    files = scan_dir(path)

    p1 = mp.Process(target=cls_eval, args=(files,))
    p2 = mp.Process(target=fun_eval, args=(files,))

    p1.start()
    p2.start()

    p1.join()
    p2.join()


if __name__ == "__main__":
    main()
