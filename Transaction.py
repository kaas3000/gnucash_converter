from datetime import date


class transaction:
    '''
    Transaction data container
    '''
    heading = [
        'Date',
        'Num',
        'Description',
        'Notes',
        'Account',
        'Deposit',
        'Withdrawal',
        'Balance',
    ]

    def __init__(self, transaction_date=None,
                 num=None,
                 description=None,
                 notes=None,
                 account=None,
                 deposit=None,
                 withdrawal=None,
                 balance=None):
        self.date = transaction_date
        self.num = num
        self.description = description
        self.notes = notes
        self.account = account
        self.deposit = deposit
        self.withdrawal = withdrawal
        self.balance = balance

    def asList(self) -> list:
        '''
        Return list representation to be used for CSV export
        '''
        date = getattr(self, 'date', '')
        num = getattr(self, 'num', '')
        description = getattr(self, 'description', '')
        notes = getattr(self, 'notes', '')
        account = getattr(self, 'account', '')
        deposit = getattr(self, 'deposit', '')
        withdrawal = getattr(self, 'withdrawal', '')
        balance = getattr(self, 'balance', '')

        return [
            date,
            num,
            description,
            notes,
            account,
            deposit,
            withdrawal,
            balance,
        ]
