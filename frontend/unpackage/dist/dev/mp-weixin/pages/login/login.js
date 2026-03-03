"use strict";
const common_vendor = require("../../common/vendor.js");
const utils_request = require("../../utils/request.js");
const utils_auth = require("../../utils/auth.js");
const _sfc_main = {
  data() {
    return {
      form: {
        name: "",
        phone: "",
        password: ""
      },
      loading: false,
      isRegister: false
    };
  },
  methods: {
    toggleMode() {
      this.isRegister = !this.isRegister;
    },
    async handleGuestLogin() {
      if (this.guestLoading)
        return;
      this.guestLoading = true;
      try {
        const res = await utils_request.request({
          url: "/auth/guest_login",
          method: "POST"
        });
        const { access_token, user } = res.data;
        utils_auth.saveAuth(access_token, user);
        common_vendor.index.showToast({ title: "访客登录成功", icon: "success" });
        setTimeout(() => {
          common_vendor.index.switchTab({ url: "/pages/index/index" });
        }, 300);
      } catch (error) {
        common_vendor.index.__f__("error", "at pages/login/login.vue:64", "访客登录失败", error);
      } finally {
        this.guestLoading = false;
      }
    },
    async handleSubmit() {
      if (!this.form.phone || !this.form.password || this.isRegister && !this.form.name) {
        common_vendor.index.showToast({ title: "请完整填写信息", icon: "none" });
        return;
      }
      this.loading = true;
      try {
        if (this.isRegister) {
          await utils_request.request({
            url: "/auth/register",
            method: "POST",
            data: {
              phone: this.form.phone,
              name: this.form.name,
              password: this.form.password
            }
          });
          common_vendor.index.showToast({ title: "注册成功，请登录", icon: "none" });
          this.isRegister = false;
        } else {
          const res = await utils_request.request({
            url: "/auth/login",
            method: "POST",
            data: {
              phone: this.form.phone,
              password: this.form.password
            }
          });
          const { access_token, user } = res.data;
          utils_auth.saveAuth(access_token, user);
          common_vendor.index.showToast({ title: "登录成功", icon: "success" });
          setTimeout(() => {
            common_vendor.index.switchTab({ url: "/pages/index/index" });
          }, 300);
        }
      } catch (error) {
        common_vendor.index.__f__("error", "at pages/login/login.vue:105", error);
      } finally {
        this.loading = false;
      }
    }
  }
};
function _sfc_render(_ctx, _cache, $props, $setup, $data, $options) {
  return common_vendor.e({
    a: common_vendor.t($data.isRegister ? "注册新账户" : "登录账户"),
    b: $data.isRegister
  }, $data.isRegister ? {
    c: $data.form.name,
    d: common_vendor.o(($event) => $data.form.name = $event.detail.value)
  } : {}, {
    e: $data.form.phone,
    f: common_vendor.o(($event) => $data.form.phone = $event.detail.value),
    g: $data.form.password,
    h: common_vendor.o(($event) => $data.form.password = $event.detail.value),
    i: common_vendor.t($data.isRegister ? "注册账号" : "立即登录"),
    j: $data.loading,
    k: common_vendor.o((...args) => $options.handleSubmit && $options.handleSubmit(...args)),
    l: common_vendor.t($data.isRegister ? "已有账号？去登录" : "没有账号？去注册"),
    m: common_vendor.o((...args) => $options.toggleMode && $options.toggleMode(...args)),
    n: !$data.isRegister
  }, !$data.isRegister ? {
    o: _ctx.guestLoading,
    p: common_vendor.o((...args) => $options.handleGuestLogin && $options.handleGuestLogin(...args))
  } : {});
}
const MiniProgramPage = /* @__PURE__ */ common_vendor._export_sfc(_sfc_main, [["render", _sfc_render], ["__scopeId", "data-v-e4e4508d"]]);
wx.createPage(MiniProgramPage);
//# sourceMappingURL=../../../.sourcemap/mp-weixin/pages/login/login.js.map
