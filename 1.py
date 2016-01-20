#Filename: ADDRESS_BOOK
class Person:
    def __init__(self, name, phone=None, email=None):
        self.name = name
        self.phone = phone
        self.email = email


class AddressBook:
    ContactNum = 0
    D = {}
    
    def __init__(self, name=None):
        print('Create one Address_Book: \
        the operation you can do is add, delete, find, export.')
        self.name = name
        print('This connect book is empty, please add.')

    def add(self, Person p):
        AddressBook.D[p.name] = [p.phone, p.email]
        AddressBook.ContactNum += 1
