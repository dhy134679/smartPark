<template>
  <view class="page">
    <view class="card" v-if="user">
      <view class="title">个人信息</view>
      <view>姓名：{{ user.name }}</view>
      <view>手机号：{{ user.phone }}</view>
      <view>角色：{{ user.role }}</view>
      <button class="ghost" @click="logout">退出登录</button>
    </view>

    <view class="card" v-if="user && user.role !== 'guest'">
      <view class="title">绑定车辆</view>
      <view v-for="item in vehicles" :key="item.id" class="vehicle-item">
        <view>
          <view class="plate">{{ item.plate_number }}</view>
          <view>{{ item.brand || '-' }} / {{ item.color || '-' }}</view>
        </view>
        <button size="mini" type="warn" @click="removeVehicle(item.id)">解绑</button>
      </view>
      <view class="form">
        <input class="input" v-model="vehicleForm.plate_number" placeholder="车牌号" />
        <input class="input" v-model="vehicleForm.brand" placeholder="品牌" />
        <input class="input" v-model="vehicleForm.color" placeholder="颜色" />
        <label class="checkbox">
          <switch :checked="vehicleForm.is_resident" @change="vehicleForm.is_resident = $event.detail.value" />
          小区车辆
        </label>
        <button type="primary" @click="addVehicle">添加车辆</button>
      </view>
    </view>

    <view class="card" v-if="user && user.role !== 'guest' && user.role !== 'admin'">
      <view class="title">我的车位与共享设置</view>
      <view v-if="mySpots.length === 0" class="empty">暂无名下车位</view>
      <view v-for="(spot, index) in mySpots" :key="spot.id" class="spot-card">
        <view class="spot-header">
          <text class="plate">车位: {{ spot.spot_number }} ({{ spot.zone }}区)</text>
          <switch
            :checked="spot.is_shared"
            @change="(event) => toggleShare(index, event.detail.value)"
            color="#2a82e4"
            style="transform: scale(0.8)"
          />
        </view>
        <view v-if="spot.is_shared" class="share-opts">
          <view class="share-row">
            <text>共享开始时间:</text>
            <input v-model="spot.shared_start" placeholder="YYYY-MM-DD HH:mm:ss" class="share-input" />
          </view>
          <view class="share-row">
            <text>共享结束时间:</text>
            <input v-model="spot.shared_end" placeholder="YYYY-MM-DD HH:mm:ss" class="share-input" />
          </view>
          <button size="mini" type="primary" @click="saveShare(spot)" style="margin-top: 10rpx;">保存时间设置</button>
        </view>
      </view>
    </view>

    <view class="card" v-if="user && user.role !== 'guest' && user.role !== 'admin'">
      <view class="title">我的找平收益明细</view>
      <view class="income-total">总计：￥{{ myIncome.total_income || '0.00' }}</view>
      <view v-for="(log, idx) in myIncome.recent_details" :key="idx" class="income-row">
        <text>{{ log.time }}</text>
        <text>{{ log.plate_number }}</text>
        <text class="income-plus">+{{ log.amount }}</text>
      </view>
      <view v-if="!myIncome.recent_details || myIncome.recent_details.length === 0" class="empty">
        暂无收益记录
      </view>
    </view>

    <view class="card quick-links">
      <button @click="openPage('/pages/records/records')">停车记录</button>
      <button @click="openPage('/pages/simulate/simulate')">模拟出入</button>
    </view>
  </view>
</template>

<script>
import { request } from '@/utils/request.js'
import { clearAuth } from '@/utils/auth.js'

export default {
  data() {
    return {
      user: null,
      vehicles: [],
      mySpots: [],
      myIncome: { total_income: 0, recent_details: [] },
      vehicleForm: {
        plate_number: '',
        brand: '',
        color: '',
        is_resident: true
      }
    }
  },
  onShow() {
    this.loadData()
  },
  methods: {
    toggleShare(index, value) {
      if (value) {
        const now = new Date()
        const startStr = now.toISOString().replace('T', ' ').slice(0, 19)
        const endStr = new Date(now.getTime() + 8 * 3600 * 1000)
          .toISOString()
          .replace('T', ' ')
          .slice(0, 19)
        this.mySpots[index].shared_start = startStr
        this.mySpots[index].shared_end = endStr
      } else {
        this.mySpots[index].shared_start = null
        this.mySpots[index].shared_end = null
      }
      this.mySpots[index].is_shared = value
      this.saveShare(this.mySpots[index])
    },
    async saveShare(spot) {
      try {
        await request({
          url: `/spots/${spot.id}/share`,
          method: 'PUT',
          data: {
            is_shared: spot.is_shared,
            shared_start: spot.shared_start || null,
            shared_end: spot.shared_end || null
          }
        })
        uni.showToast({ title: '共享设置已保存', icon: 'success' })
      } catch (error) {
        uni.showToast({ title: '设置失败', icon: 'none' })
      }
    },
    async loadData() {
      try {
        const [profile, vehicles] = await Promise.all([
          request({ url: '/auth/profile' }),
          request({ url: '/vehicles' })
        ])
        this.user = profile.data.user
        this.vehicles = vehicles.data.items

        if (this.user.role !== 'guest' && this.user.role !== 'admin') {
          const [spotsRes, incomeRes] = await Promise.all([
            request({ url: '/spots/my' }),
            request({ url: '/spots/my/income' })
          ])
          this.mySpots = spotsRes.data.items
          this.myIncome = incomeRes.data
        }
      } catch (error) {
        console.error(error)
        if (error?.statusCode === 401) {
          this.logout()
        }
      }
    },
    async addVehicle() {
      if (!this.vehicleForm.plate_number) {
        uni.showToast({ title: '请输入车牌号', icon: 'none' })
        return
      }
      try {
        await request({ url: '/vehicles', method: 'POST', data: this.vehicleForm })
        uni.showToast({ title: '添加成功', icon: 'success' })
        this.vehicleForm = { plate_number: '', brand: '', color: '', is_resident: true }
        this.loadData()
      } catch (error) {
        console.error(error)
      }
    },
    async removeVehicle(id) {
      try {
        await request({ url: `/vehicles/${id}`, method: 'DELETE' })
        this.loadData()
      } catch (error) {
        console.error(error)
      }
    },
    logout() {
      clearAuth()
      uni.reLaunch({ url: '/pages/login/login' })
    },
    openPage(url) {
      uni.navigateTo({ url })
    }
  }
}
</script>

<style scoped>
.page {
  padding: 24rpx;
}

.card {
  background: #fff;
  border-radius: 18rpx;
  padding: 24rpx;
  margin-bottom: 24rpx;
}

.title {
  font-size: 32rpx;
  margin-bottom: 16rpx;
}

.vehicle-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #f0f0f0;
  padding: 16rpx 0;
}

.vehicle-item:last-child {
  border-bottom: none;
}

.input {
  background: #f4f6fb;
  border-radius: 12rpx;
  padding: 16rpx;
  margin-bottom: 12rpx;
}

.checkbox {
  display: flex;
  align-items: center;
  margin-bottom: 12rpx;
}

.quick-links button {
  margin-right: 16rpx;
}

.ghost {
  margin-top: 20rpx;
  color: #ff5c5c;
}

.spot-card {
  padding: 20rpx;
  background: #fafafa;
  border-radius: 12rpx;
  margin-bottom: 20rpx;
  border: 1px solid #eee;
}

.spot-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12rpx;
}

.share-opts {
  background: #fdfdfd;
  padding: 16rpx;
  border-radius: 8rpx;
  margin-top: 10rpx;
}

.share-row {
  display: flex;
  align-items: center;
  font-size: 26rpx;
  margin-bottom: 16rpx;
}

.share-input {
  flex: 1;
  margin-left: 20rpx;
  border-bottom: 1px solid #ddd;
  padding: 4rpx;
  font-size: 24rpx;
}

.income-total {
  font-size: 36rpx;
  color: #ff5c5c;
  font-weight: 600;
  margin-bottom: 20rpx;
}

.income-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16rpx 0;
  border-bottom: 1px solid #f2f2f2;
  font-size: 26rpx;
}

.income-row:last-child {
  border-bottom: none;
}

.income-plus {
  color: #4cd964;
}

.empty {
  color: #999;
  font-size: 24rpx;
}
</style>
