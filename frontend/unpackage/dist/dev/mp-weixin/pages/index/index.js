"use strict";
const common_vendor = require("../../common/vendor.js");
const utils_request = require("../../utils/request.js");
const utils_auth = require("../../utils/auth.js");
const _sfc_main = {
  data() {
    return {
      summary: { total: 0, free: 0, occupied: 0, reserved: 0, shared: 0 },
      statistics: { entries_today: 0, exits_today: 0, occupied_spots: 0, revenue_today: 0 },
      availability: { recommended_time: "", availability: [] },
      user: null
    };
  },
  computed: {
    summaryCards() {
      var _a, _b, _c;
      const cards = [];
      if (((_a = this.user) == null ? void 0 : _a.role) === "admin") {
        cards.push({ label: "总车位", value: this.summary.total, type: "primary" });
      }
      cards.push({ label: "当前空闲", value: this.summary.free, type: "success" });
      if (((_b = this.user) == null ? void 0 : _b.role) === "admin") {
        cards.push({ label: "已占用", value: this.summary.occupied, type: "danger" });
      }
      if (((_c = this.user) == null ? void 0 : _c.role) !== "guest") {
        cards.push({ label: "共享开放", value: this.summary.shared, type: "warning" });
      }
      return cards;
    }
  },
  onShow() {
    this.user = utils_auth.getUser();
    if (!this.user) {
      common_vendor.index.reLaunch({ url: "/pages/login/login" });
      return;
    }
    this.fetchData();
  },
  methods: {
    goTo(url) {
      common_vendor.index.navigateTo({ url });
    },
    formatHour(timestamp) {
      if (!timestamp)
        return "--";
      const date = new Date(timestamp);
      return `${date.getHours()}:00`;
    },
    async fetchData() {
      try {
        const [summary, statistics, availability] = await Promise.all([
          utils_request.request({ url: "/spots/summary" }),
          utils_request.request({ url: "/parking/statistics" }),
          utils_request.request({ url: "/predict/availability" })
        ]);
        this.summary = summary.data;
        this.statistics = statistics.data;
        this.availability = availability.data;
      } catch (error) {
        common_vendor.index.__f__("error", "at pages/index/index.vue:115", error);
      }
    }
  }
};
function _sfc_render(_ctx, _cache, $props, $setup, $data, $options) {
  var _a, _b, _c, _d, _e, _f, _g, _h, _i;
  return common_vendor.e({
    a: common_vendor.t(((_a = $data.user) == null ? void 0 : _a.name) || "访客"),
    b: ((_b = $data.user) == null ? void 0 : _b.role) !== "guest"
  }, ((_c = $data.user) == null ? void 0 : _c.role) !== "guest" ? {
    c: common_vendor.o(($event) => $options.goTo("/pages/profile/profile"))
  } : {}, {
    d: ((_d = $data.user) == null ? void 0 : _d.role) === "admin" || ((_e = $data.user) == null ? void 0 : _e.role) === "guest"
  }, ((_f = $data.user) == null ? void 0 : _f.role) === "admin" || ((_g = $data.user) == null ? void 0 : _g.role) === "guest" ? {
    e: common_vendor.o(($event) => $options.goTo("/pages/simulate/simulate"))
  } : {}, {
    f: common_vendor.o(($event) => $options.goTo("/pages/predict/predict")),
    g: common_vendor.f($options.summaryCards, (item, k0, i0) => {
      return {
        a: common_vendor.t(item.label),
        b: common_vendor.t(item.value),
        c: item.label,
        d: common_vendor.n(item.type)
      };
    }),
    h: ((_h = $data.user) == null ? void 0 : _h.role) === "admin"
  }, ((_i = $data.user) == null ? void 0 : _i.role) === "admin" ? {
    i: common_vendor.t($data.statistics.entries_today),
    j: common_vendor.t($data.statistics.exits_today),
    k: common_vendor.t($data.statistics.occupied_spots),
    l: common_vendor.t($data.statistics.revenue_today)
  } : {}, {
    m: common_vendor.t($data.availability.recommended_time || "---"),
    n: common_vendor.f($data.availability.availability, (item, k0, i0) => {
      return {
        a: common_vendor.t($options.formatHour(item.timestamp)),
        b: common_vendor.t(item.available),
        c: item.timestamp
      };
    })
  });
}
const MiniProgramPage = /* @__PURE__ */ common_vendor._export_sfc(_sfc_main, [["render", _sfc_render], ["__scopeId", "data-v-1cf27b2a"]]);
wx.createPage(MiniProgramPage);
//# sourceMappingURL=../../../.sourcemap/mp-weixin/pages/index/index.js.map
