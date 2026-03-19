import json
import os


def textDump(text:list[str]|str, path:str):
    """Prints a text file, 

    Args:
        text (str|list[str]): accepts either array of text or string.
        path (str): file path to write to. 
    """
    with open(path, "w")as f:
        if type(text) == str:
            print(text, file=f)
        else:
            for i in text:
                print(i, file=f)
        f.close()


def textRead(path:str)->list[str]:
    """Reads in a text file as a list of lines.

    Args:
        path (str): path to file.
    Returns:
        text (list[str]): list of lines in the file.
    """
    with open(path, "r") as f:
        text = f.readlines()
        f.close()
    clean = [line.replace("\n","") for line in text]
    return clean


def jsonDump(dict:dict, path:str,):
    """
    The function `jsonDump` takes a dictionary and a file path as input, then writes the dictionary to a
    JSON file at the specified path.
    
    Args:
        dict (dict): A dictionary containing the data that you want to dump into a JSON file.
        path (str): The `path` parameter in the `jsonDump` function is a string that represents the file
    path where the JSON data will be dumped or saved. It should be the location where you want to store
    the JSON data.
    """
    try:
        with open(path, "w") as f:
            json.dump(dict, f, indent="\t", sort_keys=True, )
    except TypeError:
        with open(path, "w") as f:
            json.dump(dict, f, indent="\t",)


def jsonRead(path:str)->dict:
    """
    The function `jsonRead` reads and returns the content of a JSON file located at the specified path.
    
    Args:
        path (str): The `path` parameter in the `jsonRead` function is a string that represents the file
    path to the JSON file that you want to read and load.
    
    Returns:
        text (dict): The function `jsonRead` reads a JSON file located at the specified `path` and returns the contents
    of the file as a Python dictionary.
    """
    with open(path, "r") as f:
        text = json.load(f, object_hook=parse_float_keys)
        f.close()
    return text


def parse_float_keys(dct:dict)->dict:
    """Enables float keys in json files by converting them from strings.


    Args:
        dct (dict): Dictionary to parse

    Returns:
        float|str: Dictionary with float keys where possible.
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


def MakeDir(path: str):
    """Makes directory in path if it doesn't already exist

    Args:
        path (str): Path to directory. 
    """
    print(f"INFO: Generating {path}")
    try:
        os.mkdir(path)
    except FileExistsError:
        print(f"INFO: {path} already exists")
        pass