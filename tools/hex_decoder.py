import urllib.parse


def decode_url(input_string: str) -> str:
    return urllib.parse.unquote(input_string)


if __name__ == "__main__":
    encoded_string = "niya%E1%B9%81"
    decoded_string = decode_url(encoded_string)
    print(decoded_string)
