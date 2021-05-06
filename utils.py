
import os

def is_same_path(pa, pb):
    return os.path.normcase(os.path.realpath(pa)) == os.path.normcase(os.path.realpath(pb))

def is_in_path(pa, pb):
    return os.path.normcase(os.path.realpath(pa)) in os.path.normcase(os.path.realpath(pb))
