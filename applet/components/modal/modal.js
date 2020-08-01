Component({

    //  组件的属性列表
    properties: {
        //是否显示modal
        show: {
            type: Boolean,
            value: false
        },
        //modal的高度
        height: {
            type: String,
            value: '80%'
        },
        //是否展示确定和取消按钮
        show_buttons: {
            type: Boolean,
            value: true
        },
        // 是否显示取消按钮
        can_cancel: {
            type: Boolean,
            value: true
        }
    },

    /**
     * 组件的初始数据
     */
    data: {

    },

    /**
     * 组件的方法列表
     */
    methods: {
        // 点击蒙层没什么用,先注销了
        clickMask() {
            // this.setData({show: false})
        },

        cancel() {
            this.setData({
                show: false
            })
            this.triggerEvent('cancel')
        },

        confirm() {
            this.setData({
                show: false
            })
            this.triggerEvent('confirm')
        }
    }
})