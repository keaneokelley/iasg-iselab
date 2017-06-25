#!/usr/bin/env python3
import getpass

import logging

import datetime
from peewee import DoesNotExist

from models import User, db_init
from utils import create_user

WELCOME_MESSAGE = """### Welcome to the IASG ISELab!!! ###
For assistance, join the #iselab channel on https://iasg.slack.com.

Enter your ISU netID to get started.
"""


def main():
    logging.basicConfig(filename='iasg.log', level=logging.INFO)
    db_init()
    print(WELCOME_MESSAGE)
    username = input("Username: ")
    user = None
    try:
        user = User.get(netid=username)
    except DoesNotExist:
        logging.info("Username {} didn't exist, creating new user.".format(username))
        attempts = 0
        while not user:
            if attempts == 3:
                print("Sorry.")
                logging.warning("Disconnecting {} after 3 failed attempts.".format(username))
                raise SystemExit
            user = create_user(username)
            if user:
                print("Account created successfully! Please connect again with your new credentials.")
                raise SystemExit
            else:
                print("Username didn't work, try again?")
                username = input("Username: ")
                attempts += 1
    logging.info("User {} exists".format(username))
    if user.locked:
        logging.info("Locked account {} tried to login".format(username))
        print("Your account is locked! Please request help in the #iselab channel on https://iasg.slack.com.")
        raise SystemExit
    attempts = 0
    auth = False
    while not auth:
        password = getpass.getpass()
        auth = user.verify_password(password)
        attempts += 1
        if attempts == 3:
            user.locked = True
            logging.warning("Locked account {} after 3 failed attempts".format(username))
            print("Sorry, you're locked out. Please request help in the #iselab channel on https://iasg.slack.com.")
            raise SystemExit
    user.last_login = datetime.datetime.now()
    print("Everything work well!")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print()
        print("Exiting...")
        raise SystemExit
