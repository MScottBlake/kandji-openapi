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
