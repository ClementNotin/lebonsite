# coding=utf-8
from hashlib import sha1
from secret import PWD_SALT


def hash(password):
    return sha1(PWD_SALT + password).hexdigest()


if __name__ == "__main__":
    password = raw_input("Clear pass?")
    print hash(password)
