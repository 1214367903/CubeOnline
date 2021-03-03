# CubeOnline

**CubeOnline**是一个支持实时在线PK魔方的小程序, 玩家进入房间并创建`websocket`连接, 然后进行实时竞技. 服务器基于`pypy3.6`和`tornado6.0.3`实现.

## 内容列表

- [部署](#部署)
- [服务流程](#服务流程)
  - [http部分](#http部分)
  - [WebSocket部分](#websocket部分)
- [额外部分](#额外部分)
  - [后端的form组件](#后端的form组件)
  - [后端的session组件](#后端的session组件)
  - [前端的自定义模态框](#前端的自定义模态框)
- [注意事项](#注意事项)
- [示例](#示例)
- [使用许可](#使用许可)

## 部署

在部署项目之前, 你需要先在对应的平台注册开发账号, 然后将你的```app_id```和```app_secret```填入后端的```config.py```文件.

对于服务器端, 这个项目需要 [redis](http://www.redis.cn/), [docker](https://www.docker.com/) 和 [tnoodle](https://github.com/thewca/tnoodle)等组件. 安装完成后, 使用docker将代码打包为镜像, 然后实例化容器运行即可. 在运行服务之前, 请确保**redis**和**tnoodle**处于正常工作的状态.

对于前端来说, 只需要在```app.js```中设置你的服务器url即可. 发布小程序可以参考[微信小程序发布流程](https://developers.weixin.qq.com/miniprogram/dev/framework/quickstart/release.html#%E5%8D%8F%E5%90%8C%E5%B7%A5%E4%BD%9C).

## 服务流程

### http部分
   
   目前后端提供```/user/login```,```/room/create```和```/room/random```三个http接口, 负责用户的登录, 以及为用户提供可加入的房间号码. 其工作流程如下:

   ![http_img](https://github.com/1214367903/CubeOnline/blob/master/pictures/http.png)
### WebSocket部分
   
   获取到房间号之后, 用户就可以进入房间页面, 创建WebSocket连接与后端进行通信.

   在应用层面, 通信数据的格式为```{event:xxx, data:{...}}```. 前后端都有负责处理此类消息的Handler对象, 当收到消息时, 通过反射找到event事件对应的处理方法, 将数据交由该方法进行处理. 目前有如下的消息类型:

| 事件类型         | 方向  | 说明                |
| --------------- | ---- | ------------------- |
| on_ready        | c->s | 用户点击准备按钮, 告知后端. |
| upload_score    | c->s | 用户完成本轮比赛, 向后端上传成绩. |
| initialize_room | s->c | 用户进入房间后, 后端将房间的数据传给前端渲染. |
| add_member      | s->c | 有新成员加入后, 后端将该成员的信息发送给房间其他成员. |
| delete_member   | s->c | 有成员离开后, 后端将该信息发送给房间其他成员. |
| change_state    | s->c | 房间内某个成员改变了自己的状态, 后端告知其他成员. |
| start_round     | s->c | 通知前端开始比赛. |
| update_score    | s->c | 成员上传自己的成绩后, 后端将成绩发给其他成员来实时更新. |
| finish_round    | s->c | 所有成员都完成了比赛, 后端将排名和积分等信息发送给前端. |

进入room页面, 小程序的状态机如下:

![app_img](https://github.com/1214367903/CubeOnline/blob/master/pictures/app.png)

在本项目的WebSocket通信中, 后端是被动的一方. 它不主动搞事或者发消息, 而是在接收到前端的消息之后, 基于对应的事件处理方法进行回应.

## 额外部分

本项目有多个自行开发的组件, 不光能用于本项目, 也可以用在其它地方.

### 后端的form组件

该组件负责对从前端获得的数据进行提取和验证, 支持处理**字典dict**, **字符串string**和**字节bytes**格式的数据, 其中字符串和字节会自动解码. 这个组件的工作原理如下图所示:

![form_img](https://github.com/1214367903/CubeOnline/blob/master/pictures/form.png)

如有需要, 你可以通过继承的方式自定义新的Field和Form类, 完成更多数据类型和格式验证. 这个组件的源代码可见[forms](server/form/forms.py)和[fields](server/form/fields.py).

### 后端的session组件
该组件是为tornado量身定制的, 使用协程的形式进行耗时操作. 因此在增加了tornado的session能力的同时, 也没有阻塞主线程, 造成性能损失.

这个组件的原理比较简单, 就是基于redis的哈希类型设计的. 源代码可见[user](/project/server/controller/user.py).

### 前端的自定义模态框
该模态框内可以放入任意小程序的组件, 因此可定制性强于原生模态框.

首先, 在页面的json文件中引入模态框:

```"my-modal": "/components/modal/modal"```

然后,在对应的html页面中使用即可:
```
<my-modal show="{{show_modal}}" height='60%' bindconfirm='modalConfirm'>
    你的内容
</my-modal>
```
这个模态框的源代码可见[modal](/project/applet/components/modal/modal.js).

## 注意事项

1. 目前小程序仅支持微信和QQ端. 如果要增加小程序能够发布的平台, 则需要在前端的```app.js```->```global_data.applet```中重写小程序平台的判断方式.
2. 如果后端服务通过```nginx```转发, 那么必须在```nginx```的http配置中设置```underscores_in_headers on```, 否则会导致转发的部分数据丢失.

## 示例

在微信小程序里面搜索"CubeOnline"即可.

## 使用许可

[MIT](LICENSE)
