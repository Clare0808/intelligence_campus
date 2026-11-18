const accessibilitySource =
  "https://love.adm.ncu.edu.tw/NCU_counsel/NCU-barrier-free/";

// Supplement the project's existing names; do not alter its building geometry.
// Chinese and English library names were checked against NCU's official pages.
const verifiedNames = {
  "中正圖書館(舊圖)": {
    name: "中正圖書館",
    aliases: ["舊圖"],
    englishName: "Zhong-Zheng Library (Old Library)",
    source: accessibilitySource,
  },
  總圖書館: {
    aliases: ["總圖"],
    englishName: "Main Library",
    source: "https://www.ncu.edu.tw/p/412-1000-324.php?Lang=zh-tw",
  },
  國鼎圖書資料館: {
    aliases: ["國鼎圖書館"],
    englishName: "Kwoh-Ting Library",
    source: accessibilitySource,
  },
};

export function buildingLabel(properties) {
  const original = String(properties.name || "未命名建築");
  const verified = verifiedNames[original] ?? {};
  const name = verified.name || original;
  const aliases = [
    ...(verified.aliases ?? []),
    ...[properties.alt_name, properties.short_name, properties.official_name]
      .filter((value) => typeof value === "string")
      .flatMap((value) => value.split(";")),
  ];
  return {
    name,
    aliases: [...new Set(aliases.map((value) => value.trim()))].filter(
      (value) => value && value !== name
    ),
    englishName: verified.englishName || properties["name:en"] || "",
    source: verified.source || "",
  };
}
