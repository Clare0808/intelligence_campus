import { ref } from "vue";

const session = ref(null);
const prefix = "/api/campus";
const dates = new Intl.DateTimeFormat("zh-TW", {
  dateStyle: "short",
  timeStyle: "short",
  timeZone: "Asia/Taipei",
});

export const kinds = { construction: "施工", damage: "毀壞", idle: "閒置" };
export const reportStatuses = {
  pending: "待審核",
  approved: "已公開",
  rejected: "已退回",
};
export const exportReportsUrl = prefix + "/admin/reports.xlsx";

export function formatTime(value) {
  return value ? dates.format(new Date(value)) : "—";
}

export async function campusRequest(path, method = "GET", payload) {
  const options = { method, credentials: "same-origin" };
  if (method !== "GET") {
    options.headers = {
      "Content-Type": "application/json",
      "X-Campus-CSRF": session.value?.csrf || "",
    };
    options.body = JSON.stringify(payload ?? {});
  }
  let response;
  try {
    response = await fetch(prefix + path, options);
  } catch {
    throw new Error("目前無法連線至校園服務，請稍後重試。");
  }
  const data = await response.json().catch(() => null);
  if (!response.ok || data === null) {
    throw new Error(data?.message || "校園服務目前無法使用，請稍後重試。");
  }
  return data;
}

export async function refreshOfficialConstructionData() {
  const response = await fetch("/api/construction/refresh-official", {
    method: "POST",
    credentials: "same-origin",
    headers: { "X-Campus-CSRF": session.value?.csrf || "" },
  });
  const data = await response.json().catch(() => null);
  if (!response.ok || data === null) {
    throw new Error(data?.message || "施工公告更新失敗，請稍後再試。");
  }
  return data;
}

export async function loadCampusFile(filename) {
  const response = await fetch(import.meta.env.BASE_URL + "data/" + filename);
  if (!response.ok) throw new Error("校園地圖資料載入失敗。");
  return response.json();
}

export function useCampusAccount() {
  return {
    session,
    async refresh() {
      session.value = await campusRequest("/session");
    },
    async signInAs(role) {
      session.value = await campusRequest("/session/preview", "POST", { role });
    },
    async signOut() {
      session.value = await campusRequest("/session/logout", "POST");
    },
    loginUrl: (provider) => prefix + "/login/" + provider,
  };
}
