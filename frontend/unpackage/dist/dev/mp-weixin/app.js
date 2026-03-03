"use strict";
Object.defineProperty(exports, Symbol.toStringTag, { value: "Module" });
const common_vendor = require("./common/vendor.js");
if (!Math) {
  "./pages/login/login.js";
  "./pages/index/index.js";
  "./pages/spots/spots.js";
  "./pages/simulate/simulate.js";
  "./pages/navigation/navigation.js";
  "./pages/predict/predict.js";
  "./pages/records/records.js";
  "./pages/profile/profile.js";
}
const _sfc_main = {
  onLaunch() {
    common_vendor.index.__f__("log", "at App.vue:4", "App Launch");
  },
  onShow() {
    common_vendor.index.__f__("log", "at App.vue:7", "App Show");
  },
  onHide() {
    common_vendor.index.__f__("log", "at App.vue:10", "App Hide");
  }
};
function createApp() {
  const app = common_vendor.createSSRApp(_sfc_main);
  return {
    app
  };
}
createApp().app.mount("#app");
exports.createApp = createApp;
//# sourceMappingURL=../.sourcemap/mp-weixin/app.js.map
