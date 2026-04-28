import os

import pymd.tools.io as io

TEMP_DIR = "./test/temp_dir"
FILE_LOC = "./test/test_data/"

def test_make_dir():
	assert os.path.isdir(TEMP_DIR) == False
	io.make_dir(TEMP_DIR)
	assert os.path.isdir(TEMP_DIR)
	io.make_dir(TEMP_DIR) # This shouldz do nothing but not fail
	io.remove_dir(TEMP_DIR, force=False)
	assert os.path.isdir(TEMP_DIR) == False
	io.make_dir(TEMP_DIR)
	io.text_dump("test", os.path.join(TEMP_DIR, "test.txt")) # Make the directory not empty
	io.remove_dir(TEMP_DIR, force=False)
	assert os.path.isdir(TEMP_DIR)
	io.remove_dir(TEMP_DIR, force=True)
	assert os.path.isdir(TEMP_DIR) == False


def test_text_io():
	test_text = f"""line0
line1
line2
line3
line4

line6
"""
	io.make_dir(TEMP_DIR)
	io.text_dump(test_text, os.path.join(TEMP_DIR, "test.txt"))
	assert os.path.isfile(os.path.join(TEMP_DIR, "test.txt"))
	test_text_read = io.text_read(os.path.join(TEMP_DIR, "test.txt"))

	assert test_text.splitlines() == test_text_read
	os.remove(os.path.join(TEMP_DIR, "test.txt"))
	io.text_dump(list(test_text.splitlines()), os.path.join(TEMP_DIR, "test.txt"))
	test_text_read = io.text_read(os.path.join(TEMP_DIR, "test.txt"))
	
	assert test_text.splitlines() == test_text_read
	io.remove_dir(TEMP_DIR, force=True)

def test_dict_io():
	test_dict = dict(data1 = [0, 1], data2 = {"a": 3}, data3 = {4:5})

	io.make_dir(TEMP_DIR)
	io.json_dump(test_dict, os.path.join(TEMP_DIR, "Test.json"))
	assert os.path.isfile(os.path.join(TEMP_DIR, "Test.json"))
	test_dict_read = io.json_read(os.path.join(TEMP_DIR, "Test.json"))
    
	assert test_dict == test_dict_read
	io.remove_dir(TEMP_DIR, force=True)


def test_grep():
	correct_example = io.text_read(os.path.join(FILE_LOC, "2BN.pdb"))
	grepped, _ = io.grep(os.path.join(FILE_LOC, "1N23.pdb"), "2BN", strip=False)
	assert grepped == correct_example