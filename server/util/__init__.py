"""
这里放了项目需要的各种组件
启动项目之前,必须先调用init_utils把组件初始化,否则有些组件用不了
"""


async def init_utils() -> None:
    # 有些组件依赖于connector,因此必须先初始化connector
    import util.connector
    await util.connector.init()

    import util.cache
    import util.scrambler
    await util.cache.init()
    await util.scrambler.init()


class UtilError(Exception):
    """
    如果使用组件的方式不当,就引发这个异常
    """
    pass
