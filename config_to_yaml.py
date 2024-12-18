import re
import argparse
import yaml

class ConfigParser:
    def __init__(self):
        self.constants = {}

    def parse(self, text):
        text = self._remove_comments(text)
        text = self._resolve_constants(text)
        return self._parse_structure(text)

    def _remove_comments(self, text):
        return re.sub(r"\{#.*?#\}", "", text, flags=re.DOTALL)

    def _resolve_constants(self, text):
        constant_pattern = re.compile(r"([a-zA-Z]+)\s*<-\s*(.*?);", re.MULTILINE)
        for match in constant_pattern.finditer(text):
            name, value = match.groups()
            value = value.strip()
            self.constants[name] = self._parse_value(value)

        def replace_constant(match):
            name = match.group(1)
            if name in self.constants:
                return str(self.constants[name])
            raise ValueError(f"Undefined constant: {name}")

        text = re.sub(r"\${([a-zA-Z]+)}", replace_constant, text)
        text = re.sub(constant_pattern, "", text)
        return text

    def _parse_structure(self, text):
        if text.startswith("table(["):
            return self._parse_dict(text)
        elif text.startswith("'("):
            return self._parse_array(text)
        else:
            raise ValueError("Unsupported structure")

    def _parse_dict(self, text):
        dict_pattern = re.compile(r"table\(\[([\s\S]*)\]\)")
        match = dict_pattern.match(text)
        if not match:
            raise ValueError("Invalid dictionary format")

        entries = match.group(1).strip()
        result = {}
        entry_pattern = re.compile(r"([a-zA-Z]+)\s*=\s*(.*?),")
        for match in entry_pattern.finditer(entries):
            key, value = match.groups()
            result[key] = self._parse_value(value.strip())

        return result

    def _parse_array(self, text):
        array_pattern = re.compile(r"'\(\s*(.*?)\s*\)")
        match = array_pattern.match(text)
        if not match:
            raise ValueError("Invalid array format")

        elements = match.group(1).split()
        return [self._parse_value(element) for element in elements]

    def _parse_value(self, value):
        if value.startswith("table(["):
            return self._parse_dict(value)
        elif value.startswith("'("):
            return self._parse_array(value)
        elif re.match(r"^-?\d+(\.\d+)?$", value):
            return float(value) if '.' in value else int(value)
        else:
            return value.strip()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert configuration language to YAML.")
    parser.add_argument("output", help="Path to the output YAML file.")
    parser.add_argument("-i", "--input", help="Path to the input configuration file. If not provided, reads from standard input.", default=None)
    args = parser.parse_args()

    if args.input:
        with open(args.input, 'r') as input_file:
            input_text = input_file.read()
    else:
        print("Enter configuration text (Ctrl+D to finish):")
        input_text = "".join(iter(input, ""))

    config_parser = ConfigParser()
    try:
        parsed_data = config_parser.parse(input_text)
        with open(args.output, 'w') as output_file:
            yaml.dump(parsed_data, output_file, default_flow_style=False, allow_unicode=True)
    except Exception as e:
        print(f"Error: {e}")

