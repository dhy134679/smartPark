<template>
  <view class="page">
    <view class="hero">
      <view>
        <view class="hello">欢迎回来</view>
        <view class="username">{{ user?.name || '访客' }}</view>
      </view>
      <view class="hero-actions">
        <button v-if="user?.role !== 'guest'" size="mini" @click="goTo('/pages/profile/profile')">个人中心</button>
        <button v-if="user?.role === 'admin' || user?.role === 'guest'" size="mini" @click="goTo('/pages/simulate/simulate')">停车模拟</button>
        <button size="mini" @click="goTo('/pages/predict/predict')">车位预测</button>
      </view>
    </view>

    <view class="section-title">实时概览</view>
    <view class="cards">
      <view class="card" v-for="item in summaryCards" :key="item.label" :class="item.type">
        <text class="label">{{ item.label }}</text>
        <text class="value">{{ item.value }}</text>
      </view>
    </view>

    <view v-if="user?.role === 'admin'">
      <view class="section-title">今日核心统计</view>
      <view class="stats">
        <view class="stat-item">
          <text class="small-label">入场</text>
          <text class="stat-value">{{ statistics.entries_today }}</text>
        </view>
        <view class="stat-item">
          <text class="small-label">出场</text>
          <text class="stat-value">{{ statistics.exits_today }}</text>
        </view>
        <view class="stat-item">
          <text class="small-label">占用车位</text>
          <text class="stat-value">{{ statistics.occupied_spots }}</text>
        </view>
        <view class="stat-item">
          <text class="small-label">收入(元)</text>
          <text class="stat-value">{{ statistics.revenue_today }}</text>
        </view>
      </view>
    </view>

    <view class="section-title">未来空闲预测</view>
    <view class="trend-card">
      <view class="recommend">推荐到场时间：{{ formatMinute(availability.recommended_time) || '---' }}</view>
      <view class="trend-list">
        <view class="trend-item" v-for="item in availability.availability" :key="item.timestamp">
          <text>{{ formatHour(item.timestamp) }}</text>
          <text>{{ item.available }} 个空闲</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import { request } from '@/utils/request.js'
import { getUser } from '@/utils/auth.js'

export default {
  data() {
    return {
      summary: { total: 0, free: 0, occupied: 0, reserved: 0, shared: 0 },
      statistics: { entries_today: 0, exits_today: 0, occupied_spots: 0, revenue_today: 0 },
      availability: { recommended_time: '', availability: [] },
      user: null
    }
  },
  computed: {
    summaryCards() {
      const cards = []
      if (this.user?.role === 'admin') {
         cards.push({ label: '总车位', value: this.summary.total, type: 'primary' })
      }
      cards.push({ label: '当前空闲', value: this.summary.free, type: 'success' })
      if (this.user?.role === 'admin') {
         cards.push({ label: '已占用', value: this.summary.occupied, type: 'danger' })
      }
      if (this.user?.role !== 'guest') {
         cards.push({ label: '共享开放', value: this.summary.shared, type: 'warning' })
      }
      return cards
    }
  },
  onShow() {
    this.user = getUser()
    if (!this.user) {
      uni.reLaunch({ url: '/pages/login/login' })
      return
    }
    this.fetchData()
  },
  methods: {
    goTo(url) {
      // tabBar 页面必须使用 switchTab，否则会出现“进不去”的问题
      const tabPages = [
        '/pages/index/index',
        '/pages/spots/spots',
        '/pages/navigation/navigation',
        '/pages/profile/profile'
      ]
      if (tabPages.includes(url)) {
        uni.switchTab({ url })
        return
      }
      uni.navigateTo({ url })
    },
    formatMinute(timestamp) {
      if (!timestamp) return ''
      const date = new Date(timestamp)
      const mm = String(date.getMonth() + 1).padStart(2, '0')
      const dd = String(date.getDate()).padStart(2, '0')
      const hh = String(date.getHours()).padStart(2, '0')
      const mi = String(date.getMinutes()).padStart(2, '0')
      return `${mm}-${dd} ${hh}:${mi}`
    },
    formatHour(timestamp) {
      if (!timestamp) return '--'
      const date = new Date(timestamp)
      return `${date.getHours()}:00`
    },
    async fetchData() {
      try {
        const [summary, statistics, availability] = await Promise.all([
          request({ url: '/spots/summary' }),
          request({ url: '/parking/statistics' }),
          request({ url: '/predict/availability' })
        ])
        this.summary = summary.data
        this.statistics = statistics.data
        this.availability = availability.data
      } catch (error) {
        console.error(error)
      }
    }
  }
}
</script>

<style scoped>
.page {
  padding: 40rpx 32rpx 80rpx;
}

.hero {
  background: linear-gradient(120deg, #2a82e4, #6a8bff);
  color: #fff;
  padding: 40rpx;
  border-radius: 24rpx;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.hello {
  font-size: 28rpx;
  color: rgba(255, 255, 255, 0.8);
}

.username {
  font-size: 40rpx;
  font-weight: bold;
}

.hero-actions button {
  margin-left: 16rpx;
}

.section-title {
  margin-top: 40rpx;
  margin-bottom: 20rpx;
  font-weight: 600;
}

.cards {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20rpx;
}

.card {
  border-radius: 18rpx;
  padding: 30rpx;
  background: #fff;
}

.card .value {
  font-size: 36rpx;
  font-weight: bold;
}

.card.primary {
  border: 2rpx solid #2a82e4;
}

.card.success {
  border: 2rpx solid #30c594;
}

.card.danger {
  border: 2rpx solid #ff7a7a;
}

.card.warning {
  border: 2rpx solid #ffb347;
}

.stats {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20rpx;
}

.stat-item {
  background: #fff;
  border-radius: 16rpx;
  padding: 24rpx;
}

.stat-value {
  font-size: 34rpx;
  font-weight: bold;
}

.trend-card {
  background: #fff;
  border-radius: 16rpx;
  padding: 24rpx;
}

.trend-list {
  margin-top: 20rpx;
}

.trend-item {
  display: flex;
  justify-content: space-between;
  padding: 12rpx 0;
  border-bottom: 1px solid #f0f0f0;
}

.trend-item:last-child {
  border-bottom: none;
}
</style>
