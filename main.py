from collections import UserDict
from datetime import datetime, timedelta
from pathlib import Path
import pickle


DATA_FILE = Path(__file__).with_name("addressbook.pkl")


class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    pass


class Phone(Field):
    def __init__(self, value):
        if not self.is_valid(value):
            raise ValueError("Phone number must contain exactly 10 digits.")
        super().__init__(value)

    @staticmethod
    def is_valid(value):
        return value.isdigit() and len(value) == 10


class Birthday(Field):
    def __init__(self, value):
        try:
            birthday = datetime.strptime(value, "%d.%m.%Y").date()
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")
        super().__init__(birthday)

    def __str__(self):
        return self.value.strftime("%d.%m.%Y")


class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone):
        self.phones.append(Phone(phone))

    def remove_phone(self, phone):
        self.phones = [p for p in self.phones if p.value != phone]

    def edit_phone(self, old_phone, new_phone):
        for index, phone in enumerate(self.phones):
            if phone.value == old_phone:
                self.phones[index] = Phone(new_phone)
                return
        raise ValueError(f"Phone {old_phone} not found.")

    def find_phone(self, phone):
        for p in self.phones:
            if p.value == phone:
                return p.value
        return None

    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)

    def __str__(self):
        phones = "; ".join(p.value for p in self.phones) or "no phones"
        birthday = f", birthday: {self.birthday}" if self.birthday else ""
        return f"{self.name.value}: {phones}{birthday}"


class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name)

    def delete(self, name):
        if name in self.data:
            del self.data[name]

    def get_upcoming_birthdays(self):
        today = datetime.today().date()
        upcoming_birthdays = []

        for record in self.data.values():
            if record.birthday is None:
                continue

            birthday_this_year = record.birthday.value.replace(year=today.year)
            if birthday_this_year < today:
                birthday_this_year = birthday_this_year.replace(year=today.year + 1)

            delta_days = (birthday_this_year - today).days
            if 0 <= delta_days <= 7:
                congratulation_date = birthday_this_year
                if congratulation_date.weekday() == 5:
                    congratulation_date += timedelta(days=2)
                elif congratulation_date.weekday() == 6:
                    congratulation_date += timedelta(days=1)

                upcoming_birthdays.append(
                    {
                        "name": record.name.value,
                        "congratulation_date": congratulation_date.strftime("%d.%m.%Y"),
                    }
                )

        return upcoming_birthdays


def save_data(book, filename=DATA_FILE):
    with open(filename, "wb") as file:
        pickle.dump(book, file)


def load_data(filename=DATA_FILE):
    try:
        with open(filename, "rb") as file:
            return pickle.load(file)
    except FileNotFoundError:
        return AddressBook()


def parse_input(user_input):
    cmd, *args = user_input.split()
    cmd = cmd.strip().lower()
    return cmd, *args


def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as error:
            return str(error)
        except IndexError:
            return "Enter the required arguments."
        except KeyError:
            return "Contact not found."

    return inner


@input_error
def add_contact(args, book):
    name, phone, *_ = args
    record = book.find(name)
    message = "Contact updated."

    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."

    record.add_phone(phone)
    return message


@input_error
def change_contact(args, book):
    name, old_phone, new_phone, *_ = args
    record = book.find(name)

    if record is None:
        return f"Contact {name} not found."

    record.edit_phone(old_phone, new_phone)
    return "Contact updated."


@input_error
def show_contact(args, book):
    name, *_ = args
    record = book.find(name)

    if record is None:
        return f"Contact {name} not found."

    return "; ".join(phone.value for phone in record.phones) or "No phones found."


@input_error
def show_all_contacts(book):
    if not book.data:
        return "No contacts found."
    return "\n".join(str(record) for record in book.data.values())


@input_error
def add_birthday(args, book):
    name, birthday, *_ = args
    record = book.find(name)

    if record is None:
        return f"Contact {name} not found."

    record.add_birthday(birthday)
    return "Birthday added."


@input_error
def show_birthday(args, book):
    name, *_ = args
    record = book.find(name)

    if record is None:
        return f"Contact {name} not found."
    if record.birthday is None:
        return f"Birthday for {name} not found."

    return str(record.birthday)


@input_error
def birthdays(args, book):
    upcoming_birthdays = book.get_upcoming_birthdays()

    if not upcoming_birthdays:
        return "No upcoming birthdays."

    return "\n".join(
        f"{item['name']}: {item['congratulation_date']}" for item in upcoming_birthdays
    )


def main():
    book = load_data()

    print("Welcome to the assistant bot!")
    print(
        "Available commands:\n"
        + "-> hello\n"
        + "-> add <name> <phone>\n"
        + "-> change <name> <old_phone> <new_phone>\n"
        + "-> phone <name>\n"
        + "-> all\n"
        + "-> add-birthday <name> <birthday DD.MM.YYYY>\n"
        + "-> show-birthday <name>\n"
        + "-> birthdays\n"
        + "-> close/exit"
    )

    while True:
        user_input = input("Enter a command: ")
        if not user_input.strip():
            continue

        command, *args = parse_input(user_input)

        if command in ["close", "exit"]:
            save_data(book)
            print("Good bye!")
            break
        elif command == "hello":
            print("How can I help you?")
        elif command == "add":
            print(add_contact(args, book))
        elif command == "change":
            print(change_contact(args, book))
        elif command == "phone":
            print(show_contact(args, book))
        elif command == "all":
            print(show_all_contacts(book))
        elif command == "add-birthday":
            print(add_birthday(args, book))
        elif command == "show-birthday":
            print(show_birthday(args, book))
        elif command == "birthdays":
            print(birthdays(args, book))
        else:
            print("Invalid command.")


if __name__ == "__main__":
    main()
