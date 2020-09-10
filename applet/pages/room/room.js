const app = getApp()

const WebSocketClient = require('./websocket')
const Timer = require('./timer')
const EventHandler = require('./handler')

Page({
    data: {
        // 这三样是给公共的信息模态框用的
        information: '',
        show_im: false,
        can_im_cancel: true,
        // 信息栏显示的信息
        notice_bar_content: '暂时没有通告',
        // 这是三大外挂,负责长连接,响应服务端的事件,以及计时
        websocket: null,
        event_handler: null,
        timer: null,
        // 房间设置和用户信息等等
        contest_item: null,
        time_limit: null,
        show_sm: false,
        scramble: null,
        scramble_font_size: 36,
        scramble_area_height: 160,
        user_id: null,
        // 用户界面用的,也存放用户的数据
        member_title_items: [
            '积分',
            '最好',
            '平均',
            '复原',
            '尝试',
        ],
        members: [],
        // 下面这几个是给计时界面用的
        hide_room_page: false,
        hide_countdown_page: true,
        hide_timer_page: true,
        countdown_seconds: 4,
        current_time: 0,
        punishments: [{
                text: '无惩罚',
                value: 0
            },
            {
                text: '+2',
                type: 'warn',
                value: 1
            },
            {
                text: 'DNF',
                type: 'warn',
                value: 2
            }
        ],
        show_pas: false,
        // 展示赛果用的,也储存本轮比赛成绩
        show_result_page: false,
        result_page_closeable: false,
        current_scores: []
    },
    // 这个属性储存房间当前的状态,有preparation和cubing两种
    state: 'preparation',
    // *************************
    // ###下面几个方法负责控制比赛流程
    // *************************
    on_user_ready: function () {
        // 当用户准备好时，它会点击按钮触发这个事件，然后与后台通信
        if (this.get_member().state === 'ready') {
            const info = '你已经点了准备, 等所有人都准备好后, 比赛会自动开始'
            this.show_info_modal(info, false)
            return
        }
        const info = '是否打乱并观察完毕'
        const _this = this
        const cb = function () {
            _this.show_loading()
            _this.send_message('on_ready', {}, null, null, _this.hide_loading)
        }
        this.show_info_modal(info, true, cb)
    },
    start_round: function () {
        const current_scores = []
        for (let member of this.data.members) {
            current_scores.push({
                id: member.id,
                username: member.username,
                usericon: member.usericon,
                score: '...',
                is_pb: false,
                rank: '...',
                point: '...',
            })
        }
        this.setData({
            'current_scores': current_scores,
        })
        this.state = 'cubing'
        this.data.timer.start()
    },
    stop_timer: function () {
        this.data.timer.on_stop_timer()
    },
    select_punishment: function () {
        this.setData({
            show_pas: true,
        })
    },
    select_punishment_callback: function (e) {
        this.setData({
            show_pas: false,
        })
        this.data.timer.select_punishment_callback(e)
    },
    on_timer_finish: function (score, is_timeout) {
        // 计时结束后,上传成绩,然后进入比赛结果界面
        this.send_message('upload_score', {
            'score': score
        })
        const _this = this
        const show_result = function () {
            _this.setData({
                'show_result_page': true,
            })
            // 如果当前还没比完,先隐藏掉关闭赛果页的按钮
            if (_this.state === 'cubing') {
                _this.setData({
                    'result_page_closeable': false
                })
            }
        }
        if (is_timeout) {
            this.show_info_modal('你已超时, 本轮成绩记为DNF', false, show_result)
        } else {
            show_result()
        }

    },
    close_result_page: function () {
        this.setData({
            'show_result_page': false,
        })
    },
    // *************************
    // ###下面是一些公用方法
    // *************************
    show_info_modal: function (info, can_cancel = true, confirm_cb = null, cancel_cb = null) {
        this.setData({
            information: info,
            show_im: true,
            can_im_cancel: can_cancel
        })
        this.modal_confirm_callback = confirm_cb || function () {}
        this.modal_cancel_callback = cancel_cb || function () {}
    },
    // 给上面的show_info_modal的回调, 工具人
    modal_confirm_callback: function () {},
    modal_cancel_callback: function () {},
    show_loading: function (text = 'Loading') {
        wx.showLoading({
            title: text,
            mask: true
        })
    },
    hide_loading: function () {
        wx.hideLoading()
    },
    show_modal: function (e) {
        const field = e.currentTarget.dataset.var_name
        this.setData({
            [field]: true,
        })
    },
    notice_sound: wx.createInnerAudioContext(),
    show_notice: function (notice) {
        this.notice_sound.src = '/static/notice.mp3'
        this.setData({
            'notice_bar_content': notice
        })
        this.notice_sound.play()
    },
    on_change: function (e) {
        const field = e.currentTarget.dataset.var_name
        const value = e.detail.value
        this.setData({
            [field]: value,
        })
    },
    send_message: function (event, data, success, fail, complete) {
        // 后面三个回调函数可以不要,但是事件类型和数据是必须的
        const message = {
            'event': event,
            'data': data
        }
        this.data.websocket.send(JSON.stringify(message), success, fail, complete)
    },
    get_member: function (id = this.data.user_id) {
        // 这个函数返回members列表中的某个member
        // 默认是自己,也可以通过id指定其他人
        // 需要注意的是,返回的member数据是只读的,如果需要修改,还得用setData
        for (let member of this.data.members) {
            if (member.id === id) {
                return member
            }
        }
    },
    get_current_score: function (id = this.data.user_id) {
        // 这个函数返回members列表中的某个member的成绩
        // 默认是自己,也可以通过id指定其他人
        // 需要注意的是,返回的member数据是只读的,如果需要修改,还得用setData
        for (let result of this.data.current_scores) {
            if (result.id === id) {
                return result
            }
        }
    },
    left_room: function () {
        const info = "是否返回主页?"
        const callback = function () {
            wx.redirectTo({
                url: '../index/index',
            })
        }
        this.show_info_modal(info, true, callback)
    },
    onLoad: function (options) {
        // 第一步,读取room_id和session_id
        const room_id = options.room_id
        const session_id = app.global_data.session_id

        // 第二步,创建页面标题并显示loading,增强用户体验
        wx.setNavigationBarTitle({
            title: `${room_id}号房间`,
        })
        this.show_loading()

        // 第三步,创建长连接,这个连接如果失败,就会触发on_close回到主界面
        // 无论是否成功,都会隐藏loading
        const ws_args = {
            url: `wss://${app.global_data.url}/room/join`,
            header: {
                'content-type': 'application/json',
                'room_id': room_id,
                'session_id': session_id
            },
            fail: this._on_close,
            complete: this.hide_loading
        }
        const ws_callbacks = {
            open_cb: this._on_open,
            close_cb: this._on_close,
            error_cb: this._on_error,
            message_cb: this._on_message,
        }
        const websocket = new WebSocketClient(
            ws_args, ws_callbacks
        )

        // 第四步,new一些其他需要的对象,最后将这些数据存入data        
        const timer = new Timer(this)
        const event_handler = new EventHandler(this)
        this.setData({
            'websocket': websocket,
            'timer': timer,
            'event_handler': event_handler
        })
    },
    onUnload: function () {
        this.data.websocket.close(1000, 'member left')
    },
    onShow: function () {
        wx.hideHomeButton()
        wx.showShareMenu({
            withShareTicket: true,
            showShareItems: ['qq', 'qzone', 'wechatFriends', 'wechatMoment']
        })
    },
    onShareAppMessage: function () {
        // QQ小程序非得往这个方法里面写内容, 不然老是审核不通过
        if (app.global_data.applet !== 'qq') {
            return
        }
        qq.showShareMenu({
            showShareItems: ['qq', 'qzone', 'wechatFriends', 'wechatMoment']
        })
    },
    // 下面的四个方法是为websocket准备的, 在websocket触发对应事件后, 会调用这些相应的回调
    _on_open: function (header, profile) {},
    _on_close: function (message) {
        // 虽然官方说的是会给出code和reason两个参数,但是实际上只获得一个参数
        let info = `连接已断开, 信息:"${message.reason}", 现在回到主页`
        if (this.data.websocket.is_ping_failed) {
            info = '你的网络似乎不稳定...' + info
        }
        const callback = function () {
            wx.redirectTo({
                url: '../index/index',
            })
        }
        this.show_info_modal(info, false, callback)
    },
    _on_error: function (error_message) {
        console.error('长连接发生错误, 信息如下:')
        console.log(error_message)
        this.data.websocket.close(3000, error_message.errMsg)
    },
    _on_message: function (message) {
        this.data.event_handler.handle(message)
    },
})