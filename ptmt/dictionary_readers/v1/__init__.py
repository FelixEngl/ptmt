from os import path

import ptmt.dictionary_readers.v1.buildscript

lark_dir = path.join(path.dirname(__file__), 'lark')

assert path.exists(lark_dir), f"The lark directory does not exist at {lark_dir}!"
