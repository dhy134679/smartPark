<template>
  <view class="page">
    <view class="card" v-if="user">
      <view class="title">个人中心</view>
      <view class="form" v-if="!isAdmin">
        <input class="input" v-model.trim="profileForm.name" placeholder="姓名" />
        <input class="input" v-model.trim="profileForm.phone" placeholder="手机号" />
        <button size="mini" type="primary" @click="saveProfile">保存资料</button>
      </view>
      <view v-else>
        <view>管理员账号：{{ user.name }}</view>
        <view>手机号：{{ user.phone }}</view>
      </view>
      <button class="ghost" @click="logout">退出登录</button>
    </view>

    <view class="card" v-if="user">
      <view class="title">修改密码</view>
      <input class="input" password v-model="pwdForm.old_password" placeholder="原密码" />
      <input class="input" password v-model="pwdForm.new_password" placeholder="新密码（至少6位）" />
      <button size="mini" type="primary" @click="changePassword">更新密码</button>
    </view>

    <!-- 模拟钱包功能区 -->
    <view class="card wallet-card" v-if="user && !isAdmin && user.role !== 'guest'">
      <view class="wallet-header">
        <view class="title wallet-title">我的钱包</view>
        <view class="balance">
          <text class="currency">¥</text>
          <text class="amount">88.00</text>
        </view>
      </view>
      <view class="wallet-actions">
        <button size="mini" class="btn-recharge" @click="simulateRecharge">充值</button>
        <button size="mini" class="btn-bill" @click="simulateBill">账单记录</button>
      </view>
    </view>

    <view class="card" v-if="user && !isAdmin && user.role !== 'guest'">
      <view class="title">绑定车辆</view>
      <view v-for="item in vehicles" :key="item.id" class="row">
        <text>{{ item.plate_number }} {{ item.brand || '-' }} {{ item.color || '-' }}</text>
        <button size="mini" type="warn" @click="removeVehicle(item.id)">删除</button>
      </view>
      <input class="input" v-model="vehicleForm.plate_number" placeholder="车牌号" />
      <input class="input" v-model="vehicleForm.brand" placeholder="品牌" />
      <input class="input" v-model="vehicleForm.color" placeholder="颜色" />
      <button size="mini" type="primary" @click="addVehicle">添加车辆</button>
    </view>

    <view class="card" v-if="user && !isAdmin && user.role !== 'guest'">
      <view class="title">车位变更申请（需管理员审批）</view>
      <view class="hint">当前车位：{{ mySpots[0]?.spot_number || '暂无' }}</view>
      <picker :range="actions" @change="onActionChange">
        <view class="picker">申请类型：{{ actionLabel }}</view>
      </picker>
      <picker :range="zones" @change="onZoneChange" v-if="spotAction !== 'release'">
        <view class="picker">目标区域：{{ targetZone || '请选择区域' }}</view>
      </picker>
      <picker :range="targetSpotOptions" range-key="label" @change="onSpotChange" v-if="spotAction !== 'release'">
        <view class="picker">目标车位：{{ targetSpotLabel }}</view>
      </picker>
      <input class="input" v-model.trim="requestReason" placeholder="申请原因（可选）" />
      <button size="mini" type="primary" @click="submitSpotRequest">提交申请</button>

      <view class="subtitle">我的申请记录</view>
      <view v-for="item in myRequests" :key="item.id" class="req-item">
        <text>#{{ item.id }} {{ actionText(item.action) }} {{ statusText(item.status) }}</text>
        <text class="muted">{{ item.target_zone ? item.target_zone + '区' : '-' }} / {{ item.target_spot_id || '-' }}</text>
      </view>
      <view v-if="myRequests.length === 0" class="empty">暂无申请记录</view>
    </view>

    <view class="card" v-if="isAdmin">
      <view class="title">审批中心</view>
      <view class="row" v-for="item in pendingRequests" :key="item.id">
        <view>
          <view>申请人ID: {{ item.user_id }} | {{ actionText(item.action) }}</view>
          <view class="muted">目标区域: {{ item.target_zone || '-' }}，目标车位ID: {{ item.target_spot_id || '-' }}</view>
        </view>
        <view>
          <button size="mini" type="primary" @click="reviewRequest(item.id, 'approved')">通过</button>
          <button size="mini" type="warn" @click="reviewRequest(item.id, 'rejected')">拒绝</button>
        </view>
      </view>
      <view v-if="pendingRequests.length === 0" class="empty">暂无待审批申请</view>
    </view>
  </view>
</template>

<script>
import { request } from '@/utils/request.js'
import { clearAuth, getToken, saveAuth } from '@/utils/auth.js'

export default {
  data() {
    return {
      user: null,
      vehicles: [],
      mySpots: [],
      allSpots: [],
      myRequests: [],
      pendingRequests: [],
      profileForm: { name: '', phone: '' },
      pwdForm: { old_password: '', new_password: '' },
      vehicleForm: { plate_number: '', brand: '', color: '', is_resident: true },
      actions: ['新增车位', '更换车位', '释放车位'],
      spotAction: 'assign',
      zones: ['A', 'B', 'C'],
      targetZone: '',
      targetSpotId: null,
      requestReason: ''
    }
  },
  computed: {
    isAdmin() {
      return this.user && this.user.role === 'admin'
    },
    actionLabel() {
      return this.actionText(this.spotAction)
    },
    targetSpotOptions() {
      return this.allSpots
        .filter((item) => item.status === 'free')
        .filter((item) => !this.targetZone || item.zone === this.targetZone)
        .map((item) => ({ id: item.id, label: `${item.spot_number} (${item.zone}区)` }))
    },
    targetSpotLabel() {
      const target = this.targetSpotOptions.find((item) => item.id === this.targetSpotId)
      return target ? target.label : '请选择目标车位'
    }
  },
  onShow() {
    this.loadData()
  },
  methods: {
    actionText(action) {
      if (action === 'assign') return '新增车位'
      if (action === 'release') return '释放车位'
      return '更换车位'
    },
    statusText(status) {
      if (status === 'approved') return '（已通过）'
      if (status === 'rejected') return '（已拒绝）'
      return '（待审批）'
    },
    onActionChange(event) {
      const idx = Number(event.detail.value)
      const map = ['assign', 'change', 'release']
      this.spotAction = map[idx] || 'assign'
    },
    onZoneChange(event) {
      const idx = Number(event.detail.value)
      this.targetZone = this.zones[idx] || ''
      this.targetSpotId = null
    },
    simulateRecharge() {
      uni.showToast({ title: '模拟支付暂未开通真实充值', icon: 'none' })
    },
    simulateBill() {
      uni.showToast({ title: '暂无更多账单记录', icon: 'none' })
    },
    onSpotChange(event) {
      const idx = Number(event.detail.value)
      const target = this.targetSpotOptions[idx]
      this.targetSpotId = target ? target.id : null
    },
    async loadData() {
      try {
        const profile = await request({ url: '/auth/profile' })
        this.user = profile.data.user
        this.profileForm = { name: this.user.name, phone: this.user.phone }
        if (this.isAdmin) {
          const reqRes = await request({ url: '/spots/change-requests?status=pending' })
          this.pendingRequests = reqRes.data.items || []
          return
        }

        if (this.user.role !== 'guest') {
          const [vehiclesRes, mySpotsRes, spotsRes, myReqRes] = await Promise.all([
            request({ url: '/vehicles' }),
            request({ url: '/spots/my' }),
            request({ url: '/spots' }),
            request({ url: '/spots/change-requests/my' })
          ])
          this.vehicles = vehiclesRes.data.items || []
          this.mySpots = mySpotsRes.data.items || []
          this.allSpots = spotsRes.data.items || []
          this.myRequests = myReqRes.data.items || []
        }
      } catch (error) {
        console.error(error)
        if (error?.statusCode === 401) this.logout()
      }
    },
    async saveProfile() {
      try {
        const res = await request({ url: '/auth/profile', method: 'PUT', data: this.profileForm })
        this.user = res.data.user
        saveAuth(getToken(), this.user)
        uni.showToast({ title: '资料已更新', icon: 'success' })
      } catch (error) {
        console.error(error)
      }
    },
    async changePassword() {
      try {
        await request({ url: '/auth/change-password', method: 'PUT', data: this.pwdForm })
        this.pwdForm = { old_password: '', new_password: '' }
        uni.showToast({ title: '密码已更新', icon: 'success' })
      } catch (error) {
        console.error(error)
      }
    },
    async addVehicle() {
      if (!this.vehicleForm.plate_number) {
        uni.showToast({ title: '请输入车牌号', icon: 'none' })
        return
      }
      await request({ url: '/vehicles', method: 'POST', data: this.vehicleForm })
      this.vehicleForm = { plate_number: '', brand: '', color: '', is_resident: true }
      await this.loadData()
    },
    async removeVehicle(vehicleId) {
      await request({ url: `/vehicles/${vehicleId}`, method: 'DELETE' })
      await this.loadData()
    },
    async submitSpotRequest() {
      if (this.spotAction !== 'release' && !this.targetSpotId) {
        uni.showToast({ title: '请选择目标车位', icon: 'none' })
        return
      }
      await request({
        url: '/spots/change-requests',
        method: 'POST',
        data: {
          action: this.spotAction,
          target_spot_id: this.spotAction === 'release' ? null : this.targetSpotId,
          target_zone: this.spotAction === 'release' ? null : this.targetZone,
          reason: this.requestReason || null
        }
      })
      uni.showToast({ title: '申请已提交', icon: 'success' })
      this.requestReason = ''
      this.targetSpotId = null
      await this.loadData()
    },
    async reviewRequest(requestId, status) {
      await request({
        url: `/spots/change-requests/${requestId}/review`,
        method: 'PUT',
        data: { status }
      })
      uni.showToast({ title: '审批完成', icon: 'success' })
      await this.loadData()
    },
    logout() {
      clearAuth()
      uni.reLaunch({ url: '/pages/login/login' })
    }
  }
}
</script>

<style scoped>
.page { padding: 24rpx; }
.card { background: #fff; border-radius: 16rpx; padding: 24rpx; margin-bottom: 24rpx; }
.title { font-size: 32rpx; font-weight: 600; margin-bottom: 12rpx; }
.subtitle { margin-top: 16rpx; font-size: 28rpx; font-weight: 600; }
.input, .picker { background: #f4f6fb; border-radius: 10rpx; padding: 14rpx; margin-top: 10rpx; }
.row { display: flex; justify-content: space-between; align-items: center; padding: 10rpx 0; border-bottom: 1px solid #f0f0f0; }
.row:last-child { border-bottom: none; }
.hint, .muted, .empty { color: #888; font-size: 24rpx; margin-top: 8rpx; }
.req-item { padding: 8rpx 0; }
.ghost { margin-top: 12rpx; }

/* 钱包样式 */
.wallet-card {
  background: linear-gradient(135deg, #fff3f5 0%, #ffe4e9 100%);
  border: 1px solid #ffd1d9;
}
.wallet-title { color: #d81b60; font-weight: bold; }
.wallet-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24rpx; }
.balance { color: #d81b60; }
.currency { font-size: 32rpx; font-weight: bold; margin-right: 4rpx; }
.amount { font-size: 56rpx; font-weight: bold; font-family: 'Courier New', Courier, monospace; }
.wallet-actions { display: flex; gap: 24rpx; }
.btn-recharge { flex: 1; background: linear-gradient(90deg, #ff4081, #d81b60); color: #fff; border-radius: 40rpx; }
.btn-bill { flex: 1; background: #fff; color: #d81b60; border: 1px solid #d81b60; border-radius: 40rpx; }
</style>
