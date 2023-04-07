import pytest

import jextract
import argparse
from pathlib import Path

HERE = Path(__file__).parent
SRC = HERE.parent / 'src'
COMMAND = "jextract.py"


def test_parse_args_returns_parsed_arguments():
    result = jextract.parse_args(['--names'])
    assert isinstance(result, argparse.Namespace)
    assert result.names is True
    assert result.all_names is False


