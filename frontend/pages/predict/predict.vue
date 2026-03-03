<template>
  <view class="page">
    <view class="card">
      <view class="title">趋势预测</view>
      <slider min="6" max="24" step="2" :value="horizon" @change="onHorizonChange" />
      <view class="hint">预测小时数：{{ horizon }}</view>
      <view class="trend-item" v-for="item in trend" :key="item.timestamp">
        <text>{{ formatTime(item.timestamp) }}</text>
        <text>{{ Math.round(item.occupancy_rate * 100) }}% 占用</text>
      </view>
    </view>

    <view class="card">
      <view class="title">未来空闲</view>
      <view class="availability" v-for="item in availability" :key="item.timestamp">
        <text>{{ formatTime(item.timestamp) }}</text>
        <text>{{ item.available }} 个空位</text>
      </view>
    </view>
  </view>
</template>

<script>
import { request } from '@/utils/request.js'

export default {
  data() {
    return {
      horizon: 12,
      trend: [],
      availability: []
    }
  },
  onShow() {
    this.loadData()
  },
  methods: {
    formatTime(ts) {
      const date = new Date(ts)
      return `${date.getMonth() + 1}/${date.getDate()} ${date.getHours()}:00`
    },
    async loadData() {
      try {
        const [trendRes, availabilityRes] = await Promise.all([
          request({ url: `/predict/trend?horizon=${this.horizon}` }),
          request({ url: '/predict/availability' })
        ])
        this.trend = trendRes.data.trend
        this.availability = availabilityRes.data.availability
      } catch (error) {
        console.error(error)
      }
    },
    onHorizonChange(e) {
      this.horizon = Number(e.detail.value)
      this.loadData()
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

.trend-item,
.availability {
  display: flex;
  justify-content: space-between;
  padding: 12rpx 0;
  border-bottom: 1px solid #f2f2f2;
}

.trend-item:last-child,
.availability:last-child {
  border-bottom: none;
}

.hint {
  font-size: 24rpx;
  color: #999;
  margin-bottom: 12rpx;
}
</style>
