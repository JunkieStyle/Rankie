import pytest

from django.core.exceptions import ValidationError

from apps.rankie.models import GameParserValidator


class TestGameParserValidator:
    @pytest.mark.parametrize("expression", [r"", r"\w", r"1234", r"(?P<key>value)"])
    def test_validate_is_regex__correct(self, expression):
        validator = GameParserValidator()
        validator.validate_is_regex(expression)

    @pytest.mark.parametrize("expression", [r"[", r"((", r"(?P<key>value)(?P<key>value)"])
    def test_validate_is_regex__incorrect(self, expression):
        validator = GameParserValidator()
        with pytest.raises(ValidationError):
            validator.validate_is_regex(expression)

    @pytest.mark.parametrize(
        "expression, required_groups",
        [
            (r"", None),
            (r"", []),
            (r"(?P<key>value)", ["key"]),
            (r"(?P<key1>value)(?P<key2>value)", ["key1", "key2"]),
        ],
    )
    def test_validate_regex_groups__correct(self, expression, required_groups):
        validator = GameParserValidator(required_groups)
        validator.validate_regex_groups(expression)

    @pytest.mark.parametrize(
        "expression, required_groups",
        [
            ("", ["key"]),
            ("(?P<key1>value)", ["key1", "key2"]),
        ],
    )
    def test_validate_regex_groups__incorrect(self, expression, required_groups):
        validator = GameParserValidator(required_groups)
        with pytest.raises(ValidationError):
            validator.validate_regex_groups(expression)
