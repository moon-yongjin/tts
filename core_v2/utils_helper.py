# Utility functions helper

import os

def get_file_size(file_path):
    return os.path.getsize(file_path)

def get_file_extension(file_path):
    return os.path.splitext(file_path)[1][1:]
