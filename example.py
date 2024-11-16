from kiwibank_api import KiwibankApi

import datetime

class Account:
    def __init__(
        self,
        Id=None,
        AccountType=None,
        DateFrom=None,
        DateTo=None,
        AmountLow=None,
        AmountHigh=None,
        ExportInclude=None,
        ExportFormat=None,
    ):
        self.Id = Id
        self.AccountType = AccountType
        self.DateFrom = DateFrom
        self.DateTo = DateTo
        self.AmountLow = AmountLow
        self.AmountHigh = AmountHigh
        self.ExportInclude = ExportInclude
        self.ExportFormat = ExportFormat

    def __str__(self):
        return (
            f"Account(Id={self.Id}, AccountType={self.AccountType}, DateFrom={self.DateFrom}, DateTo={self.DateTo}, "
            f"AmountLow={self.AmountLow}, AmountHigh={self.AmountHigh}, ExportInclude={self.ExportInclude}, "
            f"ExportFormat={self.ExportFormat})"
        )

if __name__ == "__main__":

    # Login details
    user = "1234567"
    password = "MySuperPassword"

    # KeepSafe challenge
    questionsAnswers = {
        "The name of my first pet?": "pinette",
        "My mother's maiden name?": "duchesse d'orléans",
        "Another question?": "another response",
    }

    accounts = [
        Account(
            Id = "123456789ABCDEF123456789ABCDEF12",
            AccountType = "",  # Empty string for standard accounts or "credit-card" for credit card accounts
            DateFrom = datetime.datetime(2024, 6, 1),
            DateTo = datetime.datetime.today(),
            AmountLow = "",
            AmountHigh = "",
            ExportInclude = "DepositsAndWithdrawals",  # DepositsAndWithdrawals, WithdrawalsOnly, DepositsOnly
            ExportFormat = "OFX"  # CSV-Extended, CSV-Basic, OFX, OFC, QIF, PDF-Extended, PDF-Basic
        ),
        Account(
            Id = "123456789ABCDEF123456789ABCDEF13",
            AccountType = "credit-card",
            DateFrom = datetime.datetime(2024, 1, 1),
            DateTo = datetime.datetime(2024, 3, 1),
            AmountLow = 100,
            AmountHigh = 5000,
            ExportInclude = "WithdrawalsOnly",
            ExportFormat = "CSV-Extended"
        )
    ]

    formats = {
        "CSV-Extended": "csv",
        "CSV-Basic": "csv",
        "OFX": "ofx",
        "OFC": "ofc",
        "QIF": "qif",
        "PDF-Extended": "pdf",
        "PDF-Basic": "pdf"
    }

    kbApi = KiwibankApi()

    kbApi.login(user, password)
    kbApi.resolveChallenge(questionsAnswers)

    for account in accounts:
        exportData = kbApi.exportStatement(
            account.Id,
            account.AccountType,
            account.DateFrom,
            account.DateTo,
            account.AmountLow,
            account.AmountHigh,
            account.ExportInclude,
            account.ExportFormat
        )

        fileName = "_".join(
            filter(
                None,
                [
                    account.Id,
                    str(account.DateFrom.strftime("%Y_%m_%d")),
                    str(account.DateTo.strftime("%Y_%m_%d")),
                    account.AmountLow,
                    account.AmountHigh,
                    account.ExportInclude,
                    account.ExportFormat,
                ],
            )
        ).replace(".", "_") + "." + formats[account.ExportFormat]

        fileData = "\n".join(exportData.splitlines())

        with open(fileName, "w") as exportFile:
            exportFile.write(fileData)

    kbApi.logout()