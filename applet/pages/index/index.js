const app = getApp()

Page({
    data: {
        // 这几个值决定对应的模态框是否要显示, 默认都是隐藏的
        show_crm: false,
        show_srm: false,
        show_rrm: false,
        show_im: false,
        // 这几个是房间相关的属性
        contest_index: 1,
        contest_items: ['222', '333', '444', '555', '666', '777', '333oh', '333bf', '444bf', '555bf', 'pyram', 'skewb', 'minx', 'sq1', 'clock', '333wf'],
        minute_limit: 0,
        second_limit: 20,
        is_room_private: false,
        room_id: null,
        // 这两属性和公共的信息模态框有关
        information: '',
        can_im_cancel: true,
    },
    // 用户创建房间时使用这个方法, 将用户设置的房间设置等信息传到后台, 从而获取room_id
    request_create_room: function () {
        const time_limit = this.data.minute_limit * 60 + this.data.second_limit
        if (time_limit === 0) {
            this.show_info_modal('别闹了, 还原时限最少要设定为1秒!', false)
            return
        }
        const data = {
            room_settings: {
                contest_item: this.data.contest_items[this.data.contest_index],
                time_limit: time_limit,
                is_room_private: this.data.is_room_private,
            },
            session_id: app.global_data.session_id
        }
        const _this = this
        wx.request({
            url: 'https://' + app.global_data.url + '/room/create',
            data: JSON.stringify(data),
            dataType: 'json',
            method: 'POST',
            success: function (response) {
                _this.hide_loading()
                if (response.data.code === 200) {
                    const room_id = response.data.data.room_id
                    const info = '创建成功! 房间号' + room_id + ', 点击确定进入该房间'
                    _this.setData({
                        'room_id': room_id
                    })
                    _this.show_info_modal(info, true, _this.request_join_room)
                } else {
                    _this.show_info_modal(response.data.message, false)
                }
            },
            fail: function (e) {
                _this.hide_loading()
                const info = '请求失败! 网络不给力啊'
                _this.show_info_modal(info, false)
                console.error(e)
            }
        })
        _this.show_loading()
    },
    // 用户请求获取随机房间时会调用这个方法, 套路和创建房间是一样的
    request_random_room: function () {
        const data = {
            room_settings: {
                contest_item: this.data.contest_items[this.data.contest_index],
            },
            session_id: app.global_data.session_id
        }
        const _this = this
        wx.request({
            url: 'https://' + app.global_data.url + '/room/random',
            data: JSON.stringify(data),
            dataType: 'json',
            method: 'POST',
            success: function (response) {
                _this.hide_loading()
                if (response.data.code === 200) {
                    const room_id = response.data.data.room_id
                    const time_limit = response.data.data.time_limit
                    const info = `为你找到${room_id}号房间, 还原时限${_this.elapsed_time(time_limit,0)}, 点击确定加入该房间`
                    _this.setData({
                        'room_id': room_id
                    })
                    _this.show_info_modal(info, true, _this.request_join_room)
                } else {
                    _this.show_info_modal(response.data.message, false)
                }
            },
            fail: function (e) {
                _this.hide_loading()
                const info = '请求失败! 网络不给力啊'
                _this.show_info_modal(info, false)
                console.error(e)
            }
        })
        _this.show_loading()
    },
    // 要加入房间时调用这个方法, 跳转到room页面
    request_join_room: function () {
        const room_id = this.data.room_id
        if (/^[0-9]{4}$/.test(room_id)) {
            wx.redirectTo({
                url: '../room/room?room_id=' + room_id,
            })
            return
        } else {
            this.show_info_modal('房间号不合法!', false)
            return
        }
    },
    // *************************
    // ###下面是一些公用方法
    // *************************
    // 表单组件的bind:change绑定这个方法, 这样用户改变表单的值时, data中的对应变量也会变
    // 必须在bind的元素上定义data-var_name, 其值为对应的变量名
    on_change: function (e) {
        const field = e.currentTarget.dataset.var_name
        const value = e.detail.value
        this.setData({
            [field]: value,
        })
    },
    // 这个方法用来展示一个指定的模态框
    // 必须在按钮上上定义data-var_name, 其值为data中显示对应模态框的布尔变量名
    show_modal: function (e) {
        // 这个函数显示的模态框都和房间有关,会向服务器发消息
        // 如果用户还没登录,就在这里卡住它
        if (!app.global_data.logged) {
            if (!app.global_data.is_user_authorized) {
                // 如果用户没有授权获取用户信息,就跳转到login页面要求用户授权
                this.show_info_modal('你还没登录, 请先登录', true, function () {
                    wx.navigateTo({
                        url: '../login/login',
                    })
                })
                return
            } else {
                // 否则,就一直等到小程序登录为止
                const _this = this
                const waiting_until_logged = function () {
                    if (app.global_data.logged) {
                        _this.hide_loading()
                        _this.show_modal(e)
                    } else {
                        _this.sleep(100).then(function () {
                            waiting_until_logged()
                        })
                    }
                }
                this.show_loading()
                waiting_until_logged()
                return
            }
        }
        const field = e.currentTarget.dataset.var_name
        this.setData({
            [field]: true,
        })
    },
    // 这个方法弹出一个展示信息的模态框
    // 可以通过参数设置是否允许取消模态框, 以及关闭模态框之后的回调
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
    // 这个方法返回一个定时器,调用定时器的then方法执行回调
    sleep: function (time) {
        return new Promise(resolve => setTimeout(resolve, time))
    },
    // 把数字格式的时间转化为分:秒的形式
    elapsed_time: function (value) {
        if (value === 'DNF') {
            return value
        } else if (value < 60) {
            return value + '秒'
        } else {
            const minute = parseInt(value / 60)
            let second = (value % 60)
            if (second < 10) {
                second = '0' + second
            }
            return `${minute}分${second}秒`
        }
    },
    // 通过这个函数跳转到about界面
    show_about_page: function () {
        wx.navigateTo({
            url: '../about/about',
        })
    },
    onLoad: function () {
        // wx.navigateTo({
        //     url: '../room/room?room_id=test',
        // })
        // onload什么都不做了,等用户在进行房间相关操作时,再去提示它登录
        // if (!app.global_data.logged) {
        //     wx.redirectTo({
        //         url: '../login/login',
        //     })
        //     return
        // }
        // if (app.global_data.session_id !== null) {
        //     return
        // }
        // const sleep = function (time) {
        //     return new Promise(resolve => setTimeout(resolve, time))
        // }
        // const _this = this
        // const waiting_for_login = function () {
        //     if (app.global_data.failed_to_login) {
        //         _this.hide_loading()
        //         _this.show_info_modal('用户登录失败! 关闭小程序重进试试', false)
        //     } else if (app.global_data.session_id !== null) {
        //         _this.hide_loading()
        //     } else {
        //         sleep(100).then(function () {
        //             waiting_for_login()
        //         })
        //     }
        // }
        // this.show_loading()
        // waiting_for_login()
    },
    onShow: function () {
        wx.showShareMenu({
            withShareTicket: true,
            showShareItems: ['qq', 'qzone', 'wechatFriends', 'wechatMoment']
        })
    },
    onShareAppMessage: function () {
        // QQ小程序非得加上这个, 不然老是审核不通过
        if (app.global_data.applet !== 'qq') {
            return
        }
        qq.showShareMenu({
            showShareItems: ['qq', 'qzone', 'wechatFriends', 'wechatMoment']
        })
    }
})