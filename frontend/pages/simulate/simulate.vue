<template>
  <view class="page">
    <!-- 入场模拟 -->
    <view class="card">
      <view class="card-header">
        <view class="title">车辆入场模拟</view>
        <view class="step-bar">
          <view class="step" :class="{ active: entryStep >= 1 }">上传图片</view>
          <view class="step-line" :class="{ active: entryStep >= 2 }"></view>
          <view class="step" :class="{ active: entryStep >= 2 }">车牌识别</view>
          <view class="step-line" :class="{ active: entryStep >= 3 }"></view>
          <view class="step" :class="{ active: entryStep >= 3 }">分配车位</view>
        </view>
      </view>

      <!-- 方式选择 -->
      <view class="mode-switch">
        <button size="mini" :type="entryMode === 'image' ? 'primary' : 'default'" @click="entryMode = 'image'">图片识别</button>
        <button size="mini" :type="entryMode === 'manual' ? 'primary' : 'default'" @click="entryMode = 'manual'">手动输入</button>
      </view>

      <!-- 图片上传模式 -->
      <view v-if="entryMode === 'image'" class="upload-area" @click="chooseEntryImage">
        <image v-if="entryImagePath" :src="entryImagePath" mode="aspectFit" class="preview-image" />
        <view v-else class="upload-placeholder">
          <text class="upload-icon">上传图片</text>
          <text>点击拍照或选择车辆图片</text>
        </view>
      </view>

      <!-- 手动输入模式 -->
      <view v-if="entryMode === 'manual'" class="form-group">
        <input class="input" v-model="entryForm.plate_number" placeholder="车牌号，如 京A12345" />
        <input class="input" v-model="entryForm.vehicle_brand" placeholder="品牌（可选）" />
        <input class="input" v-model="entryForm.vehicle_color" placeholder="颜色（可选）" />
        
        <picker
          :range="freeSpots"
          range-key="label"
          @change="onTargetSpotChange"
        >
          <view class="picker input">{{ targetSpotLabel }}</view>
        </picker>
      </view>

      <!-- 识别结果 -->
      <view class="recognize-result" v-if="recognizeResult">
        <view class="result-header">
          <text class="result-plate">{{ recognizeResult.plate_number }}</text>
          <text class="confidence">置信度 {{ (recognizeResult.confidence * 100).toFixed(1) }}%</text>
        </view>
        <view class="result-tag" :class="recognizeResult.is_resident ? 'resident' : 'visitor'">
          {{ recognizeResult.is_resident ? '小区车辆' : '外来车辆' }}
        </view>
      </view>

      <button class="btn-primary" @click="handleEntry" :loading="entryLoading">
        {{ entryMode === 'image' ? '上传识别并入场' : '模拟入场' }}
      </button>

      <!-- 入场结果 -->
      <view class="result-card success" v-if="entryResult">
        <view class="result-title">入场成功</view>
        <view class="result-row">车牌：<text class="bold">{{ entryResult.plate_number }}</text></view>
        <view class="result-row">车位：<text class="bold">{{ entryResult.spot?.spot_number || '等待分配' }}</text></view>
        <view class="result-row">区域：<text class="bold">{{ entryResult.spot?.zone || '-' }} 区</text></view>
        <view class="result-row">
          类型：
          <text :class="entryResult.is_resident ? 'text-green' : 'text-orange'">
            {{ entryResult.is_resident ? '小区车辆（免费）' : '外来车辆（计时收费）' }}
          </text>
        </view>
        <button v-if="entryResult.spot" size="mini" type="primary" @click="goNavigation(entryResult.spot.id)">
          查看导航路线 →
        </button>
      </view>
    </view>

    <!-- 出场模拟 -->
    <view class="card">
      <view class="card-header">
        <view class="title">车辆出场模拟</view>
        <view class="step-bar">
          <view class="step" :class="{ active: exitStep >= 1 }">识别车牌</view>
          <view class="step-line" :class="{ active: exitStep >= 2 }"></view>
          <view class="step" :class="{ active: exitStep >= 2 }">费用计算</view>
          <view class="step-line" :class="{ active: exitStep >= 3 }"></view>
          <view class="step" :class="{ active: exitStep >= 3 }">模拟支付</view>
        </view>
      </view>

      <view class="mode-switch">
        <button size="mini" :type="exitMode === 'image' ? 'primary' : 'default'" @click="exitMode = 'image'">图片识别</button>
        <button size="mini" :type="exitMode === 'manual' ? 'primary' : 'default'" @click="exitMode = 'manual'">手动输入</button>
      </view>

      <view v-if="exitMode === 'image'" class="upload-area" @click="chooseExitImage">
        <image v-if="exitImagePath" :src="exitImagePath" mode="aspectFit" class="preview-image" />
        <view v-else class="upload-placeholder">
          <text class="upload-icon">上传图片</text>
          <text>点击拍照或选择车辆图片</text>
        </view>
      </view>

      <view v-if="exitMode === 'manual'">
        <input class="input" v-model="exitForm.plate_number" placeholder="车牌号" />
      </view>

      <button class="btn-danger" @click="handleExit" :loading="exitLoading">
        {{ exitMode === 'image' ? '上传识别并出场' : '模拟出场' }}
      </button>

      <!-- 出场结果 -->
      <view class="result-card" :class="exitResult && exitResult.fee > 0 ? 'warning' : 'success'" v-if="exitResult">
        <view class="result-title">结算完成</view>
        <view class="result-row">车牌：<text class="bold">{{ exitResult.plate_number }}</text></view>
        <view class="result-row">停车时长：<text class="bold">{{ exitResult.duration_minutes }} 分钟</text></view>
        <view class="result-row">
          停车费用：
          <text class="bold fee-amount" :class="exitResult.fee > 0 ? 'text-orange' : 'text-green'">
            ¥{{ exitResult.fee.toFixed(2) }}
          </text>
        </view>
        <view class="result-row">
          状态：{{ exitResult.is_resident ? '小区车辆免费' : (exitResult.fee > 0 ? '待支付' : '已结算') }}
        </view>
        <button v-if="exitResult.fee > 0 && exitResult.status === 'exited'" class="btn-pay" @click="simulatePay">
          模拟支付 ¥{{ exitResult.fee.toFixed(2) }}
        </button>
      </view>
    </view>
  </view>
</template>

<script>
import { request, uploadFile } from '@/utils/request.js'

export default {
  data() {
    return {
      entryMode: 'manual',
      exitMode: 'manual',
      entryStep: 0,
      exitStep: 0,
      entryLoading: false,
      exitLoading: false,
      entryImagePath: '',
      exitImagePath: '',
      entryForm: { plate_number: '', vehicle_brand: '', vehicle_color: '' },
      exitForm: { plate_number: '' },
      recognizeResult: null,
      entryResult: null,
      exitResult: null,
      freeSpots: [],
      selectedSpotId: null
    }
  },
  computed: {
    targetSpotLabel() {
      if (!this.selectedSpotId) return '自动分配（或点击选择目标车位）'
      const spot = this.freeSpots.find(s => s.id === this.selectedSpotId)
      return spot ? spot.label : '自动分配（或点击选择目标车位）'
    }
  },
  onShow() {
    this.loadSpots()
  },
  methods: {
    async loadSpots() {
      try {
        const res = await request({ url: '/spots' })
        const allSpots = res.data.items || []
        this.freeSpots = allSpots
          .filter(spot => spot.status === 'free')
          .map(spot => ({
            id: spot.id,
            label: `${spot.spot_number} (${spot.zone}区)`
          }))
      } catch (error) {
        console.error('获取车位失败:', error)
      }
    },
    onTargetSpotChange(event) {
      const idx = Number(event.detail.value)
      const option = this.freeSpots[idx]
      if (option) {
        this.selectedSpotId = option.id
      }
    },
    isPossiblePlate(text) {
      if (!text || text === '未知') return false
      return /^[\u4e00-\u9fa5][A-Z][A-Z0-9]{5,7}$/.test(String(text).toUpperCase())
    },
    // 选择入场图片
    chooseEntryImage() {
      uni.chooseImage({
        count: 1,
        sourceType: ['album', 'camera'],
        success: (res) => {
          this.entryImagePath = res.tempFilePaths[0]
          this.entryStep = 1
          this.recognizeImage(res.tempFilePaths[0])
        }
      })
    },
    // 选择出场图片
    chooseExitImage() {
      uni.chooseImage({
        count: 1,
        sourceType: ['album', 'camera'],
        success: (res) => {
          this.exitImagePath = res.tempFilePaths[0]
          this.exitStep = 1
        }
      })
    },
    // 调用车牌识别接口
    async recognizeImage(filePath) {
      try {
        const result = await uploadFile({
          url: '/recognize/',
          filePath: filePath,
          name: 'file'
        })
        if (result.data) {
          this.recognizeResult = result.data
          if (this.isPossiblePlate(result.data.plate_number)) {
            this.entryForm.plate_number = result.data.plate_number
            this.entryStep = 2
          } else {
            this.entryForm.plate_number = ''
            this.entryMode = 'manual'
            uni.showToast({ title: '未识别到有效车牌，请手动输入', icon: 'none' })
          }
        }
      } catch (error) {
        console.error('识别失败:', error)
        uni.showToast({ title: '识别失败，请手动输入', icon: 'none' })
      }
    },
    // 入场处理
    async handleEntry() {
      if (!this.isPossiblePlate(this.entryForm.plate_number)) {
        uni.showToast({ title: '请输入车牌号或上传图片', icon: 'none' })
        return
      }
      this.entryForm.plate_number = this.entryForm.plate_number.toUpperCase()
      this.entryLoading = true
      
      const payload = { ...this.entryForm }
      if (this.selectedSpotId) {
        payload.target_spot_id = this.selectedSpotId
      }
      
      try {
        const res = await request({
          url: '/parking/entry',
          method: 'POST',
          data: payload
        })
        this.entryResult = res.data
        this.entryStep = 3
        this.selectedSpotId = null
        this.loadSpots()
        uni.showToast({ title: '入场成功', icon: 'success' })
      } catch (error) {
        console.error(error)
      } finally {
        this.entryLoading = false
      }
    },
    // 出场处理
    async handleExit() {
      let plateNumber = this.exitForm.plate_number
      // 图片模式先识别
      if (this.exitMode === 'image' && this.exitImagePath) {
        try {
          const result = await uploadFile({
            url: '/recognize/',
            filePath: this.exitImagePath,
            name: 'file'
          })
          if (result.data) {
            if (!this.isPossiblePlate(result.data.plate_number)) {
              uni.showToast({ title: '未识别到有效车牌，请手动输入', icon: 'none' })
              return
            }
            plateNumber = result.data.plate_number
            this.exitStep = 1
          }
        } catch (error) {
          uni.showToast({ title: '识别失败', icon: 'none' })
          return
        }
      }
      if (!this.isPossiblePlate(plateNumber)) {
        uni.showToast({ title: '请输入车牌号或上传图片', icon: 'none' })
        return
      }
      plateNumber = plateNumber.toUpperCase()
      this.exitLoading = true
      try {
        const res = await request({
          url: '/parking/exit',
          method: 'POST',
          data: { plate_number: plateNumber }
        })
        this.exitResult = res.data
        this.exitStep = 2
        uni.showToast({ title: '结算完成', icon: 'success' })
      } catch (error) {
        console.error(error)
      } finally {
        this.exitLoading = false
      }
    },
    // 模拟支付
    simulatePay() {
      uni.showModal({
        title: '模拟支付',
        content: `确认支付 ¥${this.exitResult.fee.toFixed(2)}？`,
        success: async (res) => {
          if (!res.confirm) return
          try {
            const payRes = await request({
              url: '/parking/pay',
              method: 'POST',
              data: { record_id: this.exitResult.record_id }
            })
            this.exitResult.status = payRes.data.status
            this.exitStep = 3
            uni.showToast({ title: '支付成功', icon: 'success' })
          } catch (error) {
            console.error(error)
          }
        }
      })
    },
    // 跳转导航
    goNavigation(spotId) {
      uni.setStorageSync('navSpotId', spotId)
      uni.switchTab({ url: '/pages/navigation/navigation' })
    }
  }
}
</script>

<style scoped>
.page { padding: 24rpx; background: #f6f7fb; min-height: 100vh; }

.card {
  background: #fff;
  border-radius: 24rpx;
  padding: 30rpx;
  margin-bottom: 30rpx;
  box-shadow: 0 12rpx 30rpx rgba(0, 0, 0, 0.06);
}

.card-header { margin-bottom: 24rpx; }

.title {
  font-size: 34rpx;
  font-weight: bold;
  margin-bottom: 16rpx;
}

/* 步骤条 */
.step-bar {
  display: flex;
  align-items: center;
  margin-top: 12rpx;
}
.step {
  font-size: 22rpx;
  color: #ccc;
  padding: 6rpx 16rpx;
  border-radius: 24rpx;
  background: #f5f5f5;
  transition: all 0.3s;
}
.step.active {
  color: #fff;
  background: linear-gradient(90deg, #2a82e4, #6a8bff);
}
.step-line {
  flex: 1;
  height: 4rpx;
  background: #eee;
  margin: 0 8rpx;
}
.step-line.active { background: #2a82e4; }

/* 模式切换 */
.mode-switch {
  display: flex;
  gap: 16rpx;
  margin-bottom: 20rpx;
}

/* 上传区域 */
.upload-area {
  border: 3rpx dashed #d0d5dd;
  border-radius: 16rpx;
  height: 300rpx;
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 20rpx;
  overflow: hidden;
  background: #fafbfc;
}
.upload-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  color: #999;
}
.upload-icon { font-size: 60rpx; margin-bottom: 12rpx; }
.preview-image { width: 100%; height: 100%; }

/* 表单 */
.form-group { margin-bottom: 20rpx; }
.input {
  padding: 20rpx;
  margin-bottom: 16rpx;
  background: #f4f6fb;
  border-radius: 12rpx;
}

/* 识别结果 */
.recognize-result {
  background: #f0f7ff;
  border-radius: 12rpx;
  padding: 20rpx;
  margin-bottom: 20rpx;
}
.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.result-plate {
  font-size: 36rpx;
  font-weight: bold;
  color: #2a82e4;
}
.confidence {
  font-size: 24rpx;
  color: #999;
}
.result-tag {
  display: inline-block;
  margin-top: 12rpx;
  padding: 6rpx 16rpx;
  border-radius: 8rpx;
  font-size: 24rpx;
}
.result-tag.resident { background: #e8f5e9; color: #2e7d32; }
.result-tag.visitor { background: #fff3e0; color: #ef6c00; }

/* 按钮 */
.btn-primary {
  background: linear-gradient(90deg, #2a82e4, #6a8bff);
  color: #fff;
  border-radius: 12rpx;
  margin-top: 10rpx;
}
.btn-danger {
  background: linear-gradient(90deg, #ff5c5c, #ff8a65);
  color: #fff;
  border-radius: 12rpx;
  margin-top: 10rpx;
}
.btn-pay {
  background: linear-gradient(90deg, #30c594, #26a69a);
  color: #fff;
  border-radius: 12rpx;
  margin-top: 16rpx;
}

/* 结果卡片 */
.result-card {
  margin-top: 24rpx;
  padding: 24rpx;
  border-radius: 16rpx;
}
.result-card.success { background: #e8f5e9; border: 2rpx solid #a5d6a7; }
.result-card.warning { background: #fff3e0; border: 2rpx solid #ffcc80; }
.result-title { font-size: 30rpx; font-weight: bold; margin-bottom: 12rpx; }
.result-row { font-size: 28rpx; margin-bottom: 8rpx; color: #555; }
.bold { font-weight: bold; color: #333; }
.fee-amount { font-size: 32rpx; }
.text-green { color: #2e7d32; }
.text-orange { color: #ef6c00; }
</style>
