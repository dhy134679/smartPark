<template>
  <view class="page">
    <view v-if="isAdmin">
      <view class="card">
        <view class="title">住户管理</view>
        <view class="search-row">
          <input
            class="input"
            v-model.trim="keyword"
            placeholder="按姓名或手机号搜索"
            confirm-type="search"
            @confirm="loadAdminData"
          />
          <button size="mini" type="primary" @click="loadAdminData">查询</button>
        </view>
      </view>

      <view class="card">
        <view class="title">新增住户</view>
        <view class="form">
          <input class="input" v-model.trim="createForm.name" placeholder="姓名" />
          <input class="input" v-model.trim="createForm.phone" placeholder="手机号" type="number" />
          <input class="input" v-model.trim="createForm.password" placeholder="初始密码" password />
          <button type="primary" :loading="createLoading" @click="createUser">新增住户</button>
        </view>
      </view>

      <view class="card">
        <view class="title">住户列表</view>
        <view v-if="users.length === 0" class="empty">暂无住户</view>
        <view v-for="item in users" :key="item.id" class="user-item">
          <view class="user-main">
            <view class="name-row">
              <text class="name">{{ item.name }}</text>
            </view>
            <view class="meta">ID: {{ item.id }} | 手机号: {{ item.phone }}</view>
            <view class="meta">住户身份：{{ item.is_resident ? '是' : '否' }}</view>
          </view>

          <view class="user-actions">
            <button size="mini" type="primary" @click="goToEdit(item.id)">编辑</button>
            <button size="mini" type="warn" @click="deleteUser(item)">删除</button>
          </view>
        </view>
      </view>

      <view class="card">
        <view class="title">收费管理</view>
        <view class="form">
          <input class="input" v-model.trim="feeForm.name" placeholder="规则名称" />
          <input class="input" v-model.trim="feeForm.free_minutes" type="number" placeholder="免费时长（分钟）" />
          <input class="input" v-model.trim="feeForm.rate_per_hour" type="digit" placeholder="每小时收费（元）" />
          <input class="input" v-model.trim="feeForm.max_daily" type="digit" placeholder="每日封顶（元）" />
          <button type="primary" :loading="feeLoading" @click="saveFeeRule">保存收费规则</button>
        </view>
        <view class="income-grid">
          <view class="income-item">
            <view class="income-label">总收费</view>
            <view class="income-value">¥{{ Number(incomeSummary.total_fee || 0).toFixed(2) }}</view>
          </view>
          <view class="income-item">
            <view class="income-label">住户账号收益</view>
            <view class="income-value">¥{{ Number(incomeSummary.owner_income_total || 0).toFixed(2) }}</view>
          </view>
          <view class="income-item">
            <view class="income-label">管理员账号收益</view>
            <view class="income-value">¥{{ Number(incomeSummary.admin_income_total || 0).toFixed(2) }}</view>
          </view>
        </view>
      </view>
    </view>

    <view v-else>
      <view class="map-container">
        <view class="map-header">
          <text class="title">停车场平面图</text>
          <view class="legend">
            <view class="legend-item"><view class="dot green"></view>空闲</view>
            <view class="legend-item"><view class="dot red"></view>占用</view>
            <view class="legend-item"><view class="dot blue"></view>导航路线</view>
          </view>
        </view>
        <canvas
          canvas-id="parkingMap"
          id="parkingMap"
          class="parking-canvas"
          :style="canvasStyle"
          @click="onCanvasClick"
        ></canvas>
      </view>

      <view class="card">
        <view class="title">选择目标车位</view>
        <view class="zone-filter">
          <button
            v-for="z in ['全部', 'A', 'B', 'C']"
            :key="z"
            size="mini"
            :type="selectedZone === z ? 'primary' : 'default'"
            @click="filterZone(z)"
          >
            {{ z === '全部' ? '全部' : z + '区' }}
          </button>
        </view>
        <scroll-view scroll-y class="spot-list">
          <view
            class="spot-item"
            v-for="spot in filteredFreeSpots"
            :key="spot.id"
            :class="{ selected: selectedSpot && selectedSpot.id === spot.id }"
            @click="selectSpot(spot)"
          >
            <text class="spot-name">{{ spot.spot_number }}</text>
            <text class="spot-zone">{{ spot.zone }}区</text>
          </view>
          <view v-if="filteredFreeSpots.length === 0" class="empty">暂无空闲车位</view>
        </scroll-view>
      </view>

      <view class="card" v-if="routePath.length > 0">
        <view class="title">导航路线</view>
        <view class="route-info">
          <view class="info-item">
            <text class="info-label">起点</text>
            <text class="info-value">入口</text>
          </view>
          <view class="info-item">
            <text class="info-label">终点</text>
            <text class="info-value">{{ selectedSpot ? selectedSpot.spot_number : '-' }}</text>
          </view>
          <view class="info-item">
            <text class="info-label">步数</text>
            <text class="info-value">{{ routePath.length }} 步</text>
          </view>
          <view class="info-item">
            <text class="info-label">预计用时</text>
            <text class="info-value">{{ estimatedMinutes }} 分钟</text>
          </view>
        </view>
        <view class="tip-text">* 小程序使用静态地图引导，不依赖实时定位。</view>
        <view class="instruction-list">
          <view class="instruction-item" v-for="(item, idx) in routeInstructions" :key="idx">
            {{ idx + 1 }}. {{ item }}
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import { request } from '@/utils/request.js'
import { getUser } from '@/utils/auth.js'

const GRID_SIZE = 28
const SAFE_PADDING = 24
const COLORS = {
  background: '#f0f2f5',
  road: '#e8eaed',
  free: '#4caf50',
  occupied: '#ef5350',
  reserved: '#ff9800',
  route: '#2196f3',
  routeHead: '#1565c0',
  entry: '#9c27b0'
}

export default {
  data() {
    return {
      user: null,
      keyword: '',
      users: [],
      createForm: {
        name: '',
        phone: '',
        password: ''
      },
      createLoading: false,
      feeForm: {
        name: '标准收费',
        free_minutes: 30,
        rate_per_hour: 5,
        max_daily: 50
      },
      feeLoading: false,
      incomeSummary: {
        total_fee: 0,
        owner_income_total: 0,
        admin_income_total: 0
      },

      mapInfo: null,
      allSpots: [],
      selectedZone: '全部',
      selectedSpot: null,
      routePath: [],
      preSelectedSpotId: null,
      cellSize: GRID_SIZE,
      canvasWidth: 0,
      canvasHeight: 0
    }
  },
  computed: {
    isAdmin() {
      return this.user && this.user.role === 'admin'
    },
    freeSpots() {
      return this.allSpots.filter((spot) => spot.status === 'free')
    },
    filteredFreeSpots() {
      if (this.selectedZone === '全部') return this.freeSpots
      return this.freeSpots.filter((spot) => spot.zone === this.selectedZone)
    },
    estimatedMinutes() {
      if (this.routePath.length <= 1) return 0
      const walkingSpeedStepPerMinute = 75
      return Math.max(1, Math.ceil((this.routePath.length - 1) / walkingSpeedStepPerMinute))
    },
    canvasStyle() {
      return `width:${this.canvasWidth}px;height:${this.canvasHeight}px;`
    },
    routeInstructions() {
      if (this.routePath.length <= 1) return []
      const instructions = []
      let prevDirection = ''
      let stepCount = 0

      for (let idx = 1; idx < this.routePath.length; idx++) {
        const prev = this.routePath[idx - 1]
        const current = this.routePath[idx]
        const direction = this.getDirection(prev, current)

        if (!prevDirection) {
          prevDirection = direction
          stepCount = 1
          continue
        }

        if (direction === prevDirection) {
          stepCount += 1
        } else {
          instructions.push(`向${prevDirection}直行 ${stepCount} 步`)
          prevDirection = direction
          stepCount = 1
        }
      }

      if (stepCount > 0) {
        instructions.push(`向${prevDirection}直行 ${stepCount} 步`)
      }
      instructions.push('到达目标车位附近，请减速并观察车位编号')
      return instructions
    }
  },
  onLoad(options) {
    if (options && options.spotId) {
      this.preSelectedSpotId = parseInt(options.spotId)
    }
  },
  onShow() {
    this.user = getUser()
    if (!this.user) {
      uni.reLaunch({ url: '/pages/login/login' })
      return
    }
    const navSpotId = uni.getStorageSync('navSpotId')
    if (navSpotId) {
      this.preSelectedSpotId = parseInt(navSpotId)
      uni.removeStorageSync('navSpotId')
    }
    if (this.isAdmin) {
      this.loadAdminData()
      return
    }
    this.loadMap()
  },
  onPullDownRefresh() {
    const task = this.isAdmin ? this.loadAdminData() : this.loadMap()
    Promise.resolve(task).finally(() => uni.stopPullDownRefresh())
  },
  methods: {
    goToEdit(id) {
      uni.navigateTo({
        url: `/pages/userEdit/userEdit?id=${id}`
      })
    },
    async loadAdminData() {
      try {
        const query = {
          resident_only: true
        }
        if (this.keyword) {
          query.keyword = this.keyword
        }

        const [usersRes, feeRes, incomeRes] = await Promise.all([
          request({
            url: '/auth/users',
            data: query
          }),
          request({
            url: '/fees/rule'
          }),
          request({
            url: '/fees/income-summary'
          })
        ])

        this.users = usersRes.data.items || []
        const rule = feeRes?.data?.rule
        if (rule) {
          this.feeForm = {
            name: rule.name,
            free_minutes: rule.free_minutes,
            rate_per_hour: rule.rate_per_hour,
            max_daily: rule.max_daily
          }
        }
        this.incomeSummary = incomeRes.data || this.incomeSummary
      } catch (error) {
        console.error(error)
      }
    },
    async createUser() {
      if (!this.createForm.name || !this.createForm.phone || !this.createForm.password) {
        uni.showToast({ title: '请填写完整信息', icon: 'none' })
        return
      }
      this.createLoading = true
      try {
        await request({
          url: '/auth/users',
          method: 'POST',
          data: this.createForm
        })
        uni.showToast({ title: '新增成功', icon: 'success' })
        this.createForm = { name: '', phone: '', password: '' }
        await this.loadAdminData()
      } catch (error) {
        console.error(error)
      } finally {
        this.createLoading = false
      }
    },
    async saveFeeRule() {
      const payload = {
        name: this.feeForm.name,
        free_minutes: Number(this.feeForm.free_minutes),
        rate_per_hour: Number(this.feeForm.rate_per_hour),
        max_daily: Number(this.feeForm.max_daily)
      }
      if (!payload.name) {
        uni.showToast({ title: '请输入规则名称', icon: 'none' })
        return
      }
      if (
        Number.isNaN(payload.free_minutes) ||
        Number.isNaN(payload.rate_per_hour) ||
        Number.isNaN(payload.max_daily)
      ) {
        uni.showToast({ title: '请输入有效收费参数', icon: 'none' })
        return
      }
      this.feeLoading = true
      try {
        await request({
          url: '/fees/rule',
          method: 'PUT',
          data: payload
        })
        uni.showToast({ title: '收费规则已更新', icon: 'success' })
        await this.loadAdminData()
      } catch (error) {
        console.error(error)
      } finally {
        this.feeLoading = false
      }
    },
    deleteUser(user) {
      uni.showModal({
        title: '确认删除',
        content: `确定删除用户 ${user.name} 吗？`,
        success: async (res) => {
          if (!res.confirm) return
          try {
            await request({
              url: `/auth/users/${user.id}`,
              method: 'DELETE'
            })
            uni.showToast({ title: '删除成功', icon: 'success' })
            await this.loadAdminData()
          } catch (error) {
            console.error(error)
          }
        }
      })
    },

    filterZone(zone) {
      this.selectedZone = zone
    },
    getDirection(from, to) {
      if (to.x > from.x) return '右'
      if (to.x < from.x) return '左'
      if (to.y > from.y) return '下'
      return '上'
    },
    updateCanvasSize() {
      const systemInfo = uni.getSystemInfoSync()
      const containerWidth = systemInfo.windowWidth - SAFE_PADDING
      const gw = this.mapInfo?.width || 24
      const gh = this.mapInfo?.height || 18
      const nextCellSize = Math.max(12, Math.floor(containerWidth / gw))
      this.cellSize = nextCellSize
      this.canvasWidth = gw * nextCellSize
      this.canvasHeight = gh * nextCellSize
    },
    selectSpot(spot) {
      this.selectedSpot = spot
      this.planRoute()
    },
    async loadMap() {
      try {
        const res = await request({ url: '/navigation/map' })
        this.mapInfo = res.data
        this.allSpots = res.data.spots || []
        this.updateCanvasSize()

        if (this.preSelectedSpotId) {
          const target = this.allSpots.find((spot) => spot.id === this.preSelectedSpotId)
          if (target) {
            this.selectedSpot = target
            await this.planRoute()
            this.preSelectedSpotId = null
            return
          }
        }
        this.$nextTick(() => {
          this.drawMap()
        })
      } catch (error) {
        console.error(error)
      }
    },
    async planRoute() {
      if (!this.selectedSpot) return
      try {
        const res = await request({
          url: '/navigation/route',
          method: 'POST',
          data: { spot_id: this.selectedSpot.id }
        })
        this.routePath = res.data.route || []
        this.drawMap()
      } catch (error) {
        console.error(error)
      }
    },
    drawMap() {
      const ctx = uni.createCanvasContext('parkingMap', this)
      const gw = this.mapInfo?.width || 24
      const gh = this.mapInfo?.height || 18
      const size = this.cellSize || GRID_SIZE
      const width = gw * size
      const height = gh * size

      ctx.setFillStyle(COLORS.background)
      ctx.fillRect(0, 0, width, height)

      ctx.setFillStyle(COLORS.road)
      ctx.fillRect(0, 3 * size - 4, width, size + 8)
      ctx.fillRect(0, 10 * size - 4, width, size + 8)
      ctx.fillRect(12 * size - 4, 0, size + 8, height)

      ctx.setStrokeStyle('#bdc3c7')
      ctx.setLineWidth(2)
      ctx.setLineDash([10, 10], 0)

      ctx.beginPath()
      ctx.moveTo(0, 3.5 * size)
      ctx.lineTo(width, 3.5 * size)
      ctx.stroke()

      ctx.beginPath()
      ctx.moveTo(0, 10.5 * size)
      ctx.lineTo(width, 10.5 * size)
      ctx.stroke()

      ctx.beginPath()
      ctx.moveTo(12.5 * size, 0)
      ctx.lineTo(12.5 * size, height)
      ctx.stroke()
      ctx.setLineDash([], 0)

      if (this.routePath.length > 1) {
        ctx.setStrokeStyle('rgba(33, 150, 243, 0.3)')
        ctx.setLineWidth(10)
        ctx.setLineCap('round')
        ctx.setLineJoin('round')
        ctx.beginPath()
        const first = this.routePath[0]
        ctx.moveTo(first.x * size + size / 2, first.y * size + size / 2)
        for (let idx = 1; idx < this.routePath.length; idx++) {
          const point = this.routePath[idx]
          ctx.lineTo(point.x * size + size / 2, point.y * size + size / 2)
        }
        ctx.stroke()

        ctx.setStrokeStyle(COLORS.route)
        ctx.setLineWidth(4)
        ctx.beginPath()
        ctx.moveTo(first.x * size + size / 2, first.y * size + size / 2)
        for (let idx = 1; idx < this.routePath.length; idx++) {
          const point = this.routePath[idx]
          ctx.lineTo(point.x * size + size / 2, point.y * size + size / 2)
        }
        ctx.stroke()

        ctx.setFillStyle(COLORS.entry)
        ctx.beginPath()
        ctx.arc(first.x * size + size / 2, first.y * size + size / 2, 8, 0, Math.PI * 2)
        ctx.fill()

        const last = this.routePath[this.routePath.length - 1]
        ctx.setFillStyle(COLORS.routeHead)
        ctx.beginPath()
        ctx.arc(last.x * size + size / 2, last.y * size + size / 2, 8, 0, Math.PI * 2)
        ctx.fill()
      }

      this.allSpots.forEach((spot) => {
        const spotX = spot.x_pos * size
        const spotY = spot.y_pos * size
        const centerX = spotX + size / 2
        const centerY = spotY + size / 2
        const selected = this.selectedSpot && this.selectedSpot.id === spot.id

        ctx.setStrokeStyle('#b0bec5')
        ctx.setLineWidth(2)
        ctx.strokeRect(spotX + 2, spotY + 2, size - 4, size - 4)

        if (spot.status === 'free') {
          ctx.setFillStyle(selected ? COLORS.route : COLORS.free)
          ctx.fillRect(spotX + 4, spotY + 4, size - 8, size - 8)

          ctx.setFillStyle('#fff')
          ctx.setFontSize(10)
          ctx.setTextAlign('center')
          ctx.setTextBaseline('middle')
          ctx.fillText(spot.spot_number.replace(/^[A-C]-/, ''), centerX, centerY)
        } else {
          const carColor = spot.status === 'reserved' ? COLORS.reserved : COLORS.occupied

          ctx.setFillStyle(carColor)
          ctx.fillRect(spotX + 6, spotY + 4, size - 12, size - 8)

          ctx.setFillStyle('rgba(255, 255, 255, 0.5)')
          ctx.fillRect(spotX + 8, spotY + 6, size - 16, size * 0.2)
          ctx.fillRect(spotX + 8, spotY + (size - 8) * 0.7, size - 16, size * 0.15)
        }

        if (selected) {
           ctx.setStrokeStyle(COLORS.routeHead)
           ctx.setLineWidth(3)
           ctx.strokeRect(spotX + 2, spotY + 2, size - 4, size - 4)
        }
      })

      const entry = this.mapInfo?.entry || [0, 0]
      const entryX = entry[0] * size + size / 2
      const entryY = entry[1] * size + size / 2
      ctx.setFillStyle(COLORS.entry)
      ctx.beginPath()
      ctx.arc(entryX, entryY, 14, 0, Math.PI * 2)
      ctx.fill()

      ctx.setFillStyle('#fff')
      ctx.setFontSize(10)
      ctx.setTextAlign('center')
      ctx.setTextBaseline('middle')
      ctx.fillText('入口', entryX, entryY)

      ctx.draw()
    },
    onCanvasClick(event) {
      const size = this.cellSize || GRID_SIZE
      const x = Math.floor(event.detail.x / size)
      const y = Math.floor(event.detail.y / size)
      const clicked = this.allSpots.find(
        (spot) =>
          Math.round(spot.x_pos) === x &&
          Math.round(spot.y_pos) === y &&
          spot.status === 'free'
      )
      if (clicked) {
        this.selectSpot(clicked)
      }
    }
  }
}
</script>

<style scoped>
.page {
  padding: 24rpx;
  background: #f6f7fb;
}

.card,
.map-container {
  background: #fff;
  border-radius: 20rpx;
  padding: 24rpx;
  margin-bottom: 24rpx;
  box-shadow: 0 8rpx 20rpx rgba(0, 0, 0, 0.04);
}

.title {
  font-size: 32rpx;
  font-weight: 600;
  margin-bottom: 16rpx;
}

.search-row {
  display: flex;
  gap: 12rpx;
  align-items: center;
}

.form .input,
.search-row .input,
.edit-panel .input,
.vehicle-form .input {
  background: #f4f6fb;
  border-radius: 12rpx;
  padding: 16rpx;
  margin-bottom: 12rpx;
  flex: 1;
}

.user-item {
  border: 1px solid #f0f0f0;
  border-radius: 12rpx;
  padding: 16rpx;
  margin-bottom: 16rpx;
}

.user-main {
  margin-bottom: 12rpx;
}

.name-row {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.name {
  font-size: 30rpx;
  font-weight: 600;
}

.tag {
  font-size: 22rpx;
  color: #2a82e4;
  background: #edf4ff;
  padding: 4rpx 12rpx;
  border-radius: 999rpx;
}

.meta {
  margin-top: 6rpx;
  font-size: 24rpx;
  color: #666;
}

.user-actions {
  display: flex;
  gap: 12rpx;
  margin-bottom: 12rpx;
}

.edit-panel {
  background: #fafafa;
  border-radius: 12rpx;
  padding: 16rpx;
  margin-bottom: 12rpx;
}

.edit-actions {
  display: flex;
  gap: 12rpx;
}

.switch-row {
  display: flex;
  align-items: center;
  gap: 12rpx;
  margin-bottom: 12rpx;
}

.assign-panel {
  background: #fafafa;
  border-radius: 12rpx;
  padding: 16rpx;
  margin-bottom: 12rpx;
}

.vehicle-panel {
  background: #fafafa;
  border-radius: 12rpx;
  padding: 16rpx;
}

.assign-title {
  font-size: 26rpx;
  margin-bottom: 12rpx;
}

.picker {
  background: #fff;
  border: 1px solid #e5e5e5;
  border-radius: 10rpx;
  padding: 14rpx;
  margin-bottom: 10rpx;
  color: #444;
}

.owned-list {
  margin-top: 12rpx;
}

.owned-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8rpx;
}

.empty {
  font-size: 24rpx;
  color: #999;
}

.map-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16rpx;
}

.legend {
  display: flex;
  gap: 16rpx;
}

.legend-item {
  display: flex;
  align-items: center;
  font-size: 22rpx;
  color: #666;
}

.dot {
  width: 16rpx;
  height: 16rpx;
  border-radius: 50%;
  margin-right: 6rpx;
}

.dot.green {
  background: #4caf50;
}

.dot.red {
  background: #ef5350;
}

.dot.blue {
  background: #2196f3;
}

.parking-canvas {
  width: 100%;
  height: 504rpx;
  border-radius: 12rpx;
}

.zone-filter {
  display: flex;
  gap: 12rpx;
  margin-bottom: 16rpx;
}

.spot-list {
  max-height: 320rpx;
}

.spot-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16rpx 20rpx;
  margin-bottom: 8rpx;
  border-radius: 12rpx;
  background: #f8faf8;
  border: 2rpx solid transparent;
}

.spot-item.selected {
  border-color: #2196f3;
  background: #e3f2fd;
}

.spot-name {
  font-weight: 600;
  font-size: 28rpx;
}

.spot-zone {
  font-size: 24rpx;
  color: #999;
}

.income-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12rpx;
  margin-top: 12rpx;
}

.income-item {
  background: #f8faf8;
  border-radius: 12rpx;
  padding: 14rpx;
}

.income-label {
  color: #888;
  font-size: 22rpx;
}

.income-value {
  margin-top: 8rpx;
  font-size: 28rpx;
  font-weight: 600;
}

.route-info {
  display: flex;
  justify-content: space-around;
}


.tip-text {
  margin-top: 16rpx;
  color: #666;
  font-size: 22rpx;
}

.instruction-list {
  margin-top: 12rpx;
  background: #f7f9fc;
  border-radius: 12rpx;
  padding: 12rpx 16rpx;
}

.instruction-item {
  font-size: 24rpx;
  color: #333;
  line-height: 1.8;
}

.info-item {
  text-align: center;
}

.info-label {
  display: block;
  font-size: 24rpx;
  color: #999;
}

.info-value {
  display: block;
  font-size: 32rpx;
  font-weight: 600;
  color: #333;
  margin-top: 8rpx;
}
</style>
