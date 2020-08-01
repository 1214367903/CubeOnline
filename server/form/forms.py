import json
from typing import Any, Dict, Union

from tornado.escape import json_decode

from form.fields import (AppletField, BaseField, BoolField, ContestItemField,
                         DictField, FormField, NaturalNumField,
                         NonEmptyStrField, RoomEventField, RoomIdField,
                         UrlField)


class BaseForm:
    """
    这东西负责对前端数据的提取和校验
    首先实例化这个类,然后调用valid判断数据是否满足要求
    最后,调用get方法来获取对应的数据
    """

    def __init__(self, form_data: Union[dict, str, bytes], fields: Dict[str, BaseField]) -> None:
        self._value_dict = {}
        self._is_valid = True
        self.fields = fields
        self.error_message = ''
        if isinstance(form_data, dict):
            self.form_data = form_data
        else:
            try:
                self.form_data = json_decode(form_data)
            except (json.decoder.JSONDecodeError, TypeError):
                self._is_valid = False
                self.error_message = 'data cannot be parsed'
                return
        self._valid()

    def _valid(self) -> None:
        for field_name, field_obj in self.fields.items():
            is_valid = field_obj.valid(field_name, self.form_data)
            if not is_valid:
                self._is_valid = False
                self.error_message = f'the {field_name} is not valid!'
                break
            self._value_dict[field_name] = field_obj.value

    @property
    def valid(self) -> bool:
        return self._is_valid

    def get(self, name: str, default: Any = None) -> Any:
        return self._value_dict.get(name, default)

    def __str__(self) -> str:
        return str(self._value_dict)


class LoginForm(BaseForm):

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        fields = {
            'username': NonEmptyStrField(),
            'usericon': UrlField(),
            'has_session_id': BoolField(),
            'session_id': NonEmptyStrField(necessary=False),
            'code': NonEmptyStrField(necessary=False),
            'applet': AppletField()
        }
        super().__init__(*args, **kwargs, fields=fields)


class CreateRoomForm(BaseForm):

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        fields = {
            'room_settings': FormField(fields={
                'contest_item': ContestItemField(),
                'time_limit': NaturalNumField(),
                'is_room_private': BoolField()
            }),
            'session_id': NonEmptyStrField(necessary=False),
        }
        super().__init__(*args, **kwargs, fields=fields)


class RandomRoomForm(BaseForm):

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        fields = {
            'room_settings': FormField(fields={
                'contest_item': ContestItemField(),
            }),
            'session_id': NonEmptyStrField(necessary=False),
        }
        super().__init__(*args, **kwargs, fields=fields)


class JoinRoomForm(BaseForm):

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        fields = {
            'room_id': RoomIdField(),
            'session_id': NonEmptyStrField(),
        }
        super().__init__(*args, **kwargs, fields=fields)


class MessageForm(BaseForm):

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        fields = {
            'event': RoomEventField(),
            'data': DictField(),
        }
        super().__init__(*args, **kwargs, fields=fields)


class PingForm(BaseForm):

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        fields = {
            'ping': NaturalNumField(),
        }
        super().__init__(*args, **kwargs, fields=fields)
