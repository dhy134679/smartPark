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
      myIncome: { total_income: 0, recent_details: [] },
      vehicleForm: {
        plate_number: "",
        brand: "",
        color: "",
        is_resident: true
      }
    };
  },
  onShow() {
    this.loadData();
  },
  methods: {
    toggleShare(index, value) {
      if (value) {
        const now = /* @__PURE__ */ new Date();
        const startStr = now.toISOString().replace("T", " ").slice(0, 19);
        const endStr = new Date(now.getTime() + 8 * 3600 * 1e3).toISOString().replace("T", " ").slice(0, 19);
        this.mySpots[index].shared_start = startStr;
        this.mySpots[index].shared_end = endStr;
      } else {
        this.mySpots[index].shared_start = null;
        this.mySpots[index].shared_end = null;
      }
      this.mySpots[index].is_shared = value;
      this.saveShare(this.mySpots[index]);
    },
    async saveShare(spot) {
      try {
        await utils_request.request({
          url: `/spots/${spot.id}/share`,
          method: "PUT",
          data: {
            is_shared: spot.is_shared,
            shared_start: spot.shared_start || null,
            shared_end: spot.shared_end || null
          }
        });
        common_vendor.index.showToast({ title: "共享设置已保存", icon: "success" });
      } catch (error) {
        common_vendor.index.showToast({ title: "设置失败", icon: "none" });
      }
    },
    async loadData() {
      try {
        const [profile, vehicles] = await Promise.all([
          utils_request.request({ url: "/auth/profile" }),
          utils_request.request({ url: "/vehicles" })
        ]);
        this.user = profile.data.user;
        this.vehicles = vehicles.data.items;
        if (this.user.role !== "guest" && this.user.role !== "admin") {
          const [spotsRes, incomeRes] = await Promise.all([
            utils_request.request({ url: "/spots/my" }),
            utils_request.request({ url: "/spots/my/income" })
          ]);
          this.mySpots = spotsRes.data.items;
          this.myIncome = incomeRes.data;
        }
      } catch (error) {
        common_vendor.index.__f__("error", "at pages/profile/profile.vue:153", error);
        if ((error == null ? void 0 : error.statusCode) === 401) {
          this.logout();
        }
      }
    },
    async addVehicle() {
      if (!this.vehicleForm.plate_number) {
        common_vendor.index.showToast({ title: "请输入车牌号", icon: "none" });
        return;
      }
      try {
        await utils_request.request({ url: "/vehicles", method: "POST", data: this.vehicleForm });
        common_vendor.index.showToast({ title: "添加成功", icon: "success" });
        this.vehicleForm = { plate_number: "", brand: "", color: "", is_resident: true };
        this.loadData();
      } catch (error) {
        common_vendor.index.__f__("error", "at pages/profile/profile.vue:170", error);
      }
    },
    async removeVehicle(id) {
      try {
        await utils_request.request({ url: `/vehicles/${id}`, method: "DELETE" });
        this.loadData();
      } catch (error) {
        common_vendor.index.__f__("error", "at pages/profile/profile.vue:178", error);
      }
    },
    logout() {
      utils_auth.clearAuth();
      common_vendor.index.reLaunch({ url: "/pages/login/login" });
    },
    openPage(url) {
      common_vendor.index.navigateTo({ url });
    }
  }
};
function _sfc_render(_ctx, _cache, $props, $setup, $data, $options) {
  return common_vendor.e({
    a: $data.user
  }, $data.user ? {
    b: common_vendor.t($data.user.name),
    c: common_vendor.t($data.user.phone),
    d: common_vendor.t($data.user.role),
    e: common_vendor.o((...args) => $options.logout && $options.logout(...args))
  } : {}, {
    f: $data.user && $data.user.role !== "guest"
  }, $data.user && $data.user.role !== "guest" ? {
    g: common_vendor.f($data.vehicles, (item, k0, i0) => {
      return {
        a: common_vendor.t(item.plate_number),
        b: common_vendor.t(item.brand || "-"),
        c: common_vendor.t(item.color || "-"),
        d: common_vendor.o(($event) => $options.removeVehicle(item.id), item.id),
        e: item.id
      };
    }),
    h: $data.vehicleForm.plate_number,
    i: common_vendor.o(($event) => $data.vehicleForm.plate_number = $event.detail.value),
    j: $data.vehicleForm.brand,
    k: common_vendor.o(($event) => $data.vehicleForm.brand = $event.detail.value),
    l: $data.vehicleForm.color,
    m: common_vendor.o(($event) => $data.vehicleForm.color = $event.detail.value),
    n: $data.vehicleForm.is_resident,
    o: common_vendor.o(($event) => $data.vehicleForm.is_resident = $event.detail.value),
    p: common_vendor.o((...args) => $options.addVehicle && $options.addVehicle(...args))
  } : {}, {
    q: $data.user && $data.user.role !== "guest" && $data.user.role !== "admin"
  }, $data.user && $data.user.role !== "guest" && $data.user.role !== "admin" ? common_vendor.e({
    r: $data.mySpots.length === 0
  }, $data.mySpots.length === 0 ? {} : {}, {
    s: common_vendor.f($data.mySpots, (spot, index, i0) => {
      return common_vendor.e({
        a: common_vendor.t(spot.spot_number),
        b: common_vendor.t(spot.zone),
        c: spot.is_shared,
        d: common_vendor.o((event) => $options.toggleShare(index, event.detail.value), spot.id),
        e: spot.is_shared
      }, spot.is_shared ? {
        f: spot.shared_start,
        g: common_vendor.o(($event) => spot.shared_start = $event.detail.value, spot.id),
        h: spot.shared_end,
        i: common_vendor.o(($event) => spot.shared_end = $event.detail.value, spot.id),
        j: common_vendor.o(($event) => $options.saveShare(spot), spot.id)
      } : {}, {
        k: spot.id
      });
    })
  }) : {}, {
    t: $data.user && $data.user.role !== "guest" && $data.user.role !== "admin"
  }, $data.user && $data.user.role !== "guest" && $data.user.role !== "admin" ? common_vendor.e({
    v: common_vendor.t($data.myIncome.total_income || "0.00"),
    w: common_vendor.f($data.myIncome.recent_details, (log, idx, i0) => {
      return {
        a: common_vendor.t(log.time),
        b: common_vendor.t(log.plate_number),
        c: common_vendor.t(log.amount),
        d: idx
      };
    }),
    x: !$data.myIncome.recent_details || $data.myIncome.recent_details.length === 0
  }, !$data.myIncome.recent_details || $data.myIncome.recent_details.length === 0 ? {} : {}) : {}, {
    y: common_vendor.o(($event) => $options.openPage("/pages/records/records")),
    z: common_vendor.o(($event) => $options.openPage("/pages/simulate/simulate"))
  });
}
const MiniProgramPage = /* @__PURE__ */ common_vendor._export_sfc(_sfc_main, [["render", _sfc_render], ["__scopeId", "data-v-dd383ca2"]]);
wx.createPage(MiniProgramPage);
//# sourceMappingURL=../../../.sourcemap/mp-weixin/pages/profile/profile.js.map
