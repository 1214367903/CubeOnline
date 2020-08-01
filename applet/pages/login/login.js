const app = getApp()

Page({
    data: {},
    get_user_info: function (e) {
        if (this.has_user_info || app.global_data.is_user_authorized) {
            wx.redirectTo({
                url: '../index/index',
            })
            return
        } else if (e.detail.userInfo === undefined) {
            return
        }
        this.has_user_info = true
        app.on_get_user_info(e.detail.userInfo)
        wx.redirectTo({
            url: '../index/index',
        })
    },
    onLoad: function () {
        if (app.global_data.logged) {
            wx.redirectTo({
                url: '../index/index',
            })
        }
    },
    onShow: function () {
        wx.hideHomeButton()
    },
    onShareAppMessage: function () {
        // QQ小程序非得加上这个, 不然老是审核不通过
        if (app.global_data.applet !== 'qq') {
            return
        }
        qq.showShareMenu({
            showShareItems: ['qq', 'qzone', 'wechatFriends', 'wechatMoment']
        })
    },
    has_user_info: false
})