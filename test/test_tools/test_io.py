import os

import pymd.tools.io as io

temp_dir = "./test/temp_dir"
file_loc = "./test/test_data/"

def test_make_dir():
	assert os.path.isdir(temp_dir) == False
	io.make_dir(temp_dir)
	assert os.path.isdir(temp_dir)
	io.make_dir(temp_dir) # This shouldz do nothing but not fail
	io.remove_dir(temp_dir, force=False)
	assert os.path.isdir(temp_dir) == False
	io.make_dir(temp_dir)
	io.text_dump("test", os.path.join(temp_dir, "test.txt")) # Make the directory not empty
	io.remove_dir(temp_dir, force=False)
	assert os.path.isdir(temp_dir)
	io.remove_dir(temp_dir, force=True)
	assert os.path.isdir(temp_dir) == False


def test_text_io():
	test_text = f"""line0
line1
line2
line3
line4

line6
"""
	io.make_dir(temp_dir)
	io.text_dump(test_text, os.path.join(temp_dir, "test.txt"))
	assert os.path.isfile(os.path.join(temp_dir, "test.txt"))
	test_text_read = io.text_read(os.path.join(temp_dir, "test.txt"))

	assert test_text.splitlines() == test_text_read
	os.remove(os.path.join(temp_dir, "test.txt"))
	io.text_dump(list(test_text.splitlines()), os.path.join(temp_dir, "test.txt"))
	test_text_read = io.text_read(os.path.join(temp_dir, "test.txt"))
	
	assert test_text.splitlines() == test_text_read
	io.remove_dir(temp_dir, force=True)

def test_dict_io():
	test_dict = dict(data1 = [0, 1], data2 = {"a": 3}, data3 = {4:5})

	io.make_dir(temp_dir)
	io.json_dump(test_dict, os.path.join(temp_dir, "Test.json"))
	assert os.path.isfile(os.path.join(temp_dir, "Test.json"))
	test_dict_read = io.json_read(os.path.join(temp_dir, "Test.json"))
    
	assert test_dict == test_dict_read
	io.remove_dir(temp_dir, force=True)


def test_grep():
	correct_example = io.text_read(os.path.join(file_loc, "2BN.pdb"))
	grepped = io.grep(os.path.join(file_loc, "1N23.pdb"), "2BN")
	assert grepped == correct_example