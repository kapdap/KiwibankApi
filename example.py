from kiwibank_api import KiwibankApi

import time
import logging
import datetime


"""
The purpose of this main file is to show how to use the KiwiBankApi.
Of course all the logins, keepsafe and bank account informations here are fakes and need to be replaced by your own.
"""
if __name__ == "__main__":

    # login informations
    user = "1234567"
    password = "MySuperPassword"

    # KeepSafe challenge informations
    questionsAnswers = {
        "The name of my first pet?": "pinette",
        "My mother's maiden name?": "duchesse d'orléans",
        "Another question?": "another response",
    }

    # CSV extract informations
    accountId = "123456789ABCDEF123456789ABCDEF12"
    accountType = "" # "credit-card"
    
    dateFrom = str((datetime.datetime.today() - datetime.timedelta(days=7)).strftime("%d/%m/%Y"))
    dateTo = str(datetime.datetime.today().strftime("%d/%m/%Y"))

    # Logging stuff
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s %(threadName)s %(levelname)s %(filename)s %(funcName)s: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    kbApi = KiwibankApi()

    kbApi.login(user, password)
    kbApi.resolveChallenge(questionsAnswers)
    csvTxt = kbApi.extractCSV(accountId, accountType, dateFrom, dateTo)
    kbApi.logout()

    csvLines = csvTxt.split("\n")

    for line in csvLines:
        logger.info(line)

    logger.info("That's all folks !!!")
