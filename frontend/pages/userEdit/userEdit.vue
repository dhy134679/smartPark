<template>
  <view class="page" v-if="user">
    <view class="card">
      <view class="title">基本信息</view>
      <view class="edit-panel">
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
          <button size="mini" type="primary" @click="saveEdit">保存信息</button>
        </view>
      </view>
    </view>

    <view class="card">
      <view class="assign-panel">
        <view class="title">车位分配</view>
        <picker
          :range="assignZones"
          @change="onAssignZoneChange"
        >
          <view class="picker">{{ assignZoneLabel() }}</view>
        </picker>
        <picker
          :range="assignableSpots"
          range-key="label"
          @change="onAssignSpotChange"
        >
          <view class="picker">{{ assignLabel() }}</view>
        </picker>
        <button size="mini" type="primary" @click="assignSpot">分配车位</button>

        <view class="owned-list" v-if="ownedSpots.length > 0">
          <view v-for="spot in ownedSpots" :key="spot.id" class="owned-item">
            <text>{{ spot.spot_number }}</text>
            <button size="mini" @click="releaseSpot(spot.id)">释放</button>
          </view>
        </view>
        <view class="empty" v-else>当前无分配车位</view>
      </view>
    </view>

    <view class="card">
      <view class="vehicle-panel">
        <view class="title">车辆管理</view>
        <view class="owned-list" v-if="userVehicles.length > 0">
          <view v-for="vehicle in userVehicles" :key="vehicle.id" class="owned-item">
            <text>{{ vehicle.plate_number }} {{ vehicle.brand || '-' }} {{ vehicle.color || '-' }}</text>
            <button size="mini" type="warn" @click="deleteVehicleForUser(vehicle.id)">删除</button>
          </view>
        </view>
        <view class="empty" v-else>当前无绑定车辆</view>

        <view class="vehicle-form">
          <input
            class="input"
            v-model.trim="vehicleForm.plate_number"
            placeholder="车牌号"
          />
          <input
            class="input"
            v-model.trim="vehicleForm.brand"
            placeholder="品牌"
          />
          <input
            class="input"
            v-model.trim="vehicleForm.color"
            placeholder="颜色"
          />
          <label class="switch-row">
            <switch
              :checked="vehicleForm.is_resident"
              @change="vehicleForm.is_resident = $event.detail.value"
            />
            <text>小区车辆</text>
          </label>
          <button size="mini" type="primary" @click="addVehicleForUser">
            添加车辆
          </button>
        </view>
      </view>
    </view>
  </view>
  <view class="page empty" v-else>
    加载中...
  </view>
</template>

<script>
import { request } from '@/utils/request.js'
import { getUser } from '@/utils/auth.js'

export default {
  data() {
    return {
      userId: null,
      user: null,
      currentUser: null,
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
      
      allSpots: [],
      assignZoneSelection: null,
      assignZones: ['A', 'B', 'C'],
      assignSelection: null,

      userVehicles: [],
      vehicleForm: {
        plate_number: '',
        brand: '',
        color: '',
        is_resident: true
      }
    }
  },
  computed: {
    isAdmin() {
      return this.currentUser && this.currentUser.role === 'admin'
    },
    ownedSpots() {
      return this.allSpots.filter((spot) => spot.owner_id === this.userId)
    },
    assignableSpots() {
      const selectedZone = this.assignZoneSelection
      return this.allSpots
        .filter((spot) => spot.owner_id === null || spot.owner_id === this.userId)
        .filter((spot) => !selectedZone || spot.zone === selectedZone)
        .map((spot) => ({
          id: spot.id,
          label: `${spot.spot_number} (${spot.zone}区)`
        }))
    }
  },
  onLoad(options) {
    if (options && options.id) {
      this.userId = parseInt(options.id)
    }
  },
  onShow() {
    this.currentUser = getUser()
    if (!this.currentUser || !this.isAdmin) {
      uni.navigateBack()
      return
    }
    if (this.userId) {
      this.loadData()
    }
  },
  onPullDownRefresh() {
    if (this.userId) {
      this.loadData().finally(() => uni.stopPullDownRefresh())
    } else {
      uni.stopPullDownRefresh()
    }
  },
  methods: {
    roleLabel(role) {
      const target = this.roleOptions.find((item) => item.value === role)
      return target ? target.label : '住户'
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
    async loadData() {
      try {
        const [usersRes, spotsRes, vehiclesRes] = await Promise.all([
          request({ url: '/auth/users' }),
          request({ url: '/spots' }),
          request({ url: '/vehicles/admin', data: { owner_id: this.userId } })
        ])
        
        const users = usersRes.data.items || []
        this.user = users.find(u => u.id === this.userId)
        if (this.user) {
          this.editForm = {
            name: this.user.name,
            phone: this.user.phone,
            role: this.user.role,
            is_resident: this.user.is_resident
          }
        } else {
          uni.showToast({ title: '用户不存在', icon: 'none' })
          setTimeout(() => uni.navigateBack(), 1500)
          return
        }

        this.allSpots = spotsRes.data.items || []
        this.userVehicles = vehiclesRes.data.items || []
      } catch (error) {
        console.error(error)
      }
    },
    async saveEdit() {
      if (!this.editForm.name || !this.editForm.phone) {
        uni.showToast({ title: '姓名和手机号不能为空', icon: 'none' })
        return
      }
      try {
        await request({
          url: `/auth/users/${this.userId}`,
          method: 'PUT',
          data: this.editForm
        })
        uni.showToast({ title: '保存成功', icon: 'success' })
        await this.loadData()
      } catch (error) {
        console.error(error)
      }
    },
    
    // 车位分配逻辑
    onAssignZoneChange(event) {
      const idx = Number(event.detail.value)
      const zone = this.assignZones[idx]
      if (!zone) return
      this.assignZoneSelection = zone
      this.assignSelection = null
    },
    assignZoneLabel() {
      return this.assignZoneSelection
        ? `${this.assignZoneSelection}区`
        : '请选择目标区域'
    },
    onAssignSpotChange(event) {
      const idx = Number(event.detail.value)
      const options = this.assignableSpots
      const option = options[idx]
      if (!option) return
      this.assignSelection = option.id
    },
    assignLabel() {
      const spotId = this.assignSelection
      if (!spotId) return '请选择可分配车位'
      const spot = this.allSpots.find((item) => item.id === spotId)
      return spot ? `${spot.spot_number} (${spot.zone}区)` : '请选择可分配车位'
    },
    async assignSpot() {
      const spotId = this.assignSelection
      if (!spotId) {
        uni.showToast({ title: '请先选择车位', icon: 'none' })
        return
      }
      try {
        await request({
          url: `/spots/${spotId}/owner`,
          method: 'PUT',
          data: { owner_id: this.userId }
        })
        uni.showToast({ title: '分配成功', icon: 'success' })
        this.assignSelection = null
        await this.loadData()
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
        if (this.assignSelection === spotId) {
            this.assignSelection = null
        }
        await this.loadData()
      } catch (error) {
        console.error(error)
      }
    },

    // 车辆管理逻辑
    async addVehicleForUser() {
      const form = this.vehicleForm
      if (!form.plate_number) {
        uni.showToast({ title: '请输入车牌号', icon: 'none' })
        return
      }
      try {
        await request({
          url: `/vehicles/admin/users/${this.userId}`,
          method: 'POST',
          data: form
        })
        uni.showToast({ title: '车辆添加成功', icon: 'success' })
        this.vehicleForm = {
          plate_number: '',
          brand: '',
          color: '',
          is_resident: true
        }
        await this.loadData()
      } catch (error) {
        console.error(error)
      }
    },
    async deleteVehicleForUser(vehicleId) {
      uni.showModal({
        title: '确认删除',
        content: '确定要删除该车辆吗？',
        success: async (res) => {
          if (!res.confirm) return
          try {
            await request({
              url: `/vehicles/admin/${vehicleId}`,
              method: 'DELETE'
            })
            uni.showToast({ title: '车辆已删除', icon: 'success' })
            await this.loadData()
          } catch (error) {
            console.error(error)
          }
        }
      })
    }
  }
}
</script>

<style scoped>
.page {
  padding: 24rpx;
  background: #f6f7fb;
  min-height: 100vh;
}
.empty {
  display: flex;
  justify-content: center;
  align-items: center;
  color: #999;
}

.card {
  background: #fff;
  border-radius: 20rpx;
  padding: 24rpx;
  margin-bottom: 24rpx;
  box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.05);
}

.title {
  font-size: 32rpx;
  font-weight: 600;
  margin-bottom: 24rpx;
  padding-bottom: 12rpx;
  border-bottom: 1rpx solid #eee;
}

.input {
  background: #f4f6fb;
  border-radius: 12rpx;
  padding: 16rpx;
  margin-bottom: 20rpx;
}

.picker {
  background: #f4f6fb;
  border-radius: 12rpx;
  padding: 16rpx;
  margin-bottom: 20rpx;
  color: #333;
}

.switch-row {
  display: flex;
  align-items: center;
  gap: 12rpx;
  margin-bottom: 20rpx;
}

.edit-actions {
  display: flex;
  justify-content: center;
  margin-top: 24rpx;
}

.owned-list {
  margin-top: 24rpx;
  background: #fafafa;
  border-radius: 12rpx;
  padding: 16rpx;
}

.owned-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12rpx 0;
  border-bottom: 1rpx solid #eee;
}
.owned-item:last-child {
  border-bottom: none;
}

.vehicle-form {
  margin-top: 32rpx;
  padding-top: 24rpx;
  border-top: 1rpx dashed #ccc;
}
</style>
