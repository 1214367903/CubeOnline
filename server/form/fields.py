import re
from typing import Any, Dict

from config import applets_api, available_contest_items, room_events
from form import forms


class BaseField:
    """
    这个类用于判断用户给的某个值是否合法
    它会判断字段是否存在,字段类型对不对,str化的字段能否通过正则匹配
    此外,也可以重写other_checks实现一些自定义的数据验证
    """
    REGULAR = re.compile(r'^.*$')
    RE_REQUIRED = False
    TYPE = str

    def __init__(self, necessary: bool = True) -> None:
        self.value = None
        self.necessary = necessary

    def valid(self, field_name: str, args: dict) -> bool:
        value = args.get(field_name, None)
        # 如果这个字段不是必须的,那就只取值,不验证
        if not self.necessary:
            self.value = value
            return True
        if not isinstance(value, self.TYPE):
            return False
        if self.RE_REQUIRED:
            ret = re.match(self.REGULAR, str(value))
            if ret is None:
                return False
        if not self.other_checks(value):
            return False
        self.value = self.value_process(value)
        return True

    @staticmethod
    def value_process(value: Any) -> Any:
        # 这一步是为了给表单增加灵活性
        # 比如,如果用户输入的是密码,那么在这里就可以把密码加密了
        return value

    def other_checks(self, value: Any) -> bool:
        # 如果需要一些比较复杂的验证, 重写这个函数就行了
        return True


class NonEmptyStrField(BaseField):

    def other_checks(self, value: Any) -> bool:
        return value != ''


class BoolField(BaseField):
    TYPE = bool


class DictField(BaseField):
    TYPE = dict


class UrlField(BaseField):
    REGULAR = re.compile(r'^http(s)?:\/\/.*$')
    RE_REQUIRED = True


class FormField(BaseField):
    # 这个字段的数据本身也是一张表,可以指定必须的key名以及对应value的数据类型,用法就是套娃
    TYPE = dict

    def __init__(self, fields: Dict[str, BaseField], *args: Any, **kwargs: Any) -> None:
        self.fields = fields
        super().__init__(*args, **kwargs)

    def other_checks(self, value: dict) -> bool:
        form = forms.BaseForm(value, self.fields)
        return form.valid


class ContestItemField(BaseField):

    def other_checks(self, value: str) -> bool:
        return value in available_contest_items


class NaturalNumField(BaseField):
    TYPE = int

    def other_checks(self, value: int) -> bool:
        return value > 0


class RoomIdField(BaseField):
    TYPE = str

    def other_checks(self, value: str) -> bool:
        if not value.isnumeric():
            return False
        return 1000 <= int(value) <= 9999


class RoomEventField(BaseField):
    TYPE = str

    def other_checks(self, value: str) -> bool:
        return value in room_events


class AppletField(BaseField):
    TYPE = str

    def other_checks(self, value: Any) -> bool:
        return value in applets_api.keys()
