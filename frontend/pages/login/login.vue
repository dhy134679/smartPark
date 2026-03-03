<template>
  <view class="login-page">
    <view class="card">
      <view class="title">智能停车场系统</view>
      <view class="subtitle">{{ isRegister ? '注册新账户' : '登录账户' }}</view>
      <view class="form-item" v-if="isRegister">
        <text class="label">姓名</text>
        <input v-model="form.name" class="input" placeholder="请输入姓名" />
      </view>
      <view class="form-item">
        <text class="label">手机号</text>
        <input v-model="form.phone" class="input" type="number" placeholder="请输入手机号" />
      </view>
      <view class="form-item">
        <text class="label">密码</text>
        <input v-model="form.password" class="input" password placeholder="请输入密码" />
      </view>
      <button class="primary" :loading="loading" @click="handleSubmit">{{ isRegister ? '注册账号' : '立即登录' }}</button>
      <button class="ghost" @click="toggleMode">
        {{ isRegister ? '已有账号？去登录' : '没有账号？去注册' }}
      </button>
      <button class="text-btn" :loading="guestLoading" @click="handleGuestLogin" v-if="!isRegister">
        我是外来访客，直接进入体验
      </button>
    </view>
  </view>
</template>

<script>
import { request } from '@/utils/request.js'
import { saveAuth } from '@/utils/auth.js'

export default {
  data() {
    return {
      form: {
        name: '',
        phone: '',
        password: ''
      },
      loading: false,
      isRegister: false
    }
  },
  methods: {
    toggleMode() {
      this.isRegister = !this.isRegister
    },
    async handleGuestLogin() {
      if (this.guestLoading) return
      this.guestLoading = true
      try {
        const res = await request({
          url: '/auth/guest_login',
          method: 'POST'
        })
        const { access_token, user } = res.data
        saveAuth(access_token, user)
        uni.showToast({ title: '访客登录成功', icon: 'success' })
        setTimeout(() => {
          uni.switchTab({ url: '/pages/index/index' })
        }, 300)
      } catch (error) {
        console.error('访客登录失败', error)
      } finally {
        this.guestLoading = false
      }
    },
    async handleSubmit() {
      if (!this.form.phone || !this.form.password || (this.isRegister && !this.form.name)) {
        uni.showToast({ title: '请完整填写信息', icon: 'none' })
        return
      }
      this.loading = true
      try {
        if (this.isRegister) {
          await request({
            url: '/auth/register',
            method: 'POST',
            data: {
              phone: this.form.phone,
              name: this.form.name,
              password: this.form.password
            }
          })
          uni.showToast({ title: '注册成功，请登录', icon: 'none' })
          this.isRegister = false
        } else {
          const res = await request({
            url: '/auth/login',
            method: 'POST',
            data: {
              phone: this.form.phone,
              password: this.form.password
            }
          })
          const { access_token, user } = res.data
          saveAuth(access_token, user)
          uni.showToast({ title: '登录成功', icon: 'success' })
          setTimeout(() => {
            uni.switchTab({ url: '/pages/index/index' })
          }, 300)
        }
      } catch (error) {
        console.error(error)
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 40rpx;
  background: linear-gradient(135deg, #edf2ff, #fef7f4);
}

.card {
  width: 90%;
  max-width: 680rpx;
  padding: 60rpx;
  background: #fff;
  border-radius: 24rpx;
  box-shadow: 0 20rpx 60rpx rgba(64, 83, 191, 0.15);
}

.title {
  font-size: 40rpx;
  font-weight: bold;
  margin-bottom: 12rpx;
}

.subtitle {
  font-size: 28rpx;
  color: #888;
  margin-bottom: 40rpx;
}

.form-item {
  margin-bottom: 24rpx;
}

.label {
  display: block;
  font-size: 26rpx;
  margin-bottom: 8rpx;
}

.input {
  width: 100%;
  padding: 20rpx;
  border-radius: 12rpx;
  background: #f5f7fb;
}

.primary {
  margin-top: 20rpx;
  background: linear-gradient(90deg, #2a82e4, #6a8bff);
  color: #fff;
}

.ghost {
  margin-top: 16rpx;
  color: #2a82e4;
  border: 1px solid #2a82e4;
}

.text-btn {
  margin-top: 24rpx;
  font-size: 26rpx;
  color: #888;
  background: transparent;
  border: none;
}
.text-btn::after {
  display: none;
}
</style>
