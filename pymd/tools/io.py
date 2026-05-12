"""#TODO
"""
import json
import os
import shutil
import re

def text_dump(text: list[str]|str, path: str) -> None:
    """Prints a text file, 

    Args:
        text (str|list[str]): accepts either array of text or string.
        path (str): file path to write to. 
    """
    with open(file=path, mode="w", encoding="UTF-8")as f:
        if isinstance(text, str):
            print(text, file=f, end="")
        else:
            for i in text:
                print(i, file=f)
        f.close()


def text_read(path: str)->list[str]:
    """Reads in a text file as a list of lines.

    Args:
        path (str): path to file.
    Returns:
        text (list[str]): list of lines in the file.
    """
    with open(file=path, mode="r", encoding="UTF-8") as f:
        text = f.readlines()
        f.close()
    clean = [line.replace("\n","") for line in text]
    return clean


def json_dump(data: dict, path: str,) -> None:
    """
    The function `jsonDump` takes a dictionary and a file path as input, then writes 
    the dictionary to a JSON file at the specified path.
    
    Args:
        data (dict): A dictionary containing the data that you want to dump into a JSON file.
        path (str): The `path` parameter in the `jsonDump` function is a string that 
        represents the file path where the JSON data will be dumped or saved. It should 
        be the location where you want to store the JSON data.
    """
    try:
        with open(file=path, mode="w", encoding="UTF-8") as f:
            json.dump(obj=data, fp=f, indent="\t", sort_keys=True, )
    except TypeError:
        with open(file=path, mode="w", encoding="UTF-8") as f:
            json.dump(obj=data, fp=f, indent="\t",)


def json_read(path: str)->dict:
    """
    The function `jsonRead` reads and returns the content of a JSON 
    file located at the specified path.
    
    Args:
        path (str): The `path` parameter in the `jsonRead` function is a string that represents
        the file path to the JSON file that you want to read and load.
    
    Returns:
        text (dict): The function `jsonRead` reads a JSON file located at the specified `path`
        and returns the contents of the file as a Python dictionary.
    """
    
    with open(file=path, mode="r", encoding="UTF-8") as f:
        text = json.load(fp=f, object_hook=parse_float_keys)
        f.close()
    return text


def parse_float_keys(dct: dict)->dict:
    """Enables float keys in json files by converting them from strings.


    Args:
        dct (dict): Dictionary to parse

    Returns:
        rval (float|str): Dictionary with float keys where possible.
    """
    rval = dict()
    for key, val in dct.items():
        try:
            # Convert the key to an integer/float
            int_key = float(key)
            # Assign value to the integer key in the new dict
            rval[int_key] = val
        except ValueError:
            # Couldn't convert key to an integer; Use original key
            rval[key] = val
    return rval


def make_dir(path: str) -> None:
    """Makes directory in path if it doesn't already exist

    Args:
        path (str): Path to directory. 
    """
    print(f"INFO: Generating {path}")
    try:
        os.mkdir(path=path)
    except FileExistsError:
        print(f"INFO: {path} already exists")

def remove_dir(path: str, force: bool = True) -> None:
    """Removes directory in path if it exists, irrespective of contents.
    
    Args:
        path (str): Directory path
        force (bool, optional): Whether to forcibly remove a directory if it is not empty. Defaults to True
    """
    if os.path.isdir(s=path):
        if force is False:
            try:
                os.removedirs(name=path)
            except OSError:
                print(f"WARNING: {path} is not empty")
        else:
            shutil.rmtree(path=path)

def grep(file: str, string: str, strip: bool = False) -> list[str]:
    """
    a function that should act like the bash 'grep' command.

    Args:
        file (str): File to grep.
        string (str): Pattern to grep.
        strip (bool): Whether to strip the grep lines from the original file working like `grep -v`

    Returns:
        lines (list[str]): Lines containing grep pattern.
        contents (list[str]): Lines that do not contain grep pattern if strip == True.
    """
    contents = text_read(path=file)
    regexp = re.compile(pattern=string)
    lines = []
    for line in contents:
        if re.search(pattern=regexp, string=line):
            print(line)
            lines.append(line)
            if strip:
                contents.remove(line)
    return lines, contents

