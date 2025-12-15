import re

def chunk_python(code: str):
    return re.split(r"\n(?=def |class )", code)

def chunk_code(language, code):
    if language == "python":
        return chunk_python(code)
    return [code]
