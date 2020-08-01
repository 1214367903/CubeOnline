class Timer {
    // 这个对象负责启动和结束计时器
    // 调用start开始计时,计时完成后,它会调用page的on_timer_finish返回计时结果
    constructor(page) {
        this.page = page
        this.intervalTimer = null
        this.start_time = null
        this.score = null
        this.is_timeout = false
        this.countdown_sound = wx.createInnerAudioContext()
        this.countdown_sound.src = '/static/countdown.mp3'
    }
    start() {
        this.initialize()
        this.countdown_sound.play()
        this.countdown(this)
    }
    // 下面的方法都是start方法中的某个具体步骤
    // 首先数据初始化
    // 然后倒计时,倒计时结束就开始计时
    // 然后会触发timeout或者stop_timer停止,最终触发on_finish
    // 另外,stop_timer不直接触发on_finish,而是在触发select_punishment之后再触发on_finish
    initialize() {
        this.page.setData({
            'hide_room_page': true,
            'hide_countdown_page': false,
            'hide_timer_page': true,
            'countdown_seconds': 4,
            'current_time': 0.000
        })
        this.score = null
        this.is_timeout = false
    }
    countdown(that) {
        // 这个函数经过倒计时后调用start_timer函数
        if (that.page.data.countdown_seconds <= 1) {
            that.start_timer()
        } else {
            that.page.setData({
                'countdown_seconds': that.page.data.countdown_seconds - 1
            })
            setTimeout(function () {
                that.countdown(that)
            }, 1000)
        }
    }
    start_timer() {
        this.page.setData({
            'hide_countdown_page': true,
            'hide_timer_page': false,
        })
        this.start_time = Date.now()
        const _this = this
        this.intervalTimer = setInterval(function () {
            let current_time = parseInt((Date.now() - _this.start_time) / 1000)
            if (current_time >= _this.page.data.time_limit) {
                _this.on_timeout()
                return
            } else {
                _this.page.setData({
                    'current_time': current_time,
                })
            }
        }, 1000)
    }
    on_stop_timer() {
        if (this.score !== null) {
            return
        }
        clearInterval(this.intervalTimer)
        this.score = (Date.now() - this.start_time) / 1000
        this.page.setData({
            'current_time': this.score
        })
        this.select_punishment()
    }
    select_punishment() {
        this.page.select_punishment()
    }
    select_punishment_callback(e) {
        if (e.detail.index == 1) {
            this.score += 2
        } else if (e.detail.index == 2) {
            this.score = 'DNF'
        }
        this.on_finish()
    }
    on_timeout() {
        clearInterval(this.intervalTimer)
        this.score = 'DNF'
        this.is_timeout = true
        this.page.setData({
            'current_time': 'DNF'
        })
        this.on_finish()
    }
    on_finish() {
        this.page.setData({
            'hide_room_page': false,
            'hide_countdown_page': true,
            'hide_timer_page': true,
        })
        this.page.on_timer_finish(this.score, this.is_timeout)
    }

}


module.exports = Timer