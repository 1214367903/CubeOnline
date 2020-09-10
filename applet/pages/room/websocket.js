// 每隔59秒ping一次
const PING_INTERVAL = 15 * 1000


class WebSocketClient {
    constructor(args, callbacks) {
        this.socket = wx.connectSocket(args)
        this.callbacks = callbacks
        // 首先对socket进行改造, 把它被动触发的几个事件绑定到自己的方法上
        const _this = this
        this.socket.onOpen(function (header, profile) {
            _this.on_open(_this, header, profile)
        })
        this.socket.onClose(function (code, reason) {
            _this.on_close(_this, code, reason)
        })
        this.socket.onError(function (error_message) {
            _this.on_error(_this, error_message)
        })
        this.socket.onMessage(function (data) {
            _this.on_message(_this, data)
        })
        // 这里设置几个心跳相关的参数
        this.last_ping_flag = null
        // 这里设置ping定时器的目的是,可以在任何位置任何时候把ping任务停掉,方便关连接跑路
        this.ping_timer = null
        this.is_ping_failed = false
    }
    start_heart_beat(ws_client) {
        // 在开启连接之后调用这个方法开始心跳
        // 心跳的机制是,把时间戳发给服务器,同时也存入last_ping_flag这个变量中
        // 服务器收到之后再原封不动地发回来,这时如果和本地的last_ping_flag是一个值,就把这个值消了
        // ping发送成功后,等一段间隔继续发
        // 如果此时last_ping_flag没消,就说明有问题,没收到pong,可以close了
        const heart_beat = function (ws_client) {
            if (ws_client.last_ping_flag !== null) {
                ws_client.is_ping_failed = true
                ws_client.close(3000, 'Did not receive pong data')
                return
            } else {
                ws_client.last_ping_flag = new Date().getTime()
                const data = {
                    'ping': ws_client.last_ping_flag
                }
                const success = function () {
                    ws_client.ping_timer = setTimeout(function () {
                        heart_beat(ws_client)
                    }, PING_INTERVAL)
                }
                ws_client.send(data, success)
            }
        }
        // 需要注意的是,心跳是on_open的时候开始的
        // 因此,调用这个方法不会立即发送ping包,而是在一个ping延迟之后才开始发送
        ws_client.ping_timer = setTimeout(function () {
            heart_beat(ws_client)
        }, PING_INTERVAL)
    }
    stop_heart_beat(ws_client) {
        ws_client.last_ping_flag = null
        if (ws_client.ping_timer) {
            clearTimeout(ws_client.ping_timer);
            ws_client.ping_timer = null;
        }
    }
    send(data, success, fail, complete) {
        if (typeof (data) !== 'string') {
            data = JSON.stringify(data)
        }
        // 这里给fail加个回调, 如果发送失败就关闭连接
        const _this = this
        const fail_func = function (res) {
            res = res || ''
            _this.close(3000, '发送信息失败:' + JSON.stringify(res))
            if (fail !== undefined) {
                fail(res)
            }
        }
        this.socket.send({
            'data': data,
            'success': success,
            'fail': fail_func,
            'complete': complete
        })
    }
    close(code, reason, success, fail, complete) {
        // 如果不是正常关闭,code的值必须在3000-4999之间,否则会关闭失败,还不提示错误
        if (typeof (reason) !== 'string') {
            reason = JSON.stringify(reason)
        }
        this.socket.close({
            'code': code,
            'reason': reason,
            'success': success,
            'fail': fail,
            'complete': complete
        })
    }
    on_open(that, header, profile) {
        that.start_heart_beat(that)
        that.callbacks.open_cb(header, profile)
    }
    on_close(that, message) {
        that.stop_heart_beat(that)
        that.callbacks.close_cb(message)
    }
    on_error(that, error_message) {
        that.callbacks.error_cb(error_message)
    }
    on_message(that, data) {
        // 来消息之后,如果是pong包,就把之前的ping消掉
        const value = JSON.parse(data.data).pong
        if (value !== undefined) {
            if (value === that.last_ping_flag) {
                that.last_ping_flag = null
            }
            return
        }
        that.callbacks.message_cb(data.data)
    }
}


module.exports = WebSocketClient