import re


def string_formatting(string: str) -> str:
    string = string.strip()
    string = re.sub(r"\"", "&quot;", string)

    # Remove wrapping <p></p> tags, only if there aren't any <p> or </p> in the middle.
    if string.startswith("<p>") and string.endswith("</p>"):
        inner_string = string[3:-4]
        if not re.search(r"<p>|</p>", inner_string, re.DOTALL):
            # No middle <p> or </p> tags found, so we can strip the outer tags
            string = inner_string

    return string


def to_camel_case(input_string: str) -> str:
    # Remove any non-alphanumeric characters (optional based on needs)
    input_string = re.sub(r"[^a-zA-Z0-9\s_]", "", input_string)

    # Split the string by spaces or underscores
    words = re.split(r"[_\s]+", input_string)

    # Capitalize each word except the first one, and join them together
    return words[0].lower() + "".join(word.capitalize() for word in words[1:])
