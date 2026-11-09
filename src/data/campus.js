export const categories = [
  { id: "administrative", label: "行政服務", color: "#b9684f", icon: "行" },
  { id: "academic", label: "教學研究", color: "#d09942", icon: "學" },
  { id: "sports", label: "運動休閒", color: "#6984a0", icon: "運" },
  { id: "residential", label: "宿舍住宿", color: "#628d69", icon: "宿" },
  { id: "campus-life", label: "校園生活", color: "#9b7958", icon: "生" },
];

const buildingRecords = [
  ["1", "行政大樓", "D2", "administrative"],
  ["2", "總圖書館", "C2", "academic"],
  ["3", "中正圖書館（舊圖書館）", "C2", "academic"],
  ["4", "國鼎圖書館暨檔案館", "D3", "academic"],
  ["5", "志希館", "C3", "administrative"],
  ["6", "松果館", "B2", "administrative"],
  ["7", "依仁堂", "B3", "administrative"],
  ["8", "大講堂", "D1", "administrative"],
  ["9", "教學研究綜合大樓", "C3", "administrative"],
  ["10", "多功能會堂", "C4", "administrative"],
  ["11", "文學一館", "D3", "academic"],
  ["12", "文學二館", "D3", "academic"],
  ["13", "人文社會科學大樓", "D3", "academic"],
  ["14", "科學一館", "C4", "academic"],
  ["15", "科學二館", "C4", "academic"],
  ["16", "科學三館", "C4", "academic"],
  ["17", "鴻經館", "C4", "academic"],
  ["18", "謙翔館（科四館）", "C4", "academic"],
  ["19", "科學五館", "C4", "academic"],
  ["20", "理學院教學大樓", "C4", "academic"],
  ["21", "國鼎光電大樓", "C4", "academic"],
  ["22", "工程一館", "C2", "academic"],
  ["23", "實驗一館", "C2", "academic"],
  ["24", "工程二館", "C2", "academic"],
  ["25", "機械館", "B3", "academic"],
  ["26", "實驗三館", "B3", "academic"],
  ["27", "工程四館", "B4", "academic"],
  ["28", "機電實驗室", "B3", "academic"],
  ["29", "大型力學實驗館", "B4", "academic"],
  ["30", "風洞實驗室", "B4", "academic"],
  ["31", "工程五館", "B4", "academic"],
  ["32", "管理二館", "D4", "academic"],
  ["33", "客家學院大樓", "C4", "academic"],
  ["34", "太空及遙測研究中心", "A3", "academic"],
  ["35", "研究中心大樓二期", "A3", "academic"],
  ["36", "通識教育大樓", "C4", "academic"],
  ["37", "中大 VHF 轉播站", "A4", "academic"],
  ["38", "天線臺", "A4", "academic"],
  ["39", "大氣微量元素分析實驗室", "A3", "academic"],
  ["40", "大氣水文觀測站", "A4", "academic"],
  ["41", "先進科學與技術中心", "A3", "academic"],
  ["42", "正門", "D2", "campus-life"],
  ["45", "志道堂", "D1", "campus-life"],
  ["46", "游藝館", "D1", "campus-life"],
  ["47", "志希樓", "C1", "campus-life"],
  ["50", "桃園市中大運動中心", "B4", "sports"],
  ["51", "羽球館", "C3", "sports"],
  ["56", "攀岩塔", "B4", "sports"],
  ["57", "室內游泳池", "B4", "sports"],
  ["61", "松苑餐廳", "B3", "campus-life"],
  ["62", "小木屋鬆餅", "C3", "campus-life"],
  ["63", "牛家莊餐廳", "C1", "campus-life"],
  ["69", "湖畔小屋", "C2", "campus-life"],
  ["70", "工坊小屋", "C2", "campus-life"],
  ["71", "國際學舍", "C1", "residential"],
  ["72", "男生宿舍三舍", "C1", "residential"],
  ["73", "男生宿舍五舍", "C1", "residential"],
  ["74", "男生宿舍六舍", "C1", "residential"],
  ["75", "男生宿舍七舍", "C1", "residential"],
  ["76", "男生宿舍九舍", "D3", "residential"],
  ["77", "男生宿舍十一舍", "C1", "residential"],
  ["78", "男生宿舍十二舍", "D4", "residential"],
  ["79", "男生宿舍十三舍", "D1", "residential"],
  ["80", "女生宿舍一舍", "C2", "residential"],
  ["81", "女生宿舍二舍", "B2", "residential"],
  ["82", "女生宿舍三舍", "C2", "residential"],
  ["83", "女生宿舍四舍", "B2", "residential"],
  ["84", "女生宿舍十四舍", "C1", "residential"],
  ["85", "中大會館", "B3", "residential"],
  ["86", "研究生宿舍", "B4", "residential"],
  ["87", "教職員第一舍", "B2", "residential"],
  ["88", "教職員第二舍", "B2", "residential"],
  ["89", "教職員第四舍", "B3", "residential"],
  ["90", "中大新村", "A2", "residential"],
  ["91", "中大北村", "B4", "residential"],
  ["92", "學人宿舍", "B4", "residential"],
];

// Individually positioned footprints. Coordinates are in the 1600 × 1100 map viewBox.
// These are a visual interpretation of the printed guide, not surveyed GIS geometry.
const footprints = {
  1: [730, 862, 55, 33, 29, "courtyard"],
  2: [666, 520, 84, 45, 42, "courtyard"],
  3: [568, 544, 44, 31, 25, "wing"],
  4: [890, 795, 59, 30, 30, "wing"],
  5: [815, 625, 44, 27, 23, "wing"],
  6: [521, 260, 32, 25, 20, "block"],
  7: [830, 342, 64, 34, 26, "hall"],
  8: [365, 871, 61, 34, 23, "hall"],
  9: [899, 645, 58, 34, 38, "courtyard"],
  10: [1043, 647, 59, 37, 23, "hall"],
  11: [921, 711, 46, 28, 24, "wing"],
  12: [980, 750, 42, 28, 24, "wing"],
  13: [1038, 793, 58, 34, 34, "courtyard"],
  14: [998, 512, 43, 30, 30, "wing"],
  15: [1065, 502, 41, 27, 29, "block"],
  16: [1116, 509, 47, 27, 28, "wing"],
  17: [1000, 558, 34, 24, 26, "block"],
  18: [1071, 566, 53, 29, 36, "courtyard"],
  19: [1128, 578, 44, 25, 30, "wing"],
  20: [1000, 608, 48, 31, 31, "wing"],
  21: [1134, 630, 45, 30, 37, "block"],
  22: [609, 569, 44, 28, 26, "wing"],
  23: [543, 589, 34, 23, 21, "block"],
  24: [665, 588, 48, 28, 27, "wing"],
  25: [748, 315, 49, 30, 26, "wing"],
  26: [779, 353, 35, 25, 23, "block"],
  27: [1186, 304, 55, 30, 28, "wing"],
  28: [791, 405, 33, 23, 20, "block"],
  29: [1241, 333, 66, 36, 20, "hall"],
  30: [1321, 343, 32, 24, 21, "block"],
  31: [1280, 387, 51, 30, 30, "wing"],
  32: [1151, 833, 60, 35, 33, "courtyard"],
  33: [1197, 670, 50, 30, 27, "wing"],
  34: [873, 184, 52, 30, 28, "wing"],
  35: [931, 173, 43, 27, 31, "block"],
  36: [1168, 727, 54, 29, 29, "wing"],
  37: [1202, 178, 22, 18, 32, "tower"],
  38: [1241, 201, 20, 17, 36, "tower"],
  39: [989, 211, 26, 20, 20, "block"],
  40: [1294, 225, 25, 19, 20, "block"],
  41: [1047, 198, 57, 29, 35, "courtyard"],
  42: [779, 1012, 22, 16, 16, "gate"],
  45: [432, 856, 43, 28, 24, "hall"],
  46: [506, 850, 37, 25, 20, "block"],
  47: [336, 562, 42, 24, 23, "wing"],
  50: [1333, 522, 79, 42, 27, "hall"],
  51: [880, 497, 54, 31, 22, "hall"],
  56: [1370, 566, 19, 17, 30, "tower"],
  57: [1304, 602, 61, 31, 20, "hall"],
  61: [697, 291, 42, 27, 18, "hall"],
  62: [859, 552, 26, 19, 17, "block"],
  63: [376, 516, 36, 22, 18, "block"],
  69: [554, 460, 24, 18, 16, "block"],
  70: [589, 476, 23, 18, 17, "block"],
  71: [291, 576, 52, 29, 29, "wing"],
  72: [257, 620, 44, 26, 24, "wing"],
  73: [297, 659, 43, 25, 26, "wing"],
  74: [344, 687, 44, 24, 25, "wing"],
  75: [410, 711, 41, 25, 25, "wing"],
  76: [866, 814, 42, 26, 25, "wing"],
  77: [463, 728, 43, 24, 26, "wing"],
  78: [1223, 845, 47, 25, 27, "wing"],
  79: [565, 850, 43, 26, 25, "wing"],
  80: [499, 517, 43, 26, 24, "wing"],
  81: [392, 296, 43, 25, 24, "wing"],
  82: [483, 570, 45, 24, 25, "wing"],
  83: [429, 323, 43, 24, 25, "wing"],
  84: [510, 755, 44, 26, 28, "wing"],
  85: [673, 345, 50, 29, 30, "courtyard"],
  86: [1343, 720, 50, 28, 29, "wing"],
  87: [413, 237, 38, 23, 22, "wing"],
  88: [461, 246, 39, 23, 22, "wing"],
  89: [622, 282, 38, 24, 22, "wing"],
  90: [312, 183, 50, 27, 20, "wing"],
  91: [1361, 777, 44, 25, 24, "wing"],
  92: [1275, 811, 45, 25, 25, "wing"],
};
export const buildings = buildingRecords.map(([id, name, zone, category]) => {
  const number = Number(id);
  const [x, y, width, depth, height, shape] = footprints[id];
  const node = `building-${id}`;

  return {
    id,
    number,
    name,
    zone,
    category,
    x,
    y,
    width,
    depth,
    height,
    shape,
    node,
    short: `校園導覽圖列載地點・分區 ${zone}`,
    detail:
      "此建物名稱依中央大學官方校園導覽圖整理；地圖位置為依分區重繪的示意位置。",
    accessibility: "建物入口與無障礙設施資訊尚未查證。",
    accessibleEntry: null,
  };
});

// Route vertices follow the same drawn road geometry as campusPaths below.
const roadPoints = {
  n: [478, 164],
  nw: [363, 348],
  w: [371, 623],
  sw: [512, 785],
  entrance: [779, 1012],
  south: [713, 902],
  se: [994, 884],
  east: [1293, 648],
  ne: [1334, 437],
  upper: [1030, 253],
  lakeN: [530, 273],
  lakeE: [807, 255],
  lakeS: [578, 502],
  lakeSE: [785, 483],
  middle: [1030, 544],
  academic: [914, 645],
  lower: [755, 733],
  engineering: [626, 690],
  westN: [267, 534],
  sport: [1279, 522],
  dorm: [1193, 400],
};

const roadConnections = [
  ["n", "nw"],
  ["nw", "w"],
  ["w", "sw"],
  ["sw", "south"],
  ["south", "entrance"],
  ["south", "se"],
  ["se", "east"],
  ["east", "ne"],
  ["ne", "upper"],
  ["upper", "n"],
  ["nw", "lakeN"],
  ["lakeN", "lakeE"],
  ["lakeE", "upper"],
  ["w", "lakeS"],
  ["lakeS", "lakeSE"],
  ["lakeSE", "middle"],
  ["lakeN", "lakeS"],
  ["lakeE", "lakeSE"],
  ["upper", "middle"],
  ["middle", "academic"],
  ["academic", "lower"],
  ["lower", "south"],
  ["lower", "engineering"],
  ["engineering", "lakeS"],
  ["engineering", "w"],
  ["nw", "westN"],
  ["westN", "w"],
  ["upper", "dorm"],
  ["dorm", "ne"],
  ["middle", "sport"],
  ["sport", "east"],
  ["academic", "se"],
];

export const routeNodes = Object.entries(roadPoints).map(([name, [x, y]]) => ({
  id: `road-${name}`,
  x,
  y,
}));

const routeNodeById = new Map([
  ...routeNodes.map((node) => [node.id, node]),
  ...buildings.map((building) => [building.node, building]),
]);

export const routeEdges = [];
const addRouteEdge = (from, to) => {
  const start = routeNodeById.get(from);
  const end = routeNodeById.get(to);
  const distance = Math.round(
    Math.hypot(end.x - start.x, end.y - start.y) * 1.8
  );
  routeEdges.push({ from, to, distance, accessible: null });
};

roadConnections.forEach(([from, to]) =>
  addRouteEdge(`road-${from}`, `road-${to}`)
);

buildings.forEach((building) => {
  const nearest = routeNodes.reduce((best, node) =>
    Math.hypot(node.x - building.x, node.y - building.y) <
    Math.hypot(best.x - building.x, best.y - building.y)
      ? node
      : best
  );
  addRouteEdge(building.node, nearest.id);
});

export const campusPaths = [
  {
    id: "west-outer",
    d: "M478 164 Q405 204 363 348 Q313 456 267 534 Q280 588 371 623 Q425 715 512 785 Q610 864 713 902",
  },
  {
    id: "east-outer",
    d: "M478 164 Q695 168 807 255 L1030 253 Q1110 339 1193 400 L1334 437 Q1361 541 1293 648 Q1166 825 994 884 Q861 917 713 902",
  },
  {
    id: "main-entry",
    d: "M779 1063 L779 1012 Q768 953 713 902 Q711 811 755 733 Q820 670 914 645 Q988 608 1030 544 L1030 253",
  },
  {
    id: "lake-north",
    d: "M363 348 Q444 279 530 273 Q660 216 807 255 L1030 253",
  },
  {
    id: "lake-south",
    d: "M371 623 Q468 552 578 502 Q660 491 785 483 Q905 481 1030 544",
  },
  {
    id: "west-campus",
    d: "M363 348 Q275 401 267 534 M371 623 Q502 637 626 690 L755 733",
  },
  {
    id: "academic-spine",
    d: "M530 273 Q500 370 578 502 Q631 583 626 690 M807 255 Q863 350 785 483 Q789 578 914 645",
  },
  {
    id: "east-campus",
    d: "M1030 253 Q1102 354 1193 400 L1334 437 M1030 544 Q1168 496 1279 522 L1293 648 M914 645 Q1032 737 994 884",
  },
];

export function findRoute(startId, endId, accessibleOnly = false) {
  const start = buildings.find((building) => building.id === startId);
  const end = buildings.find((building) => building.id === endId);
  if (!start || !end) return null;
  if (startId === endId) {
    return {
      buildings: [start],
      points: [{ x: start.x, y: start.y }],
      distance: 0,
    };
  }

  const distances = new Map([[start.node, 0]]);
  const previous = new Map();
  const remaining = new Set(routeNodeById.keys());

  while (remaining.size) {
    let current = null;
    let bestDistance = Infinity;
    remaining.forEach((node) => {
      const distance = distances.has(node) ? distances.get(node) : Infinity;
      if (distance < bestDistance) {
        current = node;
        bestDistance = distance;
      }
    });

    if (current === null || bestDistance === Infinity) break;
    if (current === end.node) break;
    remaining.delete(current);

    routeEdges.forEach((edge) => {
      if (accessibleOnly && edge.accessible !== true) return;
      let neighbor = null;
      if (edge.from === current) neighbor = edge.to;
      if (edge.to === current) neighbor = edge.from;
      if (!neighbor || !remaining.has(neighbor)) return;
      const candidate = bestDistance + edge.distance;
      if (
        candidate <
        (distances.has(neighbor) ? distances.get(neighbor) : Infinity)
      ) {
        distances.set(neighbor, candidate);
        previous.set(neighbor, current);
      }
    });
  }

  if (!distances.has(end.node)) return null;
  const path = [end.node];
  while (path[0] !== start.node) {
    const parent = previous.get(path[0]);
    if (!parent) return null;
    path.unshift(parent);
  }

  const buildingsByNode = new Map(
    buildings.map((building) => [building.node, building])
  );
  return {
    buildings: path.map((node) => buildingsByNode.get(node)).filter(Boolean),
    points: path.map((node) => {
      const { x, y } = routeNodeById.get(node);
      return { x, y };
    }),
    distance: distances.get(end.node),
  };
}
