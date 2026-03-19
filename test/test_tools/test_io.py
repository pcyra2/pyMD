import pyMD.tools.io as io

import os


temp_dir = "./test/temp_dir"


def test_make_dir():
    assert os.path.isdir(temp_dir) == False
    io.MakeDir(temp_dir)
    assert os.path.isdir(temp_dir)
    io.MakeDir(temp_dir) # This should do nothing but not fail
    os.removedirs(temp_dir)