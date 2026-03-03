"use strict";
const common_vendor = require("../../common/vendor.js");
const utils_request = require("../../utils/request.js");
const _sfc_main = {
  data() {
    return {
      entryMode: "manual",
      exitMode: "manual",
      entryStep: 0,
      exitStep: 0,
      entryLoading: false,
      exitLoading: false,
      entryImagePath: "",
      exitImagePath: "",
      entryForm: { plate_number: "", vehicle_brand: "", vehicle_color: "" },
      exitForm: { plate_number: "" },
      recognizeResult: null,
      entryResult: null,
      exitResult: null
    };
  },
  methods: {
    isPossiblePlate(text) {
      if (!text || text === "未知")
        return false;
      return /^[\u4e00-\u9fa5][A-Z][A-Z0-9]{5,7}$/.test(String(text).toUpperCase());
    },
    // 选择入场图片
    chooseEntryImage() {
      common_vendor.index.chooseImage({
        count: 1,
        sourceType: ["album", "camera"],
        success: (res) => {
          this.entryImagePath = res.tempFilePaths[0];
          this.entryStep = 1;
          this.recognizeImage(res.tempFilePaths[0]);
        }
      });
    },
    // 选择出场图片
    chooseExitImage() {
      common_vendor.index.chooseImage({
        count: 1,
        sourceType: ["album", "camera"],
        success: (res) => {
          this.exitImagePath = res.tempFilePaths[0];
          this.exitStep = 1;
        }
      });
    },
    // 调用车牌识别接口
    async recognizeImage(filePath) {
      try {
        const result = await utils_request.uploadFile({
          url: "/recognize/",
          filePath,
          name: "file"
        });
        if (result.data) {
          this.recognizeResult = result.data;
          if (this.isPossiblePlate(result.data.plate_number)) {
            this.entryForm.plate_number = result.data.plate_number;
            this.entryStep = 2;
          } else {
            this.entryForm.plate_number = "";
            this.entryMode = "manual";
            common_vendor.index.showToast({ title: "未识别到有效车牌，请手动输入", icon: "none" });
          }
        }
      } catch (error) {
        common_vendor.index.__f__("error", "at pages/simulate/simulate.vue:196", "识别失败:", error);
        common_vendor.index.showToast({ title: "识别失败，请手动输入", icon: "none" });
      }
    },
    // 入场处理
    async handleEntry() {
      if (!this.isPossiblePlate(this.entryForm.plate_number)) {
        common_vendor.index.showToast({ title: "请输入车牌号或上传图片", icon: "none" });
        return;
      }
      this.entryForm.plate_number = this.entryForm.plate_number.toUpperCase();
      this.entryLoading = true;
      try {
        const res = await utils_request.request({
          url: "/parking/entry",
          method: "POST",
          data: this.entryForm
        });
        this.entryResult = res.data;
        this.entryStep = 3;
        common_vendor.index.showToast({ title: "入场成功", icon: "success" });
      } catch (error) {
        common_vendor.index.__f__("error", "at pages/simulate/simulate.vue:218", error);
      } finally {
        this.entryLoading = false;
      }
    },
    // 出场处理
    async handleExit() {
      let plateNumber = this.exitForm.plate_number;
      if (this.exitMode === "image" && this.exitImagePath) {
        try {
          const result = await utils_request.uploadFile({
            url: "/recognize/",
            filePath: this.exitImagePath,
            name: "file"
          });
          if (result.data) {
            if (!this.isPossiblePlate(result.data.plate_number)) {
              common_vendor.index.showToast({ title: "未识别到有效车牌，请手动输入", icon: "none" });
              return;
            }
            plateNumber = result.data.plate_number;
            this.exitStep = 1;
          }
        } catch (error) {
          common_vendor.index.showToast({ title: "识别失败", icon: "none" });
          return;
        }
      }
      if (!this.isPossiblePlate(plateNumber)) {
        common_vendor.index.showToast({ title: "请输入车牌号或上传图片", icon: "none" });
        return;
      }
      plateNumber = plateNumber.toUpperCase();
      this.exitLoading = true;
      try {
        const res = await utils_request.request({
          url: "/parking/exit",
          method: "POST",
          data: { plate_number: plateNumber }
        });
        this.exitResult = res.data;
        this.exitStep = 2;
        common_vendor.index.showToast({ title: "结算完成", icon: "success" });
      } catch (error) {
        common_vendor.index.__f__("error", "at pages/simulate/simulate.vue:263", error);
      } finally {
        this.exitLoading = false;
      }
    },
    // 模拟支付
    simulatePay() {
      common_vendor.index.showModal({
        title: "模拟支付",
        content: `确认支付 ¥${this.exitResult.fee.toFixed(2)}？`,
        success: async (res) => {
          if (!res.confirm)
            return;
          try {
            const payRes = await utils_request.request({
              url: "/parking/pay",
              method: "POST",
              data: { record_id: this.exitResult.record_id }
            });
            this.exitResult.status = payRes.data.status;
            this.exitStep = 3;
            common_vendor.index.showToast({ title: "支付成功", icon: "success" });
          } catch (error) {
            common_vendor.index.__f__("error", "at pages/simulate/simulate.vue:285", error);
          }
        }
      });
    },
    // 跳转导航
    goNavigation(spotId) {
      common_vendor.index.navigateTo({ url: `/pages/navigation/navigation?spotId=${spotId}` });
    }
  }
};
function _sfc_render(_ctx, _cache, $props, $setup, $data, $options) {
  var _a, _b;
  return common_vendor.e({
    a: $data.entryStep >= 1 ? 1 : "",
    b: $data.entryStep >= 2 ? 1 : "",
    c: $data.entryStep >= 2 ? 1 : "",
    d: $data.entryStep >= 3 ? 1 : "",
    e: $data.entryStep >= 3 ? 1 : "",
    f: $data.entryMode === "image" ? "primary" : "default",
    g: common_vendor.o(($event) => $data.entryMode = "image"),
    h: $data.entryMode === "manual" ? "primary" : "default",
    i: common_vendor.o(($event) => $data.entryMode = "manual"),
    j: $data.entryMode === "image"
  }, $data.entryMode === "image" ? common_vendor.e({
    k: $data.entryImagePath
  }, $data.entryImagePath ? {
    l: $data.entryImagePath
  } : {}, {
    m: common_vendor.o((...args) => $options.chooseEntryImage && $options.chooseEntryImage(...args))
  }) : {}, {
    n: $data.entryMode === "manual"
  }, $data.entryMode === "manual" ? {
    o: $data.entryForm.plate_number,
    p: common_vendor.o(($event) => $data.entryForm.plate_number = $event.detail.value),
    q: $data.entryForm.vehicle_brand,
    r: common_vendor.o(($event) => $data.entryForm.vehicle_brand = $event.detail.value),
    s: $data.entryForm.vehicle_color,
    t: common_vendor.o(($event) => $data.entryForm.vehicle_color = $event.detail.value)
  } : {}, {
    v: $data.recognizeResult
  }, $data.recognizeResult ? {
    w: common_vendor.t($data.recognizeResult.plate_number),
    x: common_vendor.t(($data.recognizeResult.confidence * 100).toFixed(1)),
    y: common_vendor.t($data.recognizeResult.is_resident ? "小区车辆" : "外来车辆"),
    z: common_vendor.n($data.recognizeResult.is_resident ? "resident" : "visitor")
  } : {}, {
    A: common_vendor.t($data.entryMode === "image" ? "上传识别并入场" : "模拟入场"),
    B: common_vendor.o((...args) => $options.handleEntry && $options.handleEntry(...args)),
    C: $data.entryLoading,
    D: $data.entryResult
  }, $data.entryResult ? common_vendor.e({
    E: common_vendor.t($data.entryResult.plate_number),
    F: common_vendor.t(((_a = $data.entryResult.spot) == null ? void 0 : _a.spot_number) || "等待分配"),
    G: common_vendor.t(((_b = $data.entryResult.spot) == null ? void 0 : _b.zone) || "-"),
    H: common_vendor.t($data.entryResult.is_resident ? "小区车辆（免费）" : "外来车辆（计时收费）"),
    I: common_vendor.n($data.entryResult.is_resident ? "text-green" : "text-orange"),
    J: $data.entryResult.spot
  }, $data.entryResult.spot ? {
    K: common_vendor.o(($event) => $options.goNavigation($data.entryResult.spot.id))
  } : {}) : {}, {
    L: $data.exitStep >= 1 ? 1 : "",
    M: $data.exitStep >= 2 ? 1 : "",
    N: $data.exitStep >= 2 ? 1 : "",
    O: $data.exitStep >= 3 ? 1 : "",
    P: $data.exitStep >= 3 ? 1 : "",
    Q: $data.exitMode === "image" ? "primary" : "default",
    R: common_vendor.o(($event) => $data.exitMode = "image"),
    S: $data.exitMode === "manual" ? "primary" : "default",
    T: common_vendor.o(($event) => $data.exitMode = "manual"),
    U: $data.exitMode === "image"
  }, $data.exitMode === "image" ? common_vendor.e({
    V: $data.exitImagePath
  }, $data.exitImagePath ? {
    W: $data.exitImagePath
  } : {}, {
    X: common_vendor.o((...args) => $options.chooseExitImage && $options.chooseExitImage(...args))
  }) : {}, {
    Y: $data.exitMode === "manual"
  }, $data.exitMode === "manual" ? {
    Z: $data.exitForm.plate_number,
    aa: common_vendor.o(($event) => $data.exitForm.plate_number = $event.detail.value)
  } : {}, {
    ab: common_vendor.t($data.exitMode === "image" ? "上传识别并出场" : "模拟出场"),
    ac: common_vendor.o((...args) => $options.handleExit && $options.handleExit(...args)),
    ad: $data.exitLoading,
    ae: $data.exitResult
  }, $data.exitResult ? common_vendor.e({
    af: common_vendor.t($data.exitResult.plate_number),
    ag: common_vendor.t($data.exitResult.duration_minutes),
    ah: common_vendor.t($data.exitResult.fee.toFixed(2)),
    ai: common_vendor.n($data.exitResult.fee > 0 ? "text-orange" : "text-green"),
    aj: common_vendor.t($data.exitResult.is_resident ? "小区车辆免费" : $data.exitResult.fee > 0 ? "待支付" : "已结算"),
    ak: $data.exitResult.fee > 0 && $data.exitResult.status === "exited"
  }, $data.exitResult.fee > 0 && $data.exitResult.status === "exited" ? {
    al: common_vendor.t($data.exitResult.fee.toFixed(2)),
    am: common_vendor.o((...args) => $options.simulatePay && $options.simulatePay(...args))
  } : {}, {
    an: common_vendor.n($data.exitResult && $data.exitResult.fee > 0 ? "warning" : "success")
  }) : {});
}
const MiniProgramPage = /* @__PURE__ */ common_vendor._export_sfc(_sfc_main, [["render", _sfc_render], ["__scopeId", "data-v-19dd6a4c"]]);
wx.createPage(MiniProgramPage);
//# sourceMappingURL=../../../.sourcemap/mp-weixin/pages/simulate/simulate.js.map
