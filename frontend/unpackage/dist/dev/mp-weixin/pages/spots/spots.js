"use strict";
const common_vendor = require("../../common/vendor.js");
const utils_request = require("../../utils/request.js");
const _sfc_main = {
  data() {
    return {
      spots: [],
      zone: "all",
      tabs: [
        { label: "全部", value: "all" },
        { label: "A 区", value: "A" },
        { label: "B 区", value: "B" },
        { label: "C 区", value: "C" }
      ]
    };
  },
  computed: {
    filteredSpots() {
      if (this.zone === "all")
        return this.spots;
      return this.spots.filter((item) => item.zone === this.zone);
    }
  },
  onShow() {
    this.loadSpots();
  },
  onPullDownRefresh() {
    this.loadSpots().finally(() => common_vendor.index.stopPullDownRefresh());
  },
  methods: {
    changeZone(value) {
      this.zone = value;
    },
    statusText(status) {
      switch (status) {
        case "free":
          return "空闲";
        case "occupied":
          return "占用";
        case "reserved":
          return "预留";
        default:
          return status;
      }
    },
    async loadSpots() {
      try {
        const res = await utils_request.request({ url: "/spots" });
        this.spots = res.data.items;
      } catch (error) {
        common_vendor.index.__f__("error", "at pages/spots/spots.vue:71", error);
      }
    }
  }
};
function _sfc_render(_ctx, _cache, $props, $setup, $data, $options) {
  return {
    a: common_vendor.f($data.tabs, (tab, k0, i0) => {
      return {
        a: common_vendor.t(tab.label),
        b: tab.value,
        c: $data.zone === tab.value ? "primary" : "default",
        d: common_vendor.o(($event) => $options.changeZone(tab.value), tab.value)
      };
    }),
    b: common_vendor.f($options.filteredSpots, (spot, k0, i0) => {
      return {
        a: common_vendor.t(spot.spot_number),
        b: common_vendor.t(spot.zone),
        c: common_vendor.t($options.statusText(spot.status)),
        d: common_vendor.n(spot.status),
        e: common_vendor.t(spot.is_shared ? "是" : "否"),
        f: common_vendor.t(spot.x_pos),
        g: common_vendor.t(spot.y_pos),
        h: spot.id
      };
    })
  };
}
const MiniProgramPage = /* @__PURE__ */ common_vendor._export_sfc(_sfc_main, [["render", _sfc_render], ["__scopeId", "data-v-efb29473"]]);
wx.createPage(MiniProgramPage);
//# sourceMappingURL=../../../.sourcemap/mp-weixin/pages/spots/spots.js.map
