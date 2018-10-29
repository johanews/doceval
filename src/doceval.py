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


def doceval(files):
    """
    Responsible for running the analysis concurrently
    by checking classes and functions in two separate
    processes.
    :param files: the list of files
    :return: a list containing the joined result from
    the separate processes.
    """
    queue = mp.Queue()

    p1 = mp.Process(target=cls_eval, args=(files, queue,))
    p2 = mp.Process(target=fun_eval, args=(files, queue,))

    p1.start()
    p2.start()

    results = [queue.get() for _ in range(2)]

    p1.join()
    p2.join()

    return results


def display(results):
    """
    Print the result in a readable manner.
    :param results: the list containing the result of
    the evaluation
    """
    print("-" * 80)
    for category in results:
        for file, funcs in category.items():
            print("FILE: \t %s \n" % file)
            for fun, i in funcs.items():
                print("%d: \t %s" % (i, fun))
    print("-" * 80)


def cls_eval(files, queue):
    """
    Scan each file from the input list, searching for
    undocumented classes.

    :param files: the list of files
    :param queue: the queue for storing the result
    """
    regex = r'class\s(\w+\([\w.]*\)):'
    evaluate(files, regex, queue)


def fun_eval(files, queue):
    """
    Scan each file from the input list, searching for
    undocumented methods.

    :param files: the list of files
    :param queue: the queue for storing the result
    """
    regex = r'def\s(\w+\(\w*\)):'
    evaluate(files, regex, queue)


def evaluate(files, regex, queue):
    """
    Scan each file from the input list, searching for
    undocumented code-blocks of the type specified by
    the regex argument. The relevant code-blocks (and
    their corresponding line numbers) are stored in a
    dict that is added to that shared result queue at
    the very end.

    :param files: the list of files
    :param regex: the regex
    :param queue: the queue for storing the result
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

    queue.put(undoc_blk)


def main():
    path = os.getcwd()
    assert os.path.isdir(path)
    files = scan_dir(path)
    result = doceval(files)
    display(result)


if __name__ == "__main__":
    main()
