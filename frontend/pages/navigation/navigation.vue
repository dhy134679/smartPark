<template>
  <view class="page">
    <view v-if="isAdmin">
      <view class="card">
        <view class="title">用户管理</view>
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
        <view class="title">新增用户</view>
        <view class="form">
          <input class="input" v-model.trim="createForm.name" placeholder="姓名" />
          <input class="input" v-model.trim="createForm.phone" placeholder="手机号" type="number" />
          <input class="input" v-model.trim="createForm.password" placeholder="初始密码" password />
          <button type="primary" :loading="createLoading" @click="createUser">新增住户</button>
        </view>
      </view>

      <view class="card">
        <view class="title">用户列表</view>
        <view v-if="users.length === 0" class="empty">暂无用户</view>
        <view v-for="item in users" :key="item.id" class="user-item">
          <view class="user-main">
            <view class="name-row">
              <text class="name">{{ item.name }}</text>
              <text class="tag">{{ roleText(item.role) }}</text>
            </view>
            <view class="meta">ID: {{ item.id }} | 手机号: {{ item.phone }}</view>
            <view class="meta">住户身份：{{ item.is_resident ? '是' : '否' }}</view>
          </view>

          <view class="user-actions">
            <button size="mini" @click="startEdit(item)">编辑</button>
            <button size="mini" type="warn" @click="deleteUser(item)">删除</button>
          </view>

          <view v-if="editingUserId === item.id" class="edit-panel">
            <input class="input" v-model.trim="editForm.name" placeholder="姓名" />
            <input class="input" v-model.trim="editForm.phone" placeholder="手机号" type="number" />
            <picker :range="roleOptions" range-key="label" @change="onEditRoleChange">
              <view class="picker">{{ roleLabel(editForm.role) }}</view>
            </picker>
            <label class="switch-row">
              <switch
                :checked="editForm.is_resident"
                @change="editForm.is_resident = $event.detail.value"
              />
              <text>是否住户</text>
            </label>
            <view class="edit-actions">
              <button size="mini" type="primary" @click="saveEdit(item.id)">保存</button>
              <button size="mini" @click="cancelEdit">取消</button>
            </view>
          </view>

          <view class="assign-panel">
            <view class="assign-title">车位分配</view>
            <picker
              :range="assignZones"
              @change="onAssignZoneChange(item.id, $event)"
            >
              <view class="picker">{{ assignZoneLabel(item.id) }}</view>
            </picker>
            <picker
              :range="assignableSpots(item.id)"
              range-key="label"
              @change="onAssignSpotChange(item.id, $event)"
            >
              <view class="picker">{{ assignLabel(item.id) }}</view>
            </picker>
            <button size="mini" type="primary" @click="assignSpot(item.id)">分配车位</button>

            <view class="owned-list" v-if="ownedSpots(item.id).length > 0">
              <view v-for="spot in ownedSpots(item.id)" :key="spot.id" class="owned-item">
                <text>{{ spot.spot_number }}</text>
                <button size="mini" @click="releaseSpot(spot.id)">释放</button>
              </view>
            </view>
            <view class="empty" v-else>当前无分配车位</view>
          </view>

          <view class="vehicle-panel">
            <view class="assign-title">车辆管理</view>
            <view class="owned-list" v-if="userVehicles(item.id).length > 0">
              <view v-for="vehicle in userVehicles(item.id)" :key="vehicle.id" class="owned-item">
                <text>{{ vehicle.plate_number }} {{ vehicle.brand || '-' }} {{ vehicle.color || '-' }}</text>
                <button size="mini" type="warn" @click="deleteVehicleForUser(vehicle.id)">删除</button>
              </view>
            </view>
            <view class="empty" v-else>当前无绑定车辆</view>

            <view class="vehicle-form">
              <input
                class="input"
                v-model.trim="vehicleForm(item.id).plate_number"
                placeholder="车牌号"
              />
              <input
                class="input"
                v-model.trim="vehicleForm(item.id).brand"
                placeholder="品牌"
              />
              <input
                class="input"
                v-model.trim="vehicleForm(item.id).color"
                placeholder="颜色"
              />
              <label class="switch-row">
                <switch
                  :checked="vehicleForm(item.id).is_resident"
                  @change="vehicleForm(item.id).is_resident = $event.detail.value"
                />
                <text>小区车辆</text>
              </label>
              <button size="mini" type="primary" @click="addVehicleForUser(item.id)">
                添加车辆
              </button>
            </view>
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
      spots: [],
      vehicles: [],
      createForm: {
        name: '',
        phone: '',
        password: ''
      },
      createLoading: false,
      editingUserId: null,
      editForm: {
        name: '',
        phone: '',
        role: 'resident',
        is_resident: true
      },
      roleOptions: [
        { label: '住户', value: 'resident' },
        { label: '管理员', value: 'admin' },
        { label: '访客', value: 'guest' }
      ],
      assignSelections: {},
      assignZoneSelections: {},
      assignZones: ['A', 'B', 'C', 'D'],
      vehicleForms: {},

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
    roleText(role) {
      if (role === 'admin') return '管理员'
      if (role === 'guest') return '访客'
      return '住户'
    },
    roleLabel(role) {
      const target = this.roleOptions.find((item) => item.value === role)
      return target ? target.label : '住户'
    },
    startEdit(user) {
      this.editingUserId = user.id
      this.editForm = {
        name: user.name,
        phone: user.phone,
        role: user.role,
        is_resident: user.is_resident
      }
    },
    cancelEdit() {
      this.editingUserId = null
      this.editForm = {
        name: '',
        phone: '',
        role: 'resident',
        is_resident: true
      }
    },
    onEditRoleChange(event) {
      const idx = Number(event.detail.value)
      const option = this.roleOptions[idx]
      if (!option) return
      this.editForm.role = option.value
      if (option.value === 'guest') {
        this.editForm.is_resident = false
      }
    },
    async loadAdminData() {
      try {
        const [usersRes, spotsRes, vehiclesRes] = await Promise.all([
          request({
            url: '/auth/users',
            data: this.keyword ? { keyword: this.keyword } : {}
          }),
          request({ url: '/spots' }),
          request({ url: '/vehicles/admin' })
        ])
        this.users = usersRes.data.items || []
        this.spots = spotsRes.data.items || []
        this.vehicles = vehiclesRes.data.items || []
        this.syncVehicleForms()
      } catch (error) {
        console.error(error)
      }
    },
    syncVehicleForms() {
      const nextForms = {}
      for (const item of this.users) {
        const existing = this.vehicleForms[item.id]
        nextForms[item.id] = existing || {
          plate_number: '',
          brand: '',
          color: '',
          is_resident: true
        }
      }
      this.vehicleForms = nextForms
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
    async saveEdit(userId) {
      if (!this.editForm.name || !this.editForm.phone) {
        uni.showToast({ title: '姓名和手机号不能为空', icon: 'none' })
        return
      }
      try {
        await request({
          url: `/auth/users/${userId}`,
          method: 'PUT',
          data: this.editForm
        })
        uni.showToast({ title: '保存成功', icon: 'success' })
        this.cancelEdit()
        await this.loadAdminData()
      } catch (error) {
        console.error(error)
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
    ownedSpots(userId) {
      return this.spots.filter((spot) => spot.owner_id === userId)
    },
    userVehicles(userId) {
      return this.vehicles.filter((vehicle) => vehicle.owner_id === userId)
    },
    vehicleForm(userId) {
      return this.vehicleForms[userId] || {
        plate_number: '',
        brand: '',
        color: '',
        is_resident: true
      }
    },
    assignableSpots(userId) {
      const selectedZone = this.assignZoneSelections[userId]
      return this.spots
        .filter((spot) => spot.owner_id === null || spot.owner_id === userId)
        .filter((spot) => !selectedZone || spot.zone === selectedZone)
        .map((spot) => ({
          id: spot.id,
          label: `${spot.spot_number} (${spot.zone}区)`
        }))
    },
    onAssignZoneChange(userId, event) {
      const idx = Number(event.detail.value)
      const zone = this.assignZones[idx]
      if (!zone) return
      this.assignZoneSelections[userId] = zone
      this.assignSelections[userId] = null
    },
    assignZoneLabel(userId) {
      return this.assignZoneSelections[userId]
        ? `${this.assignZoneSelections[userId]}区`
        : '请选择目标区域'
    },
    onAssignSpotChange(userId, event) {
      const idx = Number(event.detail.value)
      const options = this.assignableSpots(userId)
      const option = options[idx]
      if (!option) return
      this.assignSelections[userId] = option.id
    },
    assignLabel(userId) {
      const spotId = this.assignSelections[userId]
      if (!spotId) return '请选择可分配车位'
      const spot = this.spots.find((item) => item.id === spotId)
      return spot ? `${spot.spot_number} (${spot.zone}区)` : '请选择可分配车位'
    },
    async assignSpot(userId) {
      const spotId = this.assignSelections[userId]
      if (!spotId) {
        uni.showToast({ title: '请先选择车位', icon: 'none' })
        return
      }
      try {
        await request({
          url: `/spots/${spotId}/owner`,
          method: 'PUT',
          data: { owner_id: userId }
        })
        uni.showToast({ title: '分配成功', icon: 'success' })
        await this.loadAdminData()
      } catch (error) {
        console.error(error)
      }
    },
    async releaseSpot(spotId) {
      try {
        await request({
          url: `/spots/${spotId}/owner`,
          method: 'PUT',
          data: { owner_id: null }
        })
        uni.showToast({ title: '已释放', icon: 'success' })
        await this.loadAdminData()
      } catch (error) {
        console.error(error)
      }
    },
    async addVehicleForUser(userId) {
      const form = this.vehicleForm(userId)
      if (!form.plate_number) {
        uni.showToast({ title: '请输入车牌号', icon: 'none' })
        return
      }
      try {
        await request({
          url: `/vehicles/admin/users/${userId}`,
          method: 'POST',
          data: form
        })
        uni.showToast({ title: '车辆添加成功', icon: 'success' })
        this.vehicleForms[userId] = {
          plate_number: '',
          brand: '',
          color: '',
          is_resident: true
        }
        await this.loadAdminData()
      } catch (error) {
        console.error(error)
      }
    },
    async deleteVehicleForUser(vehicleId) {
      try {
        await request({
          url: `/vehicles/admin/${vehicleId}`,
          method: 'DELETE'
        })
        uni.showToast({ title: '车辆已删除', icon: 'success' })
        await this.loadAdminData()
      } catch (error) {
        console.error(error)
      }
    },

    filterZone(zone) {
      this.selectedZone = zone
    },
    // 计算方向文本（用于静态路线说明）
    getDirection(from, to) {
      if (to.x > from.x) return '右'
      if (to.x < from.x) return '左'
      if (to.y > from.y) return '下'
      return '上'
    },
    // 根据屏幕宽度动态计算画布尺寸，避免不同机型上被裁切
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
            return
          }
        }
        this.drawMap()
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

      ctx.setFillStyle('#e8eaed')
      ctx.fillRect(0, 3 * size - 4, width, size + 8)
      ctx.fillRect(0, 10 * size - 4, width, size + 8)
      ctx.fillRect(12 * size - 4, 0, size + 8, height)

      if (this.routePath.length > 1) {
        ctx.setStrokeStyle(COLORS.route)
        ctx.setLineWidth(4)
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
        const centerX = spot.x_pos * size + size / 2
        const centerY = spot.y_pos * size + size / 2
        const selected = this.selectedSpot && this.selectedSpot.id === spot.id

        ctx.setFillStyle(
          selected
            ? COLORS.route
            : spot.status === 'free'
              ? COLORS.free
              : spot.status === 'reserved'
                ? COLORS.reserved
                : COLORS.occupied
        )
        const spotSize = selected ? size - 4 : size - 6
        const offset = (size - spotSize) / 2
        ctx.fillRect(spot.x_pos * size + offset, spot.y_pos * size + offset, spotSize, spotSize)

        ctx.setFillStyle('#fff')
        ctx.setFontSize(8)
        ctx.setTextAlign('center')
        ctx.setTextBaseline('middle')
        ctx.fillText(spot.spot_number.replace(/^[A-C]-/, ''), centerX, centerY)
      })

      const entry = this.mapInfo?.entry || [0, 0]
      ctx.setFillStyle(COLORS.entry)
      ctx.setFontSize(12)
      ctx.setTextAlign('center')
      ctx.fillText('入口', entry[0] * size + size / 2, entry[1] * size + size / 2)

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
