import csv
import datetime
from decimal import *
import locale
from Transaction import transaction


class GnuCashConverter:
    '''
    csv to gnucash csv import conversion
    uses the rabobankConverter strategy classes to do the conversion
    '''

    testing = False

    def convert(self, source, target, bank, initial_balance, final_balance):
        '''
        manages the conversion
        '''

        with open(source) as csvFile:
            with open (target, 'w', newline='') as newFile:

                if bank == 'rabobank (csv)':
                    converter = rabobankConverter(csv.reader(csvFile, delimiter=',', quotechar='"'))
                elif bank == 'rabobank (txt)':
                    converter = rabobankTXTConverter(csv.reader(csvFile, delimiter=',', quotechar='"'))
                elif bank == 'ing':
                    converter = ingConverter(csv.reader(csvFile, delimiter=';', quotechar='"'))
                else:
                    return False

                converter.setInitialBalance(initial_balance)
                converter.setFinalBalance(final_balance)
                converter.convert()

                gnucashCsv = csv.writer(newFile, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)

                # gnucashCsv.writerow(['date', 'credit', 'debet', 'cumulative', 'message'])
                gnucashCsv.writerow(transaction.heading)

                # converter class is iterable
                while converter.nextRow():
                    if (self.testing):
                        print(converter.getRow().asList())
                    else:
                        gnucashCsv.writerow(converter.getRow().asList())

    def setTesting(self):
        '''
        to set the conversion to print results instead of writing to a csv
        '''
        self.testing = True


class abstractConverter:
    '''
    strategy parent class with shared methods
    '''

    def __init__(self, reader):
        '''
        setup class, save csv reader
        '''
        self.reader    = reader
        self.pointer     = 0
        self.rowcount    = 0
        self.rows        = []

    def convert(self):
        '''
        extract data from the import csv into row array
        '''
        for counter, row in enumerate(self.reader):
            new_row = self.newRow(row, counter)
            if new_row:
                self.rows.append(new_row)

        self.rowcount = len(self.rows)

    def setInitialBalance(self, initial_balance):
        '''
        set the initial balance, for the balance column
        '''
        self.balance = initial_balance

    def setFinalBalance(self, final_balance):
        '''
        set the final balance to check results
        not implemented yet
        '''
        self.final_balance = final_balance

    def nextRow(self):
        '''
        do we have a next row for iteration
        '''
        if self.pointer >= self.rowcount:
            return False

        return True

    def getRow(self) -> transaction:
        '''
        get the next row
        '''
        self.pointer += 1

        return self.rows[self.pointer - 1]

    def newRow(self, row, counter):
        '''
        abstract method
        create a new row from an import csv row

        A row contains the following elements:
            [
                Date,
                Deposit,
                Withdrawal,
                Balance,
                Description,
            ]
        '''
        raise NotImplementedError('interface / abstract class!')


class rabobankConverter(abstractConverter):
    '''
    strategy converter for rabobank csvs
    '''

    def newRow(self, row, counter):
        '''
        create a new row from an import csv row

        A row contains the following elements:
            [
                Date,
                Deposit,
                Withdrawal,
                Balance,
                Description,
            ]
        '''
        rabobankCsvDecimalSeperator = ','

        # skip the title row
        if counter == 0:
            return False

        newTransaction = transaction()

        # date
        newTransaction.date = datetime.datetime.strptime(row[4], "%Y-%m-%d").date()

        amount = parseAmount(row[6], rabobankCsvDecimalSeperator)

        # amount - credit
        if amount >= 0:
            newTransaction.deposit = amount.copy_abs()

        # amount - debet
        else:
            newTransaction.withdrawal = amount.copy_abs()

        # Balance
        newTransaction.balance = parseAmount(row[7], rabobankCsvDecimalSeperator)

        newTransaction.num = row[3]  # Volgnr
        newTransaction.description = row[9]  # Naam tegenpartij
        newTransaction.account = row[0]  # IBAN/BBAN
        newTransaction.notes = self.setMessage(row)

        return newTransaction

    def setMessage(self, row):
        '''
        collect the message from all possible rows
        '''

        messages = [
            row[8],  # Tegenrekening IBAN/BBAN
            row[12],  # BIC tegenpartij
            row[9],  # Naam tegenpartij
            row[19],  # Omschrijving-1
            row[20],  # Omschrijving-2
            row[21],  # Omschrijving-3
            row[13],  # Code
            row[15],  # Transactiereferentie
            row[16],  # Machtigingskenmerk
            row[17],  # Incassant ID
            row[18],  # Betalingskenmerk
        ]

        return ' '.join(s.strip() for s in messages if s.strip())


class rabobankTXTConverter(abstractConverter):
    '''
    strategy converter for rabobank csvs
    '''

    def newRow(self, row, counter):
        '''
        create a new row from an import csv row
        '''

        rabobankCsvDecimalSeperator = ','
        newTransaction = transaction()

        # date
        # there are two dates - this one seems to be the more accurate one
        newTransaction.date = datetime.datetime.strptime(row[2], "%Y%m%d").date()
        # newTransaction.append(datetime.datetime.strptime(row[2], "%Y%m%d").strftime("%Y-%m-%d"))
        amount = parseAmount(row[4], rabobankCsvDecimalSeperator)

        # amount - credit
        if row[3] == 'C':
            newTransaction.deposit = amount

            newTransaction.balance = self.calculateBalance(amount, "credit", counter)
        # amount - debet
        elif row[3] == 'D':
            newTransaction.withdrawal = amount

            newTransaction.balance = (self.calculateBalance(amount, "debet", counter))

        newTransaction.description = self.setMessage(row)

        return newTransaction

    def calculateBalance(self, amount, type, counter):
        '''
        calculate the current balance
        '''

        if counter == 0:
            return self.balance
        else:
            if type == "credit":
                self.balance = Decimal(self.balance) + amount
            elif type == "debet":
                self.balance = Decimal(self.balance) - amount

        return str(round(self.balance, 2))

    def setMessage(self, row):
        '''
        collect the message from all possible rows
        '''

        messages = [row[5], row[6], row[10], row[11], row[12], row[13], row[14], row[15], row[16], row[17], row[18]]

        return ' '.join(s.strip() for s in messages if s.strip())


class ingConverter(abstractConverter):
    '''
    create a new row from an import csv row
    '''

    def newRow(self, row, counter):
        '''
        return new row from the import csv
        '''

        # skip the title row
        if counter == 0:
            return False

        newTransaction = transaction()
        ingCsvDecimalSeperator = ','

        # date
        newTransaction.date = datetime.datetime.strptime(row[1], "%Y%m%d")

        amount = parseAmount(row[7], ingCsvDecimalSeperator)
        # amount - credit
        if row[6] == 'Bij':
            newTransaction.deposit = amount

            newTransaction.balance = self.calculateBalance(amount, "credit", counter)
        # amount - debet
        elif row[6] == 'Af':
            newTransaction.withdrawal = amount

            newTransaction.balance = self.calculateBalance(amount, "debet", counter)

        newTransaction.description = self.setMessage(row)

        return newTransaction

    def calculateBalance(self, amount, type, counter):
        '''
        calculate the current balance
        '''

        if counter == 0:
            return self.balance
        else:
            if type == "credit":
                self.balance = Decimal(self.balance) + amount
            elif type == "debet":
                self.balance = Decimal(self.balance) - amount

        return str(round(self.balance, 2))

    def setMessage(self, row):
        '''
        collect the message from all possible rows
        '''

        message = []

        for id, msg in enumerate(row):
            if (id == 2 or id == 4 or id == 9 or id == 10 or id == 11 or id == 12):
                message.append(msg.strip())

        return ''.join(c for c in message)


def parseAmount(amount, amountSeperator):
    '''
    Turn the amount as string into a decimal with the correct decimal seperator.
    It uses the system locale to do this.

    Return amount as Decimal if successful or None if not successful
    '''

    localeSeperator = locale.localeconv()['decimal_point']
    amountDecimal = None

    if amountSeperator == localeSeperator:
        amountDecimal = Decimal(amount)

    # Replace comma seperator to point seperator
    if amountSeperator == ',':
        amountPointSeperator = amount.replace(",", ".")
        amountPointSeperator = amountPointSeperator.replace(
            ".", "", amountPointSeperator.count(".")-1)

        amountDecimal = Decimal(amountPointSeperator)

    # Replace point seperator to point seperator
    if amountSeperator == '.':
        amountCommaSeperator = amount.replace(".", ",")
        amountCommaSeperator = amountCommaSeperator.replace(
            ",", "", amountCommaSeperator.count(","-1))

        amountDecimal = Decimal(amountCommaSeperator)

    return amountDecimal

if __name__ == '__main__':
    converter = GnuCashConverter()
    converter.setTesting()
    converter.convert(
#            "test.csv",
#            "result2.csv", 
#            "ing", 
#            121212, 
#            345)
            "test2.csv",
            "result2.csv",
            "rabobank",
            123234,
            345)
