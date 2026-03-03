<template>
  <view class="page">
    <view class="filter">
      <button v-for="tab in tabs" :key="tab.value" size="mini" :type="zone === tab.value ? 'primary' : 'default'" @click="changeZone(tab.value)">
        {{ tab.label }}
      </button>
    </view>

    <scroll-view scroll-y class="list">
      <view class="spot-card" v-for="spot in filteredSpots" :key="spot.id">
        <view>
          <view class="spot-name">{{ spot.spot_number }} ({{ spot.zone }})</view>
          <view class="spot-status" :class="spot.status">状态：{{ statusText(spot.status) }}</view>
          <view class="spot-detail">共享：{{ spot.is_shared ? '是' : '否' }}</view>
        </view>
        <view class="coords">({{ spot.x_pos }}, {{ spot.y_pos }})</view>
      </view>
    </scroll-view>
  </view>
</template>

<script>
import { request } from '@/utils/request.js'

export default {
  data() {
    return {
      spots: [],
      zone: 'all',
      tabs: [
        { label: '全部', value: 'all' },
        { label: 'A 区', value: 'A' },
        { label: 'B 区', value: 'B' },
        { label: 'C 区', value: 'C' }
      ]
    }
  },
  computed: {
    filteredSpots() {
      if (this.zone === 'all') return this.spots
      return this.spots.filter(item => item.zone === this.zone)
    }
  },
  onShow() {
    this.loadSpots()
  },
  onPullDownRefresh() {
    this.loadSpots().finally(() => uni.stopPullDownRefresh())
  },
  methods: {
    changeZone(value) {
      this.zone = value
    },
    statusText(status) {
      switch (status) {
        case 'free':
          return '空闲'
        case 'occupied':
          return '占用'
        case 'reserved':
          return '预留'
        default:
          return status
      }
    },
    async loadSpots() {
      try {
        const res = await request({ url: '/spots' })
        this.spots = res.data.items
      } catch (error) {
        console.error(error)
      }
    }
  }
}
</script>

<style scoped>
.page {
  padding: 24rpx;
}

.filter {
  display: flex;
  justify-content: space-between;
  margin-bottom: 20rpx;
}

.list {
  height: calc(100vh - 180rpx);
}

.spot-card {
  background: #fff;
  border-radius: 16rpx;
  padding: 24rpx;
  margin-bottom: 20rpx;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 10rpx 20rpx rgba(0, 0, 0, 0.05);
}

.spot-status.free {
  color: #30c594;
}

.spot-status.occupied {
  color: #ff5c5c;
}

.spot-status.reserved {
  color: #ffa500;
}

.coords {
  font-size: 26rpx;
  color: #999;
}
</style>
