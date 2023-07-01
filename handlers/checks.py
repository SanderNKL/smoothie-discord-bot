from time import time


def is_account_fake(self, user):
    """
    Account Checker: Is it Fake?

    This function will return true or false depending on what the bot deems to be fake.
    Brand new discord accounts with an age less than 7 days (604 800 seconds) is deemed fake
    """

    fake = False
    if time() - user.created_at.timestamp() < 604800:
        fake = True

    return fake
