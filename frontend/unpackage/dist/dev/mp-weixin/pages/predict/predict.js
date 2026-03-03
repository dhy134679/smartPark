"use strict";
const common_vendor = require("../../common/vendor.js");
const utils_request = require("../../utils/request.js");
const _sfc_main = {
  data() {
    return {
      horizon: 12,
      trend: [],
      availability: []
    };
  },
  onShow() {
    this.loadData();
  },
  methods: {
    formatTime(ts) {
      const date = new Date(ts);
      return `${date.getMonth() + 1}/${date.getDate()} ${date.getHours()}:00`;
    },
    async loadData() {
      try {
        const [trendRes, availabilityRes] = await Promise.all([
          utils_request.request({ url: `/predict/trend?horizon=${this.horizon}` }),
          utils_request.request({ url: "/predict/availability" })
        ]);
        this.trend = trendRes.data.trend;
        this.availability = availabilityRes.data.availability;
      } catch (error) {
        common_vendor.index.__f__("error", "at pages/predict/predict.vue:51", error);
      }
    },
    onHorizonChange(e) {
      this.horizon = Number(e.detail.value);
      this.loadData();
    }
  }
};
function _sfc_render(_ctx, _cache, $props, $setup, $data, $options) {
  return {
    a: $data.horizon,
    b: common_vendor.o((...args) => $options.onHorizonChange && $options.onHorizonChange(...args)),
    c: common_vendor.t($data.horizon),
    d: common_vendor.f($data.trend, (item, k0, i0) => {
      return {
        a: common_vendor.t($options.formatTime(item.timestamp)),
        b: common_vendor.t(Math.round(item.occupancy_rate * 100)),
        c: item.timestamp
      };
    }),
    e: common_vendor.f($data.availability, (item, k0, i0) => {
      return {
        a: common_vendor.t($options.formatTime(item.timestamp)),
        b: common_vendor.t(item.available),
        c: item.timestamp
      };
    })
  };
}
const MiniProgramPage = /* @__PURE__ */ common_vendor._export_sfc(_sfc_main, [["render", _sfc_render], ["__scopeId", "data-v-a742fe29"]]);
wx.createPage(MiniProgramPage);
//# sourceMappingURL=../../../.sourcemap/mp-weixin/pages/predict/predict.js.map
