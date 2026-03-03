<template>
  <view class="page">
    <scroll-view scroll-y class="list" :lower-threshold="60" @scrolltolower="loadMore">
      <view class="record-card" v-for="item in records" :key="item.id">
        <view class="row">
          <text class="plate">{{ item.plate_number }}</text>
          <text>{{ item.status }}</text>
        </view>
        <view class="row">入场：{{ formatTime(item.entry_time) }}</view>
        <view class="row">出场：{{ item.exit_time ? formatTime(item.exit_time) : '未出场' }}</view>
        <view class="row">费用：{{ item.fee }} 元</view>
      </view>
      <view class="footer">{{ footerText }}</view>
    </scroll-view>
  </view>
</template>

<script>
import { request } from '@/utils/request.js'

export default {
  data() {
    return {
      page: 1,
      size: 10,
      total: 0,
      loading: false,
      records: []
    }
  },
  computed: {
    footerText() {
      if (this.total === 0 && !this.loading) {
        return '暂无记录'
      }
      if (this.records.length >= this.total && this.total !== 0) {
        return '没有更多了'
      }
      return '上拉加载更多'
    }
  },
  onShow() {
    this.reset()
  },
  methods: {
    reset() {
      this.page = 1
      this.records = []
      this.total = 0
      this.loadRecords()
    },
    formatTime(time) {
      return time ? time.replace('T', ' ').slice(0, 16) : '--'
    },
    async loadRecords() {
      if (this.loading) return
      if (this.records.length >= this.total && this.total !== 0) return
      this.loading = true
      try {
        const res = await request({ url: `/parking/records?page=${this.page}&size=${this.size}` })
        const { items, total } = res.data
        this.records = this.records.concat(items)
        this.total = total
        this.page += 1
      } catch (error) {
        console.error(error)
      } finally {
        this.loading = false
      }
    },
    loadMore() {
      this.loadRecords()
    }
  }
}
</script>

<style scoped>
.page {
  padding: 24rpx;
}

.list {
  height: calc(100vh - 100rpx);
}

.record-card {
  background: #fff;
  border-radius: 18rpx;
  padding: 20rpx;
  margin-bottom: 20rpx;
  box-shadow: 0 8rpx 18rpx rgba(0, 0, 0, 0.04);
}

.row {
  margin-bottom: 12rpx;
  font-size: 26rpx;
}

.row:last-child {
  margin-bottom: 0;
}

.plate {
  font-weight: bold;
}

.footer {
  text-align: center;
  color: #999;
  padding: 20rpx 0;
}
</style>
