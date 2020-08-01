class EventHandler {
    // 这个对象负责对服务端发来的消息进行解析和处理
    // 调用handle就行了,它会读取消息中的事件类型,然后交由对应方法去处理
    constructor(page) {
        this.page = page
    }
    handle(message) {
        if (typeof (message) === 'string') {
            message = JSON.parse(message)
        }
        // 通过反射找到对应的处理函数去处理事件
        this[message.event](message.data)
    }
    initialize_room(data) {
        this.page.setData({
            'contest_item': data.settings.contest_item,
            'time_limit': data.settings.time_limit,
            'scramble': data.scramble,
            'user_id': data.user_id,
            // 成员需要按照积分从大到小排序,积分一样就按照平均成绩排序,还一样就不管了
            'members': data.members.sort(function (obj1, obj2) {
                if (obj2.point === obj1.point) {
                    return obj1.average - obj2.average
                } else {
                    return obj2.point - obj1.point
                }
            })
        })
    }
    change_state(data) {
        const members = this.page.data.members
        for (let member of members) {
            if (member.id === data.member_id) {
                member.state = data.new_state
                break
            }
        }
        this.page.setData({
            'members': members
        })
    }
    start_round(data){
        this.page.start_round()
    }
    update_score(data) {
        // 更新成绩,顺便确定是否是最好成绩
        const current_scores = this.page.data.current_scores
        const _this = this
        for (let result of current_scores) {
            if (result.id in data.scores) {
                if (data.scores[result.id] !== 'DNF') {
                    result.score = data.scores[result.id]
                    let member = _this.page.get_member(result.id)
                    if (member.best === null) {
                        result.is_pb = true
                    } else if (result.score <= member.best) {
                        result.is_pb = true
                    }
                } else {
                    result.score = 'DNF'
                }
            }
        }
        this.page.setData({
            'current_scores': current_scores
        })
    }
    finish_round(data) {
        // 首先更新本轮成绩的排名和积分
        const current_scores = this.page.data.current_scores
        const members = this.page.data.members
        const ranking = data.ranking
        const _this = this
        for (let result of current_scores) {
            result.rank = ranking[result.id][0]
            result.point = ranking[result.id][1]
        }
        for (let member of members) {
            member.state = 'unready'
            member.tried += 1
            let result = _this.page.get_current_score(member.id)
            member.point += result.point
            if (result.score !== 'DNF') {
                member.average = (member.average * member.solved + result.score) / (member.solved + 1)
                member.solved += 1
                if (result.is_pb) {
                    member.best = result.score
                }
            }
        }
        this.page.setData({
            'members': members.sort(function (obj1, obj2) {
                if (obj2.point === obj1.point) {
                    return obj1.average - obj2.average
                } else {
                    return obj2.point - obj1.point
                }
            }),
            'current_scores': current_scores.sort(function (obj1, obj2) {
                return obj1.rank - obj2.rank
            }),
            'scramble': data.new_scramble,
            'result_page_closeable': true,
        })
        this.page.state = 'preparation'
    }
    add_member(data) {
        const member = data.member_info
        const members = this.page.data.members
        members.push(member)
        this.page.setData({
            'members': members
        })
        this.page.show_notice(`${member.username}加入了房间!`)
    }
    delete_member(data) {
        const members = this.page.data.members
        let member = null
        for (let index in members) {
            if (members[index].id === data.member_id) {
                member = members[index]
                members.splice(index, 1)
                break
            }
        }
        this.page.setData({
            'members': members
        })
        if (member !== null) {
            this.page.show_notice(`${member.username}离开了房间!`)
        }
    }
}


module.exports = EventHandler