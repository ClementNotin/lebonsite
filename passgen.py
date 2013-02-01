# coding=utf-8
from hashlib import sha1
from secret import PWD_SALT

password=raw_input("Clear pass?")
print sha1(PWD_SALT + password).hexdigest()
