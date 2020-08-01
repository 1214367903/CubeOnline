const app = getApp()


Page({
    data: {},
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