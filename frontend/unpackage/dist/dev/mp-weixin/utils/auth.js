"use strict";
const common_vendor = require("../common/vendor.js");
const TOKEN_KEY = "SP_TOKEN";
const USER_KEY = "SP_USER";
function saveAuth(token, user) {
  common_vendor.index.setStorageSync(TOKEN_KEY, token);
  common_vendor.index.setStorageSync(USER_KEY, user);
}
function clearAuth() {
  common_vendor.index.removeStorageSync(TOKEN_KEY);
  common_vendor.index.removeStorageSync(USER_KEY);
}
function getToken() {
  return common_vendor.index.getStorageSync(TOKEN_KEY);
}
function getUser() {
  return common_vendor.index.getStorageSync(USER_KEY);
}
exports.clearAuth = clearAuth;
exports.getToken = getToken;
exports.getUser = getUser;
exports.saveAuth = saveAuth;
//# sourceMappingURL=../../.sourcemap/mp-weixin/utils/auth.js.map
