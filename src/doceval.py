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
    if os.path.isfile(dir):
        return [dir]
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
    for (b, c, category) in results:
        print("%s COVERAGE: %.1f%%" % (b, round(c * 100, 1)))
        for file, funcs in category.items():
            print("-" * 80)
            print("FILE: %s \n" % file)
            for (fun, i) in funcs:
                print("%d: %s" % (i, fun))
        print("-" * 80)


def cls_eval(files, queue):
    """
    Scan each file from the input list, searching for
    undocumented classes.
    :param files: the list of files
    :param queue: the queue for storing the result
    """
    regex = r'class\s(\w+\([\w\s.,]*\)):'
    evaluate(files, "CLASS", regex, queue)


def fun_eval(files, queue):
    """
    Scan each file from the input list, searching for
    undocumented methods.
    :param files: the list of files
    :param queue: the queue for storing the result
    """
    regex = r'def\s(\w+\(.*\)):'
    evaluate(files, "FUNCTION/METHOD", regex, queue)


def evaluate(files, block, regex, queue):
    """
    Scan each file from the input list, searching for
    undocumented code-blocks of the type specified by
    the regex argument. The relevant code-blocks (and
    their corresponding line numbers) are stored in a
    dict that is added to that shared result queue at
    the very end.
    :param files: the list of files
    :param block: the block type defined by the regex
    :param regex: the regex
    :param queue: the queue for storing the result
    """
    check_doc = False
    encircled = True
    preceding = ()      # A tuple storing the last discovered block (name and line number)
    und_block = {}      # A map storing the undocumented blocks

    undoc_count = 0
    block_count = 0

    doc_regex_1 = r'^\s*""".*""".*\n'
    doc_regex_2 = r'^\s*""".*\n'

    for file in files:
        und_block[file] = []                                        # The path of the file serves as the map key

        for i, line in enumerate(open(file)):
            if bool(line.strip()):                                  # Ignore empty lines
                if check_doc:
                    match_1 = re.search(doc_regex_1, line)
                    match_2 = re.search(doc_regex_2, line)
                    if not match_1 and not match_2 and encircled:   # If there are docs missing underneath
                        fun = (preceding[0], preceding[1])          # the preceding block, add it the list
                        und_block[file].append(fun)                 # of undocumented blocks
                        undoc_count += 1
                    if match_2:
                        encircled = not encircled
                if encircled:
                    match = re.search(regex, line)
                    if match:                                       # If a line matches the specified block type:
                        block_count += 1                            # (1) increment the block counter
                        preceding = (match.group(1), i + 1)         # (2) update the preceding variable
                        check_doc = True                            # (3) make sure the next iteration checks for docs
                    else:
                        check_doc = False

        if not bool(und_block[file]):                                      # Remove files with full coverage (they do
            del und_block[file]                                            # not contain blocks that will be printed)

    coverage = coverage_calc(undoc_count, block_count)
    queue.put((block, coverage, und_block))


def coverage_calc(undocumented, total):
    """
    Compute the global average. When the total number
    of blocks is 0, the coverage is defined to be 100
    percent.
    :param undocumented: the number of blocks missing
    documentation
    :param total: the total number of blocks
    :return: the global coverage
    """
    assert undocumented <= total
    if total == 0:
        return 1
    return 1 - (undocumented/total)


def main():
    path = input("Enter directory path: ")
    files = scan_dir(path)
    result = doceval(files)
    display(result)


if __name__ == "__main__":
    main()
