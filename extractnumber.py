import re

def extract_numbers_and_amounts(string):
    # Pattern to match phone numbers
    phone_pattern = r'\d{10,}'
    phone_number = re.findall(phone_pattern, string)
    phone_number = phone_number[0] if phone_number else None

    # Pattern to match dollar amounts
    amount_pattern = r'\$\d+(?:\.\d+)?'
    amount = re.findall(amount_pattern, string)
    amount = amount[0] if amount else None

    return "+"+phone_number, amount[1:]


if __name__ == "__main__":
    string1 = "Send 19095555555 $21"
    string2 = "Send $2 to 254799555555"

    phone_number1, amount1 = extract_numbers_and_amounts(string1)
    phone_number2, amount2 = extract_numbers_and_amounts(string2)

    print(phone_number1, amount1)
    print(phone_number2, amount2)