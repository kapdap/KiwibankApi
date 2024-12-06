import requests
import logging
import datetime
from bs4 import BeautifulSoup


class KiwibankApi(object):
    """
    A class to interact with Kiwibank's online banking services using HTTP requests.
    """

    BASE_URL = "https://www.ib.kiwibank.co.nz"

    def __init__(self):
        self.BASE_URL = self.BASE_URL.rstrip("/")

        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0"}
        )
        self.logger = logging.getLogger()
        self.last_response = None

    def login(self, username: str, password: str):
        """
        Logs into the Kiwibank online banking system using provided credentials.

        Args:
            username (str): The user's login username.
            password (str): The user's password.
        """
        self.logger.info("Attempting login...")

        try:
            # Perform GET request to fetch the login page
            self.last_response = self.session.get(f"{self.BASE_URL}/login/")
            self.last_response.raise_for_status()
        except requests.RequestException as e:
            self.logger.error(f"Network error: {e}")
            raise

        soup = BeautifulSoup(self.last_response.content, "html.parser")
        self.logger.debug(soup.prettify())

        try:
            # Extract necessary form fields from the login page
            view_state = soup.find(id="__VSTATE")["value"]
            event_validation = soup.find(id="__EVENTVALIDATION")["value"]
        except (TypeError, KeyError) as e:
            self.logger.error(f"Failed to extract form fields: {e}")
            raise ValueError("Unexpected login page structure.")

        # Prepare data payload for the login POST request
        data = [
            ("__LASTFOCUS", ""),
            ("__EVENTTARGET", "ctl00$c$ProgressFinalSubmit$FinalStepButton"),
            ("__EVENTARGUMENT", ""),
            ("__VSTATE", view_state),
            ("__VIEWSTATE", ""),
            ("__EVENTVALIDATION", event_validation),
            ("ctl00$c$IESError", ""),
            ("ctl00$c$ciam", ""),
            ("ctl00$c$txtUserName", username),
            ("ctl00$c$txtPassword", password),
        ]

        try:
            # Send POST request to submit login details
            self.last_response = self.session.post(f"{self.BASE_URL}/login/", data=data)
            self.last_response.raise_for_status()
        except requests.RequestException as e:
            self.logger.error(f"Login request failed: {e}")
            raise

        soup = BeautifulSoup(self.last_response.content, "html.parser")
        self.logger.debug(soup.prettify())

    def resolve_challenge(self, questions: dict):
        """
        Resolves the additional security challenge.

        Args:
            questions (dict): A dictionary mapping security questions to their answers.
        """
        self.logger.info("Resolving security challenge...")

        soup = BeautifulSoup(self.last_response.content, "html.parser")

        try:
            # Extract the security question from the page
            question = soup.find(id="question").find_all("div")[1].string
        except (AttributeError, IndexError) as e:
            self.logger.error(f"Failed to extract security question: {e}")
            raise ValueError("Unexpected security challenge page structure.")

        self.logger.info(f"Security Question: {question}")

        # Get the answer to the security question
        answer = questions.get(question)
        if not answer:
            self.logger.error(f"No answer found for the question: {question}")
            raise ValueError(f"No answer found for the question: {question}")

        try:
            # Parse answers and determine the required letters for the challenge
            answer_inputs = soup.find(id="answer").find_all("div")[1:]
            required_inputs = []
            challenge_pattern = ""

            for index, element in enumerate(answer_inputs):
                if "required" in str(element):
                    required_inputs.append(index)
                    challenge_pattern += "O"  # Required letter
                else:
                    challenge_pattern += "X"  # Not required

            letter1 = str(answer[required_inputs[0]])
            letter2 = str(answer[required_inputs[1]])
        except (AttributeError, IndexError, KeyError) as e:
            self.logger.error(f"Error parsing challenge response: {e}")
            raise ValueError("Unexpected structure in challenge response.")

        self.logger.info(f"Challenge: {challenge_pattern}")
        self.logger.debug(f"Letter 1: {letter1}")
        self.logger.debug(f"Letter 2: {letter2}")

        try:
            # Extract form fields for submitting the challenge response
            view_state = soup.find(id="__VSTATE")["value"]
            event_validation = soup.find(id="__EVENTVALIDATION")["value"]
        except (TypeError, KeyError) as e:
            self.logger.error(f"Failed to extract challenge form fields: {e}")
            raise ValueError("Unexpected challenge page structure.")

        data = [
            ("__EVENTTARGET", "ctl00$c$ChallengeControl$SubmitAnswer$FinalStepButton"),
            ("__EVENTARGUMENT", ""),
            ("__VSTATE", view_state),
            ("__VIEWSTATE", ""),
            ("__EVENTVALIDATION", event_validation),
            ("letter1", letter1),
            ("letter2", letter2),
        ]

        try:
            # Submit the challenge response
            self.last_response = self.session.post(f"{self.BASE_URL}/keepsafe/challenge/", data=data)
            self.last_response.raise_for_status()
        except requests.RequestException as e:
            self.logger.error(f"Failed to send challenge response: {e}")
            raise

        soup = BeautifulSoup(self.last_response.content, "html.parser")
        self.logger.debug(soup.prettify())

    def export_statement(
        self,
        account_id: str,
        account_type: str,
        date_from: datetime,
        date_to: datetime,
        amount_low: float,
        amount_high: float,
        export_include: str,
        export_format: str,
    ):
        """
        Exports a bank statement for a given account within a specified date range
        and amount range, with the option to include certain transaction details
        and specify the export format.

        Args:
            account_id (str): The unique identifier for the account.
            account_type (str): The type of the account (e.g., "checking", "savings").
            date_from (datetime): The start date of the statement period.
            date_to (datetime): The end date of the statement period.
            amount_low (float): The lower bound of the transaction amount range.
            amount_high (float): The upper bound of the transaction amount range.
            export_include (str): The types of transaction details to include in the export.
            export_format (str): The format of the export (e.g., "CSV", "PDF").

        Returns:
            str: The content of the exported statement if successful, otherwise an empty string.
        """
        self.logger.info("Exporting statement...")

        account_url = "/".join(filter(None, ["/accounts/view", account_type, account_id]))

        self.last_response = self.session.get(self.BASE_URL + account_url)

        soup = BeautifulSoup(self.last_response.content, "html.parser")
        self.logger.debug(soup.prettify())

        # Extract necessary hidden form fields for the export request
        try:
            request_verification_token = soup.find(id="__RequestVerificationToken")["value"]
            vstate = soup.find(id="__VSTATE")["value"]
            event_validation = soup.find(id="__EVENTVALIDATION")["value"]
        except (TypeError, KeyError) as e:
            self.logger.error(f"Failed to extract form fields: {e}")
            raise ValueError("Unexpected page structure during export statement retrieval.")

        # Prepare the data for export request
        data = [
            ("__RequestVerificationToken", request_verification_token),
            ("__EVENTTARGET", "ctl00$c$TransactionSearchControl$ActionButton"),
            ("__EVENTARGUMENT", ""),
            ("__LASTFOCUS", ""),
            ("__VSTATE", vstate),
            ("__VIEWSTATE", ""),
            ("__EVENTVALIDATION", event_validation),
            ("ctl00$c$TransactionSearchControl$AccountList", account_url),
            ("ctl00$c$TransactionSearchControl$DualDateSelector$initialDate$TextBox", "{dt.day}/{dt.month}/{dt.year}".format(dt=date_from)),
            ("ctl00$c$TransactionSearchControl$DualDateSelector$FromDateRegex_Highlight_ClientState", "VALID"),
            ("ctl00$c$TransactionSearchControl$DualDateSelector$FromDateTextBoxExtender_ClientState", "VALID"),
            ("ctl00$c$TransactionSearchControl$DualDateSelector$FromDateRegex_ShowError_ClientState", "VALID"),
            ("ctl00$c$TransactionSearchControl$DualDateSelector$InitialDateNotFuture_Highlight_ClientState", "VALID"),
            ("ctl00$c$TransactionSearchControl$DualDateSelector$InitialDateNotFutureTextBoxExtender_ClientState", "VALID"),
            ("ctl00$c$TransactionSearchControl$DualDateSelector$InitialDateNotFuture_ShowError_ClientState", "VALID"),
            ("ctl00$c$TransactionSearchControl$DualDateSelector$FromHistoryLimit_Highlight_ClientState", "VALID"),
            ("ctl00$c$TransactionSearchControl$DualDateSelector$FromHistoryLimitExtender_ClientState", "VALID"),
            ("ctl00$c$TransactionSearchControl$DualDateSelector$FromHistoryLimit_ShowError_ClientState", "VALID"),
            ("ctl00$c$TransactionSearchControl$DualDateSelector$finalDate$TextBox", "{dt.day}/{dt.month}/{dt.year}".format(dt=date_to)),
            ("ctl00$c$TransactionSearchControl$DualDateSelector$ToDateRegex_Highlight_ClientState", "VALID"),
            ("ctl00$c$TransactionSearchControl$DualDateSelector$FinalDateTextBoxExtender_ClientState", "VALID"),
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
            ("ctl00$c$TransactionSearchControl$AmountRange$TransactionAmountLowerBoundField", "" if amount_low is None else str(amount_low)),
            ("ctl00$c$TransactionSearchControl$AmountRange$LowerBoundRegex_Highlight_ClientState", "VALID"),
            ("ctl00$c$TransactionSearchControl$AmountRange$LowerBoundTextFieldExtender_ClientState", "VALID"),
            ("ctl00$c$TransactionSearchControl$AmountRange$LowerBoundRegex_ShowError_ClientState", "VALID"),
            ("ctl00$c$TransactionSearchControl$AmountRange$TransactionAmountUpperBoundField", "" if amount_high is None else str(amount_high)),
            ("ctl00$c$TransactionSearchControl$AmountRange$UpperBoundRegex_Highlight_ClientState", "VALID"),
            ("ctl00$c$TransactionSearchControl$AmountRange$UpperBoundTextFieldExtender_ClientState", "VALID"),
            ("ctl00$c$TransactionSearchControl$AmountRange$UpperBoundRegex_ShowError_ClientState", "VALID"),
            ("ctl00$c$TransactionSearchControl$DWGroup", export_include),
            ("ctl00$c$TransactionSearchControl$ExportFormats$List", export_format),
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
            ("ctl00$c$AccountGoal$SaveGoalControl$SelectedAccountGoalTypeField", "Savings")
        ]

        # Add additional fields if account type is not credit card
        if account_type != "credit-card":
            data += [
                ("ctl00$c$AccountGoal$SaveGoalControl$AccountTitleTextField", ""),
                ("ctl00$c$AccountGoal$SaveGoalControl$customisedNameValidation_errorToggle_ClientState", "VALID"),
                ("ctl00$c$AccountGoal$SaveGoalControl$ToggleCssClassExtender1_ClientState", "VALID")
            ]

        # Send POST request to perform the export
        try:
            self.last_response = self.session.post(self.BASE_URL + account_url, data=data)
            self.last_response.raise_for_status()
        except requests.RequestException as e:
            self.logger.error(f"Failed to export statement: {e}")
            raise

        if not "content-disposition" in self.last_response.headers:
            raise ValueError("No statement data for selected date range.")
        
        return self.last_response.content.decode("utf-8")

    def logout(self):
        """
        Logs out of the Kiwibank session.
        """
        try:
            self.session.get(f"{self.BASE_URL}/logout/").raise_for_status()
        except requests.RequestException as e:
            self.logger.error(f"Failed to log out: {e}")

    def __del__(self):
        """
        Closes the session when the object is destroyed.
        """
        self.session.close()
