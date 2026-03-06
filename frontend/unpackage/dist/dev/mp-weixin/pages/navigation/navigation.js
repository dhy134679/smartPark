"use strict";
const common_vendor = require("../../common/vendor.js");
const utils_request = require("../../utils/request.js");
const utils_auth = require("../../utils/auth.js");
const GRID_SIZE = 28;
const SAFE_PADDING = 24;
const COLORS = {
  background: "#f0f2f5",
  road: "#e8eaed",
  free: "#4caf50",
  occupied: "#ef5350",
  reserved: "#ff9800",
  route: "#2196f3",
  routeHead: "#1565c0",
  entry: "#9c27b0"
};
const _sfc_main = {
  data() {
    return {
      user: null,
      keyword: "",
      users: [],
      spots: [],
      vehicles: [],
      createForm: {
        name: "",
        phone: "",
        password: ""
      },
      createLoading: false,
      editingUserId: null,
      editForm: {
        name: "",
        phone: "",
        role: "resident",
        is_resident: true
      },
      roleOptions: [
        { label: "住户", value: "resident" },
        { label: "管理员", value: "admin" },
        { label: "访客", value: "guest" }
      ],
      assignSelections: {},
      assignZoneSelections: {},
      assignZones: ["A", "B", "C", "D"],
      vehicleForms: {},
      mapInfo: null,
      allSpots: [],
      selectedZone: "全部",
      selectedSpot: null,
      routePath: [],
      preSelectedSpotId: null,
      cellSize: GRID_SIZE,
      canvasWidth: 0,
      canvasHeight: 0
    };
  },
  computed: {
    isAdmin() {
      return this.user && this.user.role === "admin";
    },
    freeSpots() {
      return this.allSpots.filter((spot) => spot.status === "free");
    },
    filteredFreeSpots() {
      if (this.selectedZone === "全部")
        return this.freeSpots;
      return this.freeSpots.filter((spot) => spot.zone === this.selectedZone);
    },
    estimatedMinutes() {
      if (this.routePath.length <= 1)
        return 0;
      const walkingSpeedStepPerMinute = 75;
      return Math.max(1, Math.ceil((this.routePath.length - 1) / walkingSpeedStepPerMinute));
    },
    canvasStyle() {
      return `width:${this.canvasWidth}px;height:${this.canvasHeight}px;`;
    },
    routeInstructions() {
      if (this.routePath.length <= 1)
        return [];
      const instructions = [];
      let prevDirection = "";
      let stepCount = 0;
      for (let idx = 1; idx < this.routePath.length; idx++) {
        const prev = this.routePath[idx - 1];
        const current = this.routePath[idx];
        const direction = this.getDirection(prev, current);
        if (!prevDirection) {
          prevDirection = direction;
          stepCount = 1;
          continue;
        }
        if (direction === prevDirection) {
          stepCount += 1;
        } else {
          instructions.push(`向${prevDirection}直行 ${stepCount} 步`);
          prevDirection = direction;
          stepCount = 1;
        }
      }
      if (stepCount > 0) {
        instructions.push(`向${prevDirection}直行 ${stepCount} 步`);
      }
      instructions.push("到达目标车位附近，请减速并观察车位编号");
      return instructions;
    }
  },
  onLoad(options) {
    if (options && options.spotId) {
      this.preSelectedSpotId = parseInt(options.spotId);
    }
  },
  onShow() {
    this.user = utils_auth.getUser();
    if (!this.user) {
      common_vendor.index.reLaunch({ url: "/pages/login/login" });
      return;
    }
    if (this.isAdmin) {
      this.loadAdminData();
      return;
    }
    this.loadMap();
  },
  onPullDownRefresh() {
    const task = this.isAdmin ? this.loadAdminData() : this.loadMap();
    Promise.resolve(task).finally(() => common_vendor.index.stopPullDownRefresh());
  },
  methods: {
    roleText(role) {
      if (role === "admin")
        return "管理员";
      if (role === "guest")
        return "访客";
      return "住户";
    },
    roleLabel(role) {
      const target = this.roleOptions.find((item) => item.value === role);
      return target ? target.label : "住户";
    },
    startEdit(user) {
      this.editingUserId = user.id;
      this.editForm = {
        name: user.name,
        phone: user.phone,
        role: user.role,
        is_resident: user.is_resident
      };
    },
    cancelEdit() {
      this.editingUserId = null;
      this.editForm = {
        name: "",
        phone: "",
        role: "resident",
        is_resident: true
      };
    },
    onEditRoleChange(event) {
      const idx = Number(event.detail.value);
      const option = this.roleOptions[idx];
      if (!option)
        return;
      this.editForm.role = option.value;
      if (option.value === "guest") {
        this.editForm.is_resident = false;
      }
    },
    async loadAdminData() {
      try {
        const [usersRes, spotsRes, vehiclesRes] = await Promise.all([
          utils_request.request({
            url: "/auth/users",
            data: this.keyword ? { keyword: this.keyword } : {}
          }),
          utils_request.request({ url: "/spots" }),
          utils_request.request({ url: "/vehicles/admin" })
        ]);
        this.users = usersRes.data.items || [];
        this.spots = spotsRes.data.items || [];
        this.vehicles = vehiclesRes.data.items || [];
        this.syncVehicleForms();
      } catch (error) {
        common_vendor.index.__f__("error", "at pages/navigation/navigation.vue:395", error);
      }
    },
    syncVehicleForms() {
      const nextForms = {};
      for (const item of this.users) {
        const existing = this.vehicleForms[item.id];
        nextForms[item.id] = existing || {
          plate_number: "",
          brand: "",
          color: "",
          is_resident: true
        };
      }
      this.vehicleForms = nextForms;
    },
    async createUser() {
      if (!this.createForm.name || !this.createForm.phone || !this.createForm.password) {
        common_vendor.index.showToast({ title: "请填写完整信息", icon: "none" });
        return;
      }
      this.createLoading = true;
      try {
        await utils_request.request({
          url: "/auth/users",
          method: "POST",
          data: this.createForm
        });
        common_vendor.index.showToast({ title: "新增成功", icon: "success" });
        this.createForm = { name: "", phone: "", password: "" };
        await this.loadAdminData();
      } catch (error) {
        common_vendor.index.__f__("error", "at pages/navigation/navigation.vue:427", error);
      } finally {
        this.createLoading = false;
      }
    },
    async saveEdit(userId) {
      if (!this.editForm.name || !this.editForm.phone) {
        common_vendor.index.showToast({ title: "姓名和手机号不能为空", icon: "none" });
        return;
      }
      try {
        await utils_request.request({
          url: `/auth/users/${userId}`,
          method: "PUT",
          data: this.editForm
        });
        common_vendor.index.showToast({ title: "保存成功", icon: "success" });
        this.cancelEdit();
        await this.loadAdminData();
      } catch (error) {
        common_vendor.index.__f__("error", "at pages/navigation/navigation.vue:447", error);
      }
    },
    deleteUser(user) {
      common_vendor.index.showModal({
        title: "确认删除",
        content: `确定删除用户 ${user.name} 吗？`,
        success: async (res) => {
          if (!res.confirm)
            return;
          try {
            await utils_request.request({
              url: `/auth/users/${user.id}`,
              method: "DELETE"
            });
            common_vendor.index.showToast({ title: "删除成功", icon: "success" });
            await this.loadAdminData();
          } catch (error) {
            common_vendor.index.__f__("error", "at pages/navigation/navigation.vue:464", error);
          }
        }
      });
    },
    ownedSpots(userId) {
      return this.spots.filter((spot) => spot.owner_id === userId);
    },
    userVehicles(userId) {
      return this.vehicles.filter((vehicle) => vehicle.owner_id === userId);
    },
    vehicleForm(userId) {
      return this.vehicleForms[userId] || {
        plate_number: "",
        brand: "",
        color: "",
        is_resident: true
      };
    },
    assignableSpots(userId) {
      const selectedZone = this.assignZoneSelections[userId];
      return this.spots.filter((spot) => spot.owner_id === null || spot.owner_id === userId).filter((spot) => !selectedZone || spot.zone === selectedZone).map((spot) => ({
        id: spot.id,
        label: `${spot.spot_number} (${spot.zone}区)`
      }));
    },
    onAssignZoneChange(userId, event) {
      const idx = Number(event.detail.value);
      const zone = this.assignZones[idx];
      if (!zone)
        return;
      this.assignZoneSelections[userId] = zone;
      this.assignSelections[userId] = null;
    },
    assignZoneLabel(userId) {
      return this.assignZoneSelections[userId] ? `${this.assignZoneSelections[userId]}区` : "请选择目标区域";
    },
    onAssignSpotChange(userId, event) {
      const idx = Number(event.detail.value);
      const options = this.assignableSpots(userId);
      const option = options[idx];
      if (!option)
        return;
      this.assignSelections[userId] = option.id;
    },
    assignLabel(userId) {
      const spotId = this.assignSelections[userId];
      if (!spotId)
        return "请选择可分配车位";
      const spot = this.spots.find((item) => item.id === spotId);
      return spot ? `${spot.spot_number} (${spot.zone}区)` : "请选择可分配车位";
    },
    async assignSpot(userId) {
      const spotId = this.assignSelections[userId];
      if (!spotId) {
        common_vendor.index.showToast({ title: "请先选择车位", icon: "none" });
        return;
      }
      try {
        await utils_request.request({
          url: `/spots/${spotId}/owner`,
          method: "PUT",
          data: { owner_id: userId }
        });
        common_vendor.index.showToast({ title: "分配成功", icon: "success" });
        await this.loadAdminData();
      } catch (error) {
        common_vendor.index.__f__("error", "at pages/navigation/navigation.vue:533", error);
      }
    },
    async releaseSpot(spotId) {
      try {
        await utils_request.request({
          url: `/spots/${spotId}/owner`,
          method: "PUT",
          data: { owner_id: null }
        });
        common_vendor.index.showToast({ title: "已释放", icon: "success" });
        await this.loadAdminData();
      } catch (error) {
        common_vendor.index.__f__("error", "at pages/navigation/navigation.vue:546", error);
      }
    },
    async addVehicleForUser(userId) {
      const form = this.vehicleForm(userId);
      if (!form.plate_number) {
        common_vendor.index.showToast({ title: "请输入车牌号", icon: "none" });
        return;
      }
      try {
        await utils_request.request({
          url: `/vehicles/admin/users/${userId}`,
          method: "POST",
          data: form
        });
        common_vendor.index.showToast({ title: "车辆添加成功", icon: "success" });
        this.vehicleForms[userId] = {
          plate_number: "",
          brand: "",
          color: "",
          is_resident: true
        };
        await this.loadAdminData();
      } catch (error) {
        common_vendor.index.__f__("error", "at pages/navigation/navigation.vue:570", error);
      }
    },
    async deleteVehicleForUser(vehicleId) {
      try {
        await utils_request.request({
          url: `/vehicles/admin/${vehicleId}`,
          method: "DELETE"
        });
        common_vendor.index.showToast({ title: "车辆已删除", icon: "success" });
        await this.loadAdminData();
      } catch (error) {
        common_vendor.index.__f__("error", "at pages/navigation/navigation.vue:582", error);
      }
    },
    filterZone(zone) {
      this.selectedZone = zone;
    },
    // 计算方向文本（用于静态路线说明）
    getDirection(from, to) {
      if (to.x > from.x)
        return "右";
      if (to.x < from.x)
        return "左";
      if (to.y > from.y)
        return "下";
      return "上";
    },
    // 根据屏幕宽度动态计算画布尺寸，避免不同机型上被裁切
    updateCanvasSize() {
      var _a, _b;
      const systemInfo = common_vendor.index.getSystemInfoSync();
      const containerWidth = systemInfo.windowWidth - SAFE_PADDING;
      const gw = ((_a = this.mapInfo) == null ? void 0 : _a.width) || 24;
      const gh = ((_b = this.mapInfo) == null ? void 0 : _b.height) || 18;
      const nextCellSize = Math.max(12, Math.floor(containerWidth / gw));
      this.cellSize = nextCellSize;
      this.canvasWidth = gw * nextCellSize;
      this.canvasHeight = gh * nextCellSize;
    },
    selectSpot(spot) {
      this.selectedSpot = spot;
      this.planRoute();
    },
    async loadMap() {
      try {
        const res = await utils_request.request({ url: "/navigation/map" });
        this.mapInfo = res.data;
        this.allSpots = res.data.spots || [];
        this.updateCanvasSize();
        if (this.preSelectedSpotId) {
          const target = this.allSpots.find((spot) => spot.id === this.preSelectedSpotId);
          if (target) {
            this.selectedSpot = target;
            await this.planRoute();
            return;
          }
        }
        this.drawMap();
      } catch (error) {
        common_vendor.index.__f__("error", "at pages/navigation/navigation.vue:628", error);
      }
    },
    async planRoute() {
      if (!this.selectedSpot)
        return;
      try {
        const res = await utils_request.request({
          url: "/navigation/route",
          method: "POST",
          data: { spot_id: this.selectedSpot.id }
        });
        this.routePath = res.data.route || [];
        this.drawMap();
      } catch (error) {
        common_vendor.index.__f__("error", "at pages/navigation/navigation.vue:642", error);
      }
    },
    drawMap() {
      var _a, _b, _c;
      const ctx = common_vendor.index.createCanvasContext("parkingMap", this);
      const gw = ((_a = this.mapInfo) == null ? void 0 : _a.width) || 24;
      const gh = ((_b = this.mapInfo) == null ? void 0 : _b.height) || 18;
      const size = this.cellSize || GRID_SIZE;
      const width = gw * size;
      const height = gh * size;
      ctx.setFillStyle(COLORS.background);
      ctx.fillRect(0, 0, width, height);
      ctx.setFillStyle("#e8eaed");
      ctx.fillRect(0, 3 * size - 4, width, size + 8);
      ctx.fillRect(0, 10 * size - 4, width, size + 8);
      ctx.fillRect(12 * size - 4, 0, size + 8, height);
      if (this.routePath.length > 1) {
        ctx.setStrokeStyle(COLORS.route);
        ctx.setLineWidth(4);
        ctx.setLineCap("round");
        ctx.setLineJoin("round");
        ctx.beginPath();
        const first = this.routePath[0];
        ctx.moveTo(first.x * size + size / 2, first.y * size + size / 2);
        for (let idx = 1; idx < this.routePath.length; idx++) {
          const point = this.routePath[idx];
          ctx.lineTo(point.x * size + size / 2, point.y * size + size / 2);
        }
        ctx.stroke();
        ctx.setFillStyle(COLORS.entry);
        ctx.beginPath();
        ctx.arc(first.x * size + size / 2, first.y * size + size / 2, 8, 0, Math.PI * 2);
        ctx.fill();
        const last = this.routePath[this.routePath.length - 1];
        ctx.setFillStyle(COLORS.routeHead);
        ctx.beginPath();
        ctx.arc(last.x * size + size / 2, last.y * size + size / 2, 8, 0, Math.PI * 2);
        ctx.fill();
      }
      this.allSpots.forEach((spot) => {
        const centerX = spot.x_pos * size + size / 2;
        const centerY = spot.y_pos * size + size / 2;
        const selected = this.selectedSpot && this.selectedSpot.id === spot.id;
        ctx.setFillStyle(
          selected ? COLORS.route : spot.status === "free" ? COLORS.free : spot.status === "reserved" ? COLORS.reserved : COLORS.occupied
        );
        const spotSize = selected ? size - 4 : size - 6;
        const offset = (size - spotSize) / 2;
        ctx.fillRect(spot.x_pos * size + offset, spot.y_pos * size + offset, spotSize, spotSize);
        ctx.setFillStyle("#fff");
        ctx.setFontSize(8);
        ctx.setTextAlign("center");
        ctx.setTextBaseline("middle");
        ctx.fillText(spot.spot_number.replace(/^[A-C]-/, ""), centerX, centerY);
      });
      const entry = ((_c = this.mapInfo) == null ? void 0 : _c.entry) || [0, 0];
      ctx.setFillStyle(COLORS.entry);
      ctx.setFontSize(12);
      ctx.setTextAlign("center");
      ctx.fillText("入口", entry[0] * size + size / 2, entry[1] * size + size / 2);
      ctx.draw();
    },
    onCanvasClick(event) {
      const size = this.cellSize || GRID_SIZE;
      const x = Math.floor(event.detail.x / size);
      const y = Math.floor(event.detail.y / size);
      const clicked = this.allSpots.find(
        (spot) => Math.round(spot.x_pos) === x && Math.round(spot.y_pos) === y && spot.status === "free"
      );
      if (clicked) {
        this.selectSpot(clicked);
      }
    }
  }
};
function _sfc_render(_ctx, _cache, $props, $setup, $data, $options) {
  return common_vendor.e({
    a: $options.isAdmin
  }, $options.isAdmin ? common_vendor.e({
    b: common_vendor.o((...args) => $options.loadAdminData && $options.loadAdminData(...args)),
    c: $data.keyword,
    d: common_vendor.o(common_vendor.m(($event) => $data.keyword = $event.detail.value, {
      trim: true
    })),
    e: common_vendor.o((...args) => $options.loadAdminData && $options.loadAdminData(...args)),
    f: $data.createForm.name,
    g: common_vendor.o(common_vendor.m(($event) => $data.createForm.name = $event.detail.value, {
      trim: true
    })),
    h: $data.createForm.phone,
    i: common_vendor.o(common_vendor.m(($event) => $data.createForm.phone = $event.detail.value, {
      trim: true
    })),
    j: $data.createForm.password,
    k: common_vendor.o(common_vendor.m(($event) => $data.createForm.password = $event.detail.value, {
      trim: true
    })),
    l: $data.createLoading,
    m: common_vendor.o((...args) => $options.createUser && $options.createUser(...args)),
    n: $data.users.length === 0
  }, $data.users.length === 0 ? {} : {}, {
    o: common_vendor.f($data.users, (item, k0, i0) => {
      return common_vendor.e({
        a: common_vendor.t(item.name),
        b: common_vendor.t($options.roleText(item.role)),
        c: common_vendor.t(item.id),
        d: common_vendor.t(item.phone),
        e: common_vendor.t(item.is_resident ? "是" : "否"),
        f: common_vendor.o(($event) => $options.startEdit(item), item.id),
        g: common_vendor.o(($event) => $options.deleteUser(item), item.id),
        h: $data.editingUserId === item.id
      }, $data.editingUserId === item.id ? {
        i: $data.editForm.name,
        j: common_vendor.o(common_vendor.m(($event) => $data.editForm.name = $event.detail.value, {
          trim: true
        }), item.id),
        k: $data.editForm.phone,
        l: common_vendor.o(common_vendor.m(($event) => $data.editForm.phone = $event.detail.value, {
          trim: true
        }), item.id),
        m: common_vendor.t($options.roleLabel($data.editForm.role)),
        n: $data.roleOptions,
        o: common_vendor.o((...args) => $options.onEditRoleChange && $options.onEditRoleChange(...args), item.id),
        p: $data.editForm.is_resident,
        q: common_vendor.o(($event) => $data.editForm.is_resident = $event.detail.value, item.id),
        r: common_vendor.o(($event) => $options.saveEdit(item.id), item.id),
        s: common_vendor.o((...args) => $options.cancelEdit && $options.cancelEdit(...args), item.id)
      } : {}, {
        t: common_vendor.t($options.assignZoneLabel(item.id)),
        v: common_vendor.o(($event) => $options.onAssignZoneChange(item.id, $event), item.id),
        w: common_vendor.t($options.assignLabel(item.id)),
        x: $options.assignableSpots(item.id),
        y: common_vendor.o(($event) => $options.onAssignSpotChange(item.id, $event), item.id),
        z: common_vendor.o(($event) => $options.assignSpot(item.id), item.id),
        A: $options.ownedSpots(item.id).length > 0
      }, $options.ownedSpots(item.id).length > 0 ? {
        B: common_vendor.f($options.ownedSpots(item.id), (spot, k1, i1) => {
          return {
            a: common_vendor.t(spot.spot_number),
            b: common_vendor.o(($event) => $options.releaseSpot(spot.id), spot.id),
            c: spot.id
          };
        })
      } : {}, {
        C: $options.userVehicles(item.id).length > 0
      }, $options.userVehicles(item.id).length > 0 ? {
        D: common_vendor.f($options.userVehicles(item.id), (vehicle, k1, i1) => {
          return {
            a: common_vendor.t(vehicle.plate_number),
            b: common_vendor.t(vehicle.brand || "-"),
            c: common_vendor.t(vehicle.color || "-"),
            d: common_vendor.o(($event) => $options.deleteVehicleForUser(vehicle.id), vehicle.id),
            e: vehicle.id
          };
        })
      } : {}, {
        E: $options.vehicleForm(item.id).plate_number,
        F: common_vendor.o(common_vendor.m(($event) => $options.vehicleForm(item.id).plate_number = $event.detail.value, {
          trim: true
        }), item.id),
        G: $options.vehicleForm(item.id).brand,
        H: common_vendor.o(common_vendor.m(($event) => $options.vehicleForm(item.id).brand = $event.detail.value, {
          trim: true
        }), item.id),
        I: $options.vehicleForm(item.id).color,
        J: common_vendor.o(common_vendor.m(($event) => $options.vehicleForm(item.id).color = $event.detail.value, {
          trim: true
        }), item.id),
        K: $options.vehicleForm(item.id).is_resident,
        L: common_vendor.o(($event) => $options.vehicleForm(item.id).is_resident = $event.detail.value, item.id),
        M: common_vendor.o(($event) => $options.addVehicleForUser(item.id), item.id),
        N: item.id
      });
    }),
    p: $data.assignZones
  }) : common_vendor.e({
    q: common_vendor.s($options.canvasStyle),
    r: common_vendor.o((...args) => $options.onCanvasClick && $options.onCanvasClick(...args)),
    s: common_vendor.f(["全部", "A", "B", "C"], (z, k0, i0) => {
      return {
        a: common_vendor.t(z === "全部" ? "全部" : z + "区"),
        b: z,
        c: $data.selectedZone === z ? "primary" : "default",
        d: common_vendor.o(($event) => $options.filterZone(z), z)
      };
    }),
    t: common_vendor.f($options.filteredFreeSpots, (spot, k0, i0) => {
      return {
        a: common_vendor.t(spot.spot_number),
        b: common_vendor.t(spot.zone),
        c: spot.id,
        d: $data.selectedSpot && $data.selectedSpot.id === spot.id ? 1 : "",
        e: common_vendor.o(($event) => $options.selectSpot(spot), spot.id)
      };
    }),
    v: $options.filteredFreeSpots.length === 0
  }, $options.filteredFreeSpots.length === 0 ? {} : {}, {
    w: $data.routePath.length > 0
  }, $data.routePath.length > 0 ? {
    x: common_vendor.t($data.selectedSpot ? $data.selectedSpot.spot_number : "-"),
    y: common_vendor.t($data.routePath.length),
    z: common_vendor.t($options.estimatedMinutes),
    A: common_vendor.f($options.routeInstructions, (item, idx, i0) => {
      return {
        a: common_vendor.t(idx + 1),
        b: common_vendor.t(item),
        c: idx
      };
    })
  } : {}));
}
const MiniProgramPage = /* @__PURE__ */ common_vendor._export_sfc(_sfc_main, [["render", _sfc_render], ["__scopeId", "data-v-b0045dab"]]);
wx.createPage(MiniProgramPage);
//# sourceMappingURL=../../../.sourcemap/mp-weixin/pages/navigation/navigation.js.map
