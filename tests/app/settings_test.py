from pydantic import TypeAdapter, ValidationError
from pytest import raises

from pkscrd.app.settings.model import Settings
from pkscrd.app.settings.service import create_validation_error_message


class Test_validation_error_to_message:

    def test(self):
        obj = {
            "obs": {"port": "x", "password": 123},
            "bouyomichan": {"speed": 100.1},
            "routine": {"notifies_log": "x"},
        }
        with raises(ValidationError) as error_info:
            TypeAdapter(Settings).validate_python(obj)

        lines = create_validation_error_message(error_info.value)
        assert list(lines) == [
            "obs.port: 整数を設定してください",
            "obs.password: 文字列を設定してください",
            "obs.source: 必須項目です",
            "bouyomichan.speed: 整数を設定してください",
            "routine.notifies_log: true または false を設定してください",
        ]
