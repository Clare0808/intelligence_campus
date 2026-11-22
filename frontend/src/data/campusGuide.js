export const campusGuideSteps = [
  {
    title: "互動校園地圖",
    description:
      "拖曳地圖探索校園、縮放查看建物；點選建物可查看名稱及施工資訊。",
    panel: "",
    target: "campus-building",
  },
  {
    title: "施工資訊",
    description:
      "地圖上紅色建物代表兩週內施工中或即將施工；點選建物可查看施工內容與日期。",
    panel: "construction",
    target: "[data-guide='construction']",
  },
  {
    title: "搜尋校園地點",
    description:
      "在側欄搜尋建物名稱，或展開分類選擇地點；選取後地圖會定位至該建物。",
    panel: "construction",
    target: "#building-search",
  },
  {
    title: "路線規劃",
    description:
      "選擇起點、終點和步行或輪椅偏好，規劃路線後可在地圖查看，並隨時清除。",
    panel: "route",
    target: "[data-guide='route']",
  },
  {
    title: "地圖標記",
    description: "切換施工與毀壞、閒置設施及無障礙圖層，點選標記查看詳細資訊。",
    panel: "markers",
    target: "[data-guide='markers']",
  },
  {
    title: "登入與回報",
    description:
      "登入後可以回報施工、毀壞或閒置設施，選擇建物或在地圖上選點；回報經審核後才會公開。",
    panel: "report",
    target: "[data-guide='report']",
  },
  {
    title: "AI 助手",
    description:
      "點選地圖右下角的 AI 助手，可詢問施工資訊與地圖功能；回答僅供參考，請以校方公告與現場狀況為準。",
    panel: "",
    target: ".assistant-trigger",
  },
  {
    title: "地圖顯示與重新導覽",
    description:
      "地圖右側可切換平面／3D、重設視角與深淺色模式。日後點選右側的「功能導覽」，即可再次查看本導覽。",
    panel: "",
    target: ".guide-trigger",
  },
];
