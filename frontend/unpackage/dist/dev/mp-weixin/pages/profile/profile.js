"use strict";
const common_vendor = require("../../common/vendor.js");
const utils_request = require("../../utils/request.js");
const utils_auth = require("../../utils/auth.js");
const _sfc_main = {
  data() {
    return {
      user: null,
      vehicles: [],
      mySpots: [],
      allSpots: [],
      myRequests: [],
      pendingRequests: [],
      profileForm: { name: "", phone: "" },
      pwdForm: { old_password: "", new_password: "" },
      vehicleForm: { plate_number: "", brand: "", color: "", is_resident: true },
      actions: ["新增车位", "更换车位", "释放车位"],
      spotAction: "assign",
      zones: ["A", "B", "C", "D"],
      targetZone: "",
      targetSpotId: null,
      requestReason: ""
    };
  },
  computed: {
    isAdmin() {
      return this.user && this.user.role === "admin";
    },
    actionLabel() {
      return this.actionText(this.spotAction);
    },
    targetSpotOptions() {
      return this.allSpots.filter((item) => item.status === "free").filter((item) => !this.targetZone || item.zone === this.targetZone).map((item) => ({ id: item.id, label: `${item.spot_number} (${item.zone}区)` }));
    },
    targetSpotLabel() {
      const target = this.targetSpotOptions.find((item) => item.id === this.targetSpotId);
      return target ? target.label : "请选择目标车位";
    }
  },
  onShow() {
    this.loadData();
  },
  methods: {
    actionText(action) {
      if (action === "assign")
        return "新增车位";
      if (action === "release")
        return "释放车位";
      return "更换车位";
    },
    statusText(status) {
      if (status === "approved")
        return "（已通过）";
      if (status === "rejected")
        return "（已拒绝）";
      return "（待审批）";
    },
    onActionChange(event) {
      const idx = Number(event.detail.value);
      const map = ["assign", "change", "release"];
      this.spotAction = map[idx] || "assign";
    },
    onZoneChange(event) {
      const idx = Number(event.detail.value);
      this.targetZone = this.zones[idx] || "";
      this.targetSpotId = null;
    },
    onSpotChange(event) {
      const idx = Number(event.detail.value);
      const target = this.targetSpotOptions[idx];
      this.targetSpotId = target ? target.id : null;
    },
    async loadData() {
      try {
        const profile = await utils_request.request({ url: "/auth/profile" });
        this.user = profile.data.user;
        this.profileForm = { name: this.user.name, phone: this.user.phone };
        if (this.isAdmin) {
          const reqRes = await utils_request.request({ url: "/spots/change-requests?status=pending" });
          this.pendingRequests = reqRes.data.items || [];
          return;
        }
        if (this.user.role !== "guest") {
          const [vehiclesRes, mySpotsRes, spotsRes, myReqRes] = await Promise.all([
            utils_request.request({ url: "/vehicles" }),
            utils_request.request({ url: "/spots/my" }),
            utils_request.request({ url: "/spots" }),
            utils_request.request({ url: "/spots/change-requests/my" })
          ]);
          this.vehicles = vehiclesRes.data.items || [];
          this.mySpots = mySpotsRes.data.items || [];
          this.allSpots = spotsRes.data.items || [];
          this.myRequests = myReqRes.data.items || [];
        }
      } catch (error) {
        common_vendor.index.__f__("error", "at pages/profile/profile.vue:171", error);
        if ((error == null ? void 0 : error.statusCode) === 401)
          this.logout();
      }
    },
    async saveProfile() {
      try {
        const res = await utils_request.request({ url: "/auth/profile", method: "PUT", data: this.profileForm });
        this.user = res.data.user;
        utils_auth.saveAuth(utils_auth.getToken(), this.user);
        common_vendor.index.showToast({ title: "资料已更新", icon: "success" });
      } catch (error) {
        common_vendor.index.__f__("error", "at pages/profile/profile.vue:182", error);
      }
    },
    async changePassword() {
      try {
        await utils_request.request({ url: "/auth/change-password", method: "PUT", data: this.pwdForm });
        this.pwdForm = { old_password: "", new_password: "" };
        common_vendor.index.showToast({ title: "密码已更新", icon: "success" });
      } catch (error) {
        common_vendor.index.__f__("error", "at pages/profile/profile.vue:191", error);
      }
    },
    async addVehicle() {
      if (!this.vehicleForm.plate_number) {
        common_vendor.index.showToast({ title: "请输入车牌号", icon: "none" });
        return;
      }
      await utils_request.request({ url: "/vehicles", method: "POST", data: this.vehicleForm });
      this.vehicleForm = { plate_number: "", brand: "", color: "", is_resident: true };
      await this.loadData();
    },
    async removeVehicle(vehicleId) {
      await utils_request.request({ url: `/vehicles/${vehicleId}`, method: "DELETE" });
      await this.loadData();
    },
    async submitSpotRequest() {
      if (this.spotAction !== "release" && !this.targetSpotId) {
        common_vendor.index.showToast({ title: "请选择目标车位", icon: "none" });
        return;
      }
      await utils_request.request({
        url: "/spots/change-requests",
        method: "POST",
        data: {
          action: this.spotAction,
          target_spot_id: this.spotAction === "release" ? null : this.targetSpotId,
          target_zone: this.spotAction === "release" ? null : this.targetZone,
          reason: this.requestReason || null
        }
      });
      common_vendor.index.showToast({ title: "申请已提交", icon: "success" });
      this.requestReason = "";
      this.targetSpotId = null;
      await this.loadData();
    },
    async reviewRequest(requestId, status) {
      await utils_request.request({
        url: `/spots/change-requests/${requestId}/review`,
        method: "PUT",
        data: { status }
      });
      common_vendor.index.showToast({ title: "审批完成", icon: "success" });
      await this.loadData();
    },
    logout() {
      utils_auth.clearAuth();
      common_vendor.index.reLaunch({ url: "/pages/login/login" });
    }
  }
};
function _sfc_render(_ctx, _cache, $props, $setup, $data, $options) {
  var _a;
  return common_vendor.e({
    a: $data.user
  }, $data.user ? common_vendor.e({
    b: !$options.isAdmin
  }, !$options.isAdmin ? {
    c: $data.profileForm.name,
    d: common_vendor.o(common_vendor.m(($event) => $data.profileForm.name = $event.detail.value, {
      trim: true
    })),
    e: $data.profileForm.phone,
    f: common_vendor.o(common_vendor.m(($event) => $data.profileForm.phone = $event.detail.value, {
      trim: true
    })),
    g: common_vendor.o((...args) => $options.saveProfile && $options.saveProfile(...args))
  } : {
    h: common_vendor.t($data.user.name),
    i: common_vendor.t($data.user.phone)
  }, {
    j: common_vendor.o((...args) => $options.logout && $options.logout(...args))
  }) : {}, {
    k: $data.user
  }, $data.user ? {
    l: $data.pwdForm.old_password,
    m: common_vendor.o(($event) => $data.pwdForm.old_password = $event.detail.value),
    n: $data.pwdForm.new_password,
    o: common_vendor.o(($event) => $data.pwdForm.new_password = $event.detail.value),
    p: common_vendor.o((...args) => $options.changePassword && $options.changePassword(...args))
  } : {}, {
    q: $data.user && !$options.isAdmin && $data.user.role !== "guest"
  }, $data.user && !$options.isAdmin && $data.user.role !== "guest" ? {
    r: common_vendor.f($data.vehicles, (item, k0, i0) => {
      return {
        a: common_vendor.t(item.plate_number),
        b: common_vendor.t(item.brand || "-"),
        c: common_vendor.t(item.color || "-"),
        d: common_vendor.o(($event) => $options.removeVehicle(item.id), item.id),
        e: item.id
      };
    }),
    s: $data.vehicleForm.plate_number,
    t: common_vendor.o(($event) => $data.vehicleForm.plate_number = $event.detail.value),
    v: $data.vehicleForm.brand,
    w: common_vendor.o(($event) => $data.vehicleForm.brand = $event.detail.value),
    x: $data.vehicleForm.color,
    y: common_vendor.o(($event) => $data.vehicleForm.color = $event.detail.value),
    z: common_vendor.o((...args) => $options.addVehicle && $options.addVehicle(...args))
  } : {}, {
    A: $data.user && !$options.isAdmin && $data.user.role !== "guest"
  }, $data.user && !$options.isAdmin && $data.user.role !== "guest" ? common_vendor.e({
    B: common_vendor.t(((_a = $data.mySpots[0]) == null ? void 0 : _a.spot_number) || "暂无"),
    C: common_vendor.t($options.actionLabel),
    D: $data.actions,
    E: common_vendor.o((...args) => $options.onActionChange && $options.onActionChange(...args)),
    F: $data.spotAction !== "release"
  }, $data.spotAction !== "release" ? {
    G: common_vendor.t($data.targetZone || "请选择区域"),
    H: $data.zones,
    I: common_vendor.o((...args) => $options.onZoneChange && $options.onZoneChange(...args))
  } : {}, {
    J: $data.spotAction !== "release"
  }, $data.spotAction !== "release" ? {
    K: common_vendor.t($options.targetSpotLabel),
    L: $options.targetSpotOptions,
    M: common_vendor.o((...args) => $options.onSpotChange && $options.onSpotChange(...args))
  } : {}, {
    N: $data.requestReason,
    O: common_vendor.o(common_vendor.m(($event) => $data.requestReason = $event.detail.value, {
      trim: true
    })),
    P: common_vendor.o((...args) => $options.submitSpotRequest && $options.submitSpotRequest(...args)),
    Q: common_vendor.f($data.myRequests, (item, k0, i0) => {
      return {
        a: common_vendor.t(item.id),
        b: common_vendor.t($options.actionText(item.action)),
        c: common_vendor.t($options.statusText(item.status)),
        d: common_vendor.t(item.target_zone ? item.target_zone + "区" : "-"),
        e: common_vendor.t(item.target_spot_id || "-"),
        f: item.id
      };
    }),
    R: $data.myRequests.length === 0
  }, $data.myRequests.length === 0 ? {} : {}) : {}, {
    S: $options.isAdmin
  }, $options.isAdmin ? common_vendor.e({
    T: common_vendor.f($data.pendingRequests, (item, k0, i0) => {
      return {
        a: common_vendor.t(item.user_id),
        b: common_vendor.t($options.actionText(item.action)),
        c: common_vendor.t(item.target_zone || "-"),
        d: common_vendor.t(item.target_spot_id || "-"),
        e: common_vendor.o(($event) => $options.reviewRequest(item.id, "approved"), item.id),
        f: common_vendor.o(($event) => $options.reviewRequest(item.id, "rejected"), item.id),
        g: item.id
      };
    }),
    U: $data.pendingRequests.length === 0
  }, $data.pendingRequests.length === 0 ? {} : {}) : {});
}
const MiniProgramPage = /* @__PURE__ */ common_vendor._export_sfc(_sfc_main, [["render", _sfc_render], ["__scopeId", "data-v-dd383ca2"]]);
wx.createPage(MiniProgramPage);
//# sourceMappingURL=../../../.sourcemap/mp-weixin/pages/profile/profile.js.map
