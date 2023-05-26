import re

def extract_numbers_and_amounts(string):
    # Pattern to match phone numbers
    if '(' in string:
        phone_pattern = r'\+?\d? ?\(? ?\d{3} ?\)?-? ?\d{3} ?-? ?\d{4}|\d{10,}'
    else:
        phone_pattern = r'\d{10,}'

    phone_number = re.findall(phone_pattern, string)
    phone_number = phone_number[0] if phone_number else None

    # If phone number is found, we remove all non-digit characters
    if phone_number:
        phone_number = "+" + re.sub(r'\D', '', phone_number)

    # Pattern to match dollar amounts
    amount_pattern = r'\$\d+(?:\.\d+)?'
    amount = re.findall(amount_pattern, string)
    amount = amount[0] if amount else None

    # If amount is found, we remove the dollar sign
    if amount:
        amount = amount[1:]

    return phone_number, amount


if __name__ == "__main__":
    string1 = "Send 19095555555 $21"
    string2 = "Send $2 to 254799555555"
    string3 = "Send +1 (999) 529-4227 $0.20"

    phone_number1, amount1 = extract_numbers_and_amounts(string1)
    phone_number2, amount2 = extract_numbers_and_amounts(string2)
    phone_number3, amount3 = extract_numbers_and_amounts(string3)

    print(phone_number1, amount1)
    print(phone_number2, amount2)
    print(phone_number3, amount3)