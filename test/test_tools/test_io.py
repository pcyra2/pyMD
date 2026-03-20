import pyMD.tools.io as io

import os


temp_dir = "./test/temp_dir"


def test_make_dir():
    assert os.path.isdir(temp_dir) == False
    io.MakeDir(temp_dir)
    assert os.path.isdir(temp_dir)
    io.MakeDir(temp_dir) # This shouldz do nothing but not fail
    io.RemoveDir(temp_dir, force=False)
    assert os.path.isdir(temp_dir) == False
    io.MakeDir(temp_dir)
    io.textDump("test", os.path.join(temp_dir, "test.txt")) # Make the directory not empty
    io.RemoveDir(temp_dir, force=False)
    assert os.path.isdir(temp_dir)
    io.RemoveDir(temp_dir, force=True)
    assert os.path.isdir(temp_dir) == False


def test_text_io():
	test_text = f"""line0
line1
line2
line3
line4

line6
"""
	io.MakeDir(temp_dir)
	io.textDump(test_text, os.path.join(temp_dir, "test.txt"))
	assert os.path.isfile(os.path.join(temp_dir, "test.txt"))
	test_text_read = io.textRead(os.path.join(temp_dir, "test.txt"))

	assert test_text.splitlines() == test_text_read
	os.remove(os.path.join(temp_dir, "test.txt"))
	io.textDump(list(test_text.splitlines()), os.path.join(temp_dir, "test.txt"))
	test_text_read = io.textRead(os.path.join(temp_dir, "test.txt"))
	
	assert test_text.splitlines() == test_text_read
	io.RemoveDir(temp_dir, force=True)

def test_dict_io():
	test_dict = dict(data1 = [0, 1], data2 = {"a": 3}, data3 = {4:5})

	io.MakeDir(temp_dir)
	io.jsonDump(test_dict, os.path.join(temp_dir, "Test.json"))
	assert os.path.isfile(os.path.join(temp_dir, "Test.json"))
	test_dict_read = io.jsonRead(os.path.join(temp_dir, "Test.json"))
    
	assert test_dict == test_dict_read
	io.RemoveDir(temp_dir, force=True)
