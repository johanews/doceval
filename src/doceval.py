import os
import ast
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
                files.append(os.path.join(dirpath, file))
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
    evaluate(files, "CLASS", ast.ClassDef, queue)


def fun_eval(files, queue):
    """
    Scan each file from the input list, searching for
    undocumented functions.
    :param files: the list of files
    :param queue: the queue for storing the result
    """
    evaluate(files, "FUNCTION/METHOD", ast.FunctionDef, queue)


def evaluate(files, name, astdef, queue):
    """
    Scan each file from the input list, searching for
    nodes defined by the node argument. Nodes missing
    documentation are stored in a dict which is added
    to the shared result queue at the very end.
    :param files: the list of files
    :param name: the node type as a string
    :param astdef: the ast node definition
    :param queue: the queue for storing the result
    """
    check_doc = False
    preceding = None
    und_block = {}

    undoc_count = 0
    block_count = 0

    for file in files:

        und_block[file] = []
        data = open(file).read()
        tree = ast.parse(data)

        for node in ast.walk(tree):

            if check_doc:
                docs = ast.get_docstring(preceding)
                if docs is None:
                    fun = (preceding.name, preceding.lineno)
                    und_block[file].append(fun)
                    undoc_count += 1

            if isinstance(node, astdef):
                block_count += 1
                preceding = node
                check_doc = True
            else:
                check_doc = False

        und_block[file].sort(key=lambda tup: tup[1])

        if not bool(und_block[file]):
            del und_block[file]

    coverage = coverage_calc(undoc_count, block_count)
    queue.put((name, coverage, und_block))


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
