"use strict";
const common_vendor = require("../../common/vendor.js");
const utils_request = require("../../utils/request.js");
const _sfc_main = {
  data() {
    return {
      page: 1,
      size: 10,
      total: 0,
      loading: false,
      records: []
    };
  },
  computed: {
    footerText() {
      if (this.total === 0 && !this.loading) {
        return "暂无记录";
      }
      if (this.records.length >= this.total && this.total !== 0) {
        return "没有更多了";
      }
      return "上拉加载更多";
    }
  },
  onShow() {
    this.reset();
  },
  methods: {
    reset() {
      this.page = 1;
      this.records = [];
      this.total = 0;
      this.loadRecords();
    },
    formatTime(time) {
      return time ? time.replace("T", " ").slice(0, 16) : "--";
    },
    async loadRecords() {
      if (this.loading)
        return;
      if (this.records.length >= this.total && this.total !== 0)
        return;
      this.loading = true;
      try {
        const res = await utils_request.request({ url: `/parking/records?page=${this.page}&size=${this.size}` });
        const { items, total } = res.data;
        this.records = this.records.concat(items);
        this.total = total;
        this.page += 1;
      } catch (error) {
        common_vendor.index.__f__("error", "at pages/records/records.vue:66", error);
      } finally {
        this.loading = false;
      }
    },
    loadMore() {
      this.loadRecords();
    }
  }
};
function _sfc_render(_ctx, _cache, $props, $setup, $data, $options) {
  return {
    a: common_vendor.f($data.records, (item, k0, i0) => {
      return {
        a: common_vendor.t(item.plate_number),
        b: common_vendor.t(item.status),
        c: common_vendor.t($options.formatTime(item.entry_time)),
        d: common_vendor.t(item.exit_time ? $options.formatTime(item.exit_time) : "未出场"),
        e: common_vendor.t(item.fee),
        f: item.id
      };
    }),
    b: common_vendor.t($options.footerText),
    c: common_vendor.o((...args) => $options.loadMore && $options.loadMore(...args))
  };
}
const MiniProgramPage = /* @__PURE__ */ common_vendor._export_sfc(_sfc_main, [["render", _sfc_render], ["__scopeId", "data-v-cb371200"]]);
wx.createPage(MiniProgramPage);
//# sourceMappingURL=../../../.sourcemap/mp-weixin/pages/records/records.js.map
