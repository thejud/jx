import io

import pytest

from pathlib import Path
import re
import subprocess
import shlex
import jextract

HERE = Path(__file__).parent
SRC = HERE.parent / 'src'
COMMAND = "jextract.py"


@pytest.fixture(scope='module', params=[f for f in HERE.glob('test*.txt')])
def test_file(request):
    with open(request.param, 'r') as f:
        contents = f.read()

    # Use regular expressions to split the contents into sections
    pattern = r'^##\s(\w+)$'
    sections = re.split(pattern, contents, flags=re.MULTILINE)

    # Check that all sections are present
    expected_sections = ['DESC', 'ARGS', 'INPUT', 'OUTPUT']
    section_names = sections[1::2]
    if set(section_names) != set(expected_sections):
        raise ValueError('Invalid file format: missing or extra sections')

    desc = args = input_data = output_data = None

    for i in range(1, len(sections), 2):
        # Extract the name and content of the section
        section_name = sections[i]
        section_content = sections[i+1].strip()

        # Check the name of the section and store its content appropriately
        if section_name == 'DESC':
            desc = section_content
        elif section_name == 'ARGS':
            args = section_content
        elif section_name == 'INPUT':
            input_data = section_content
        elif section_name == 'OUTPUT':
            output_data = section_content
        else:
            raise ValueError('Invalid section title: {}'.format(section_name))

    return request.param.name, desc, args, input_data, output_data


def test_functional(test_file, monkeypatch, capsys):
    filename, description, args_string, input_string, expected_output_str = test_file
    monkeypatch.setattr('sys.stdin', io.StringIO(input_string))
    args = shlex.split(args_string)
    jextract.cli(args)
    result = capsys.readouterr().out.strip()
    assert result == expected_output_str, f"Failed test: [{filename}] {description}"

