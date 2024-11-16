import requests
import logging
import datetime
from bs4 import BeautifulSoup


class KiwibankApi(object):

    def __init__(self):
        self.session = requests.Session()
        self.logger = logging.getLogger()
        self.retRequest = None
        self.session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0"})

    def login(self, login, password):
        self.logger.info("Login attempt...")

        try:
            self.retRequest = self.session.get("https://www.ib.kiwibank.co.nz/login/")
            soup = BeautifulSoup(self.retRequest.content, "html.parser")
        except requests.RequestException as e:
            self.logger.error(f"Network error: {e}")
            raise
        
        self.logger.debug(soup.prettify())

        vstate = soup.find(id="__VSTATE")["value"]
        eventvalidation = soup.find(id="__EVENTVALIDATION")["value"]

        data = [
            ("__LASTFOCUS", ""),
            ("__EVENTTARGET", "ctl00$c$ProgressFinalSubmit$FinalStepButton"),
            ("__EVENTARGUMENT", ""),
            ("__VSTATE", vstate),
            ("__VIEWSTATE", ""),
            ("__EVENTVALIDATION", eventvalidation),
            ("ctl00$c$IESError", ""),
            ("ctl00$c$ciam", ""),
            ("ctl00$c$txtUserName", login),
            ("ctl00$c$txtPassword", password),
        ]

        self.retRequest = self.session.post(
            "https://www.ib.kiwibank.co.nz/login/", data=data
        )

        soup = BeautifulSoup(self.retRequest.content, "html.parser")
        self.logger.debug(soup.prettify())

    def resolveChallenge(self, questionsAnswers):
        self.logger.info("Resolving challenge...")

        soup = BeautifulSoup(self.retRequest.content, "html.parser")
        question = soup.find(id="question").find_all("div")[1].string

        self.logger.info("Question is : " + question)

        for k in questionsAnswers.keys():
            if question == k:
                reponse = questionsAnswers[k]
                break

        answers = soup.find(id="answer").find_all("div")[1:]

        index = []

        challenge = ""
        i = 0
        for div in answers:
            if "required" in str(div):
                index.append(i)
                challenge = challenge + "O"
            else:
                challenge = challenge + "X"
            i = i + 1

        letter1 = str(reponse[index[0]])
        letter2 = str(reponse[index[1]])

        self.logger.info("Challenge: " + challenge)
        self.logger.info("Letter 1: " + letter1)
        self.logger.info("Letter 2: " + letter2)

        vstate = soup.find(id="__VSTATE")["value"]
        eventvalidation = soup.find(id="__EVENTVALIDATION")["value"]

        data = [
            ("__EVENTTARGET", "ctl00$c$ChallengeControl$SubmitAnswer$FinalStepButton"),
            ("__EVENTARGUMENT", ""),
            ("__VSTATE", vstate),
            ("__VIEWSTATE", ""),
            ("__EVENTVALIDATION", eventvalidation),
            ("letter1", letter1),
            ("letter2", letter2),
        ]

        self.retRequest = self.session.post(
            "https://www.ib.kiwibank.co.nz/keepsafe/challenge/", data=data
        )

        soup = BeautifulSoup(self.retRequest.content, "html.parser")
        self.logger.debug(soup.prettify())

    def exportStatement(
        self,
        accountId,
        accountType,
        dateFrom: datetime,
        dateTo: datetime,
        amountLow,
        amountHigh,
        exportInclude,
        exportFormat,
    ):
        self.logger.info("Exporting statement...")
        
        accountUrl = '/'.join(filter(None, ["/accounts/view", accountType, accountId]))
        
        # Make a first get to the account to init html page
        self.retRequest = self.session.get(
            "https://www.ib.kiwibank.co.nz" + accountUrl
        )

        soup = BeautifulSoup(self.retRequest.content, "html.parser")
        self.logger.debug(soup.prettify())

        requestVerificationToken = soup.find(id="__RequestVerificationToken")["value"]
        vstate = soup.find(id="__VSTATE")["value"]
        eventvalidation = soup.find(id="__EVENTVALIDATION")["value"]

        data = [
            ("__RequestVerificationToken", requestVerificationToken),
            ("__EVENTTARGET", "ctl00$c$TransactionSearchControl$ActionButton"),
            ("__EVENTARGUMENT", ""),
            ("__LASTFOCUS", ""),
            ("__VSTATE", vstate),
            ("__VIEWSTATE", ""),
            ("__EVENTVALIDATION", eventvalidation),
            ("ctl00$c$TransactionSearchControl$AccountList", accountUrl),
            ("ctl00$c$TransactionSearchControl$DualDateSelector$initialDate$TextBox", '{dt.day}/{dt.month}/{dt.year}'.format(dt = dateFrom)),
            ("ctl00$c$TransactionSearchControl$DualDateSelector$FromDateRegex_Highlight_ClientState", "VALID"),
            ("ctl00$c$TransactionSearchControl$DualDateSelector$FromDateTextBoxExtender_ClientState", "VALID"),
            ("ctl00$c$TransactionSearchControl$DualDateSelector$FromDateRegex_ShowError_ClientState", "VALID"),
            ("ctl00$c$TransactionSearchControl$DualDateSelector$InitialDateNotFuture_Highlight_ClientState", "VALID"),
            ("ctl00$c$TransactionSearchControl$DualDateSelector$InitialDateNotFutureTextBoxExtender_ClientState", "VALID"),
            ("ctl00$c$TransactionSearchControl$DualDateSelector$InitialDateNotFuture_ShowError_ClientState", "VALID"),
            ("ctl00$c$TransactionSearchControl$DualDateSelector$FromHistoryLimit_Highlight_ClientState", "VALID"),
            ("ctl00$c$TransactionSearchControl$DualDateSelector$FromHistoryLimitExtender_ClientState", "VALID"),
            ("ctl00$c$TransactionSearchControl$DualDateSelector$FromHistoryLimit_ShowError_ClientState", "VALID"),
            ("ctl00$c$TransactionSearchControl$DualDateSelector$finalDate$TextBox", '{dt.day}/{dt.month}/{dt.year}'.format(dt = dateTo)),
            ("ctl00$c$TransactionSearchControl$DualDateSelector$ToDateRegex_Highlight_ClientState", "VALID"),
            ("ctl00$c$TransactionSearchControl$DualDateSelector$FinalDateTextBoxExtender_ClientState", "VALID",),
            ("ctl00$c$TransactionSearchControl$DualDateSelector$ToDateRegex_ShowError_ClientState", "VALID"),
            ("ctl00$c$TransactionSearchControl$DualDateSelector$DateRangeValidity_Highlight_ClientState", "VALID"),
            ("ctl00$c$TransactionSearchControl$DualDateSelector$DateRangeValidityExtender_ClientState", "VALID"),
            ("ctl00$c$TransactionSearchControl$DualDateSelector$DateRangeValidity_ShowError_ClientState", "VALID"),
            ("ctl00$c$TransactionSearchControl$DualDateSelector$FutureDate_Highlight_ClientState", "VALID"),
            ("ctl00$c$TransactionSearchControl$DualDateSelector$FinalDateNotFutureExtender_ClientState", "VALID"),
            ("ctl00$c$TransactionSearchControl$DualDateSelector$FutureDate_ShowError_ClientState", "VALID"),
            ("ctl00$c$TransactionSearchControl$DualDateSelector$ToDateHistoryLimit_Highlight_ClientState", "VALID"),
            ("ctl00$c$TransactionSearchControl$DualDateSelector$ToDateHistoryLimitExtender_ClientState", "VALID"),
            ("ctl00$c$TransactionSearchControl$DualDateSelector$ToDateHistoryLimit_ShowError_ClientState", "VALID"),
            ("ctl00$c$TransactionSearchControl$DualDateSelector$DateRangeLimitValidator_Highlight_ClientState", "VALID"),
            ("ctl00$c$TransactionSearchControl$DualDateSelector$DateRangeLimitValidatorExtender_ClientState", "VALID"),
            ("ctl00$c$TransactionSearchControl$DualDateSelector$DateRangeLimitValidator_ShowError_ClientState", "VALID"),
            ("ctl00$c$TransactionSearchControl$AmountRange$TransactionAmountLowerBoundField", amountLow),
            ("ctl00$c$TransactionSearchControl$AmountRange$LowerBoundRegex_Highlight_ClientState", "VALID"),
            ("ctl00$c$TransactionSearchControl$AmountRange$LowerBoundTextFieldExtender_ClientState", "VALID"),
            ("ctl00$c$TransactionSearchControl$AmountRange$LowerBoundRegex_ShowError_ClientState", "VALID"),
            ("ctl00$c$TransactionSearchControl$AmountRange$TransactionAmountUpperBoundField", amountHigh),
            ("ctl00$c$TransactionSearchControl$AmountRange$UpperBoundRegex_Highlight_ClientState", "VALID"),
            ("ctl00$c$TransactionSearchControl$AmountRange$UpperBoundTextFieldExtender_ClientState", "VALID"),
            ("ctl00$c$TransactionSearchControl$AmountRange$UpperBoundRegex_ShowError_ClientState", "VALID"),
            ("ctl00$c$TransactionSearchControl$DWGroup", exportInclude),
            ("ctl00$c$TransactionSearchControl$ExportFormats$List", exportFormat),
            ("ctl00$c$AccountGoal$SaveGoalControl$Starting$AmountControl$TransferFundsAmountTextBox", "0.00"),
            ("ctl00$c$AccountGoal$SaveGoalControl$Starting$AmountControl$AmountMandatoryValidator_Highlight_ClientState", "VALID"),
            ("ctl00$c$AccountGoal$SaveGoalControl$Starting$AmountControl$AmountFormatValidator_Highlight_ClientState", "VALID"),
            ("ctl00$c$AccountGoal$SaveGoalControl$Starting$AmountControl$AmountFormatValidator_ShowError_ClientState", "VALID"),
            ("ctl00$c$AccountGoal$SaveGoalControl$Starting$AmountControl$AmountValueValidator_Highlight_ClientState", "VALID"),
            ("ctl00$c$AccountGoal$SaveGoalControl$Starting$AmountControl$AmountValueValidator_ShowError_ClientState", "VALID"),
            ("ctl00$c$AccountGoal$SaveGoalControl$TargetBalance$AmountControl$TransferFundsAmountTextBox", "0.00"),
            ("ctl00$c$AccountGoal$SaveGoalControl$TargetBalance$AmountControl$AmountMandatoryValidator_Highlight_ClientState", "VALID"),
            ("ctl00$c$AccountGoal$SaveGoalControl$TargetBalance$AmountControl$AmountFormatValidator_Highlight_ClientState", "VALID"),
            ("ctl00$c$AccountGoal$SaveGoalControl$TargetBalance$AmountControl$AmountFormatValidator_ShowError_ClientState", "VALID"),
            ("ctl00$c$AccountGoal$SaveGoalControl$TargetBalance$AmountControl$AmountValueValidator_Highlight_ClientState", "VALID"),
            ("ctl00$c$AccountGoal$SaveGoalControl$TargetBalance$AmountControl$AmountValueValidator_ShowError_ClientState", "VALID"),
            ("ctl00$c$AccountGoal$SaveGoalControl$StartingAmountValidator_ErrorToggle_ClientState", "VALID"),
            ("ctl00$c$AccountGoal$SaveGoalControl$StartingAmountValidator_ErrorHighlight_ClientState", "VALID"),
            ("ctl00$c$AccountGoal$SaveGoalControl$GoalAmountValidator_ErrorToggle_ClientState", "VALID"),
            ("ctl00$c$AccountGoal$SaveGoalControl$GoalAmountValidator_ErrorHighLight_ClientState", "VALID"),
            ("ctl00$c$AccountGoal$SaveGoalControl$DateControl$SelectedDateControl$TextBox", ""),
            ("ctl00$c$AccountGoal$SaveGoalControl$DateControl$DateOverrideNull", ""),
            ("ctl00$c$AccountGoal$SaveGoalControl$DateControl$DateRequiredFieldValidator_Highlight_ClientState", "VALID"),
            ("ctl00$c$AccountGoal$SaveGoalControl$DateControl$DateRangeValidator_Highlight_ClientState", "VALID"),
            ("ctl00$c$AccountGoal$SaveGoalControl$DateControl$DateRangeValidator_ShowError_ClientState", "VALID"),
            ("ctl00$c$AccountGoal$SaveGoalControl$DateControl$DateIsDateValidator_Highlight_ClientState", "VALID"),
            ("ctl00$c$AccountGoal$SaveGoalControl$DateControl$DateIsDateValidator_ShowError_ClientState", "VALID"),
            ("ctl00$c$AccountGoal$SaveGoalControl$SelectedAccountGoalTypeField", "Savings"),
        ]
    
        if accountType != "credit-card":
            data += [
                ("ctl00$c$AccountGoal$SaveGoalControl$AccountTitleTextField", ""),
                ("ctl00$c$AccountGoal$SaveGoalControl$customisedNameValidation_errorToggle_ClientState", "VALID"),
                ("ctl00$c$AccountGoal$SaveGoalControl$ToggleCssClassExtender1_ClientState", "VALID"),
            ]

        self.retRequest = self.session.post("https://www.ib.kiwibank.co.nz" + accountUrl, data=data)
        
        return self.retRequest.content.decode("utf-8")

    def logout(self):
        self.session.get("https://www.ib.kiwibank.co.nz/logout/")

    def __del__(self):
        self.session.close()