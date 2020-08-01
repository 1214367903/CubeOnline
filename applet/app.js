//app.js
App({
    onLaunch: function () {
        // 尝试读取本地的session_id
        this.global_data.session_id = wx.getStorageSync('session_id') || null
        const _this = this
        wx.getSetting({
            success: res => {
                if (res.authSetting['scope.userInfo']) {
                    // 已经授权，可以直接调用 getUserInfo 获取头像昵称，不会弹框
                    _this.global_data.is_user_authorized = true
                    wx.getUserInfo({
                        success: function (res) {
                            _this.on_get_user_info(res.userInfo)
                        },
                        fail: function (res) {
                            console.error('获取用户信息失败, 返回值如下:')
                            console.log(res)
                        }
                    })
                }
            }
        })
    },
    on_get_user_info: function (user_info) {
        // 获取用户数据只是登录的第一步,在获取完用户数据后,走完这个函数,才算登录完成
        // 这个函数将用户数据发送给后台,然后获取session_id
        this.global_data.user_info = {
            username: user_info.nickName,
            usericon: user_info.avatarUrl,
        }
        const _this = this
        const user_data = {
            username: user_info.nickName,
            usericon: user_info.avatarUrl,
            applet: _this.global_data.applet
        }
        // 调用这个函数,把数据发到服务器,获取session_id
        const login = function () {
            wx.request({
                url: 'https://' + _this.global_data.url + '/user/login',
                data: JSON.stringify(user_data),
                dataType: 'json',
                method: 'POST',
                success: function (response) {
                    if (response.data.code === 200) {
                        console.log('小程序登录流程已完成')
                        const session_id = response.data.data.session_id
                        _this.global_data.session_id = session_id
                        _this.global_data.logged = true
                        wx.setStorageSync('session_id', session_id)
                    } else {
                        console.error('登录请求被服务器拒绝,错误信息:')
                        console.log(response.data.message)
                        return
                    }
                },
                fail: function (e) {
                    console.error('服务端登录失败,错误信息:')
                    console.log(e)
                    return
                },
            })
        }
        // 根据本地session_id的情况把用户数据补全,补全后调用上面的login函数发数据
        if (_this.global_data.session_id !== null) {
            user_data['has_session_id'] = true
            user_data['session_id'] = _this.global_data.session_id
            login()
        } else {
            user_data['has_session_id'] = false
            wx.login({
                success: function (res) {
                    user_data['code'] = res.code
                    login()
                },
                fail: function (res) {
                    console.error('调用wx.login失败, 返回值如下:')
                    console.log(res)
                }
            })
        }
    },
    global_data: {
        user_info: null,
        session_id: null,
        logged: false,
        is_user_authorized: false,
        //在这里填入你的后端url
        url: '',
        applet: typeof (qq) === "undefined" ? "wx" : "qq"
    }
})