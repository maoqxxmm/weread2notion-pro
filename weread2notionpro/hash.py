import hashlib


def md5(s: str) -> str:
    return hashlib.md5(s.encode('utf-8')).hexdigest()


def generate_code(input_value):
    if isinstance(input_value, (dict, list, object)) and not isinstance(input_value, str):
        input_value = str(input_value)

    if not isinstance(input_value, str):
        return input_value

    hash1 = md5(input_value)
    result = hash1[:3]  # 前3字符

    if input_value.isdigit():
        encoding_type = '3'
        parts = [
            hex(int(input_value[i:i+9]))[2:]
            for i in range(0, len(input_value), 9)
        ]
    else:
        encoding_type = '4'
        hex_string = ''.join(hex(ord(c))[2:] for c in input_value)
        parts = [hex_string]

    result += encoding_type
    result += '2' + hash1[-2:]

    for i, part in enumerate(parts):
        len_hex = hex(len(part))[2:].zfill(2)
        result += len_hex + part
        if i < len(parts) - 1:
            result += 'g'

    if len(result) < 20:
        result += hash1[:20 - len(result)]

    result += md5(result)[:3]
    return result


def main():
    examples = [
        "40055543",
        "758875",
        "CB_78wGKkGLd1V76Un6UO"
    ]
    for item in examples:
        print(f"Input: {item}")
        print(f"Code:  {generate_code(item)}\n")


if __name__ == '__main__':
    main()
