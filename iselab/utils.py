import getpass
import hashlib
import logging
import os
import re
import shlex
import smtplib
from email.mime.text import MIMEText
from subprocess import run

from iselab import settings
from iselab.models import User

logger = logging.getLogger('iasg')

TERMS = "TERMS AND CONDITIONS: While ISELab is a safe environment for hacking, your activities and usage must remain " \
        "in compliance with all applicable local, state, and federal laws, as well as Iowa State university policy. " \
        "Notably, you may not use " \
        "this system to attack ISU infrastructure or others outside the environment. IASG will not be held liable for " \
        "any damages, " \
        "whether physical, virtual, imaginary, stress-related, or otherwise, that may arise from the use of these " \
        "systems. " \
        "Usage of this system may be logged and monitored for abuse. With all that in mind, it is most important that " \
        "you have fun!\n\n" \
        "By typing 'yes' below, you affirm that you have read and understood the terms and conditions."


def provision(username: str, password: str):
    try:
        run(["sudo", "useradd", username, "-s", "/bin/false", "-G", "iasg-users"])
        os.system("echo {}:{} | sudo chpasswd".format(shlex.escape(username), shlex.escape(password)))
    except Exception as e:
        logger.error("Error provisioning {}: {}".format(username, e))
        print("Warning!!! We couldn't fully set up your account. Get help in #iselab on https://iasg.slack.com.")
    else:
        logger.info("Provisioned {}".format(username))


def validate_uid(username: str) -> str:
    return re.sub(r'[^\d\w]', '', username)


def random_string(length: int = 128) -> str:
    return hashlib.sha256(os.urandom(128)).hexdigest()[:length]


# Adapted from http://stackoverflow.com/a/8321609/1974978
def send_verification_code(username):
    verify = random_string(6)
    logger.info("Sending verification to " + username)
    data = "Hello {},\nWelcome to the IASG ISELab! Your verification code is: {}".format(username, verify)
    if settings.SMTP_SERVER:
        msg = MIMEText(data)
        msg['Subject'] = "IASG ISELab Verification Code"
        msg['To'] = username + "@iastate.edu"
        msg['From'] = settings.EMAIL_FROM
        mail = smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT)
        mail.starttls()
        mail.login()
        mail.sendmail(settings.EMAIL_FROM, settings.EMAIL_TO, msg.as_string())
        mail.quit()
    else:
        print("-------------------EMAIL-------------------")
        print(data)
        print("--------------------END--------------------")
    return verify


def create_user(username: str) -> User:
    print("It looks like it's your first time using IASG ISELab!")
    print()
    verify = send_verification_code(username)
    print("Check your email. We've sent you a verification code.")
    print()
    tries = 0
    while not verify == input("Verification code: "):
        tries += 1
        if tries >= 3:
            print("Too many attempts! Bye.")
            logger.warning("Too many attempts to verify new account for " + username)
            raise SystemExit
    print()
    print(TERMS)
    print()
    if not input("Accept [yes/no]? ").lower() == 'yes':
        print("Bye.")
        raise SystemExit
    while True:
        print("Now, create a password for ISELab. This should not be the same as your ISU password!")
        password = getpass.getpass()
        confirm_password = getpass.getpass("Confirm Password: ")
        if password == confirm_password:
            logger.info("Creating account {}".format(username))
            print("Setting up your account. Please wait...")
            try:
                provision(username, password)
                user = User.create(netid=username)
                user.set_password(password)
                user.save()
            except Exception as e:
                logger.error("Error creating account {}: {}".format(username, e))
                print("Error! Couldn't create your account. Please request help in #iselab on https://iasg.slack.com.")
                raise SystemExit
            return user
        else:
            print()
            print("Passwords didn't match! Try again.")
