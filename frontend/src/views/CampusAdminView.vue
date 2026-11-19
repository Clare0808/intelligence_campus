<template>
  <main class="admin">
    <div class="admin-content">
      <header class="topbar">
        <RouterLink :to="{ name: 'campus' }" class="button back-link"
          ><AdminIcon name="back" /> 返回校園地圖</RouterLink
        >
        <div class="account-area">
          <span v-if="admin" class="role-badge">管理員</span><CampusAccount />
        </div>
      </header>
      <template v-if="admin">
        <section class="overview" aria-label="回報統計" :aria-busy="loading">
          <button
            v-for="stat in stats"
            :key="stat.id"
            type="button"
            class="stat-card"
            :class="stat.tone"
            :aria-pressed="section === 'reports' && filter === stat.id"
            @click="
              section = 'reports';
              filter = stat.id;
            "
          >
            <span class="stat-top"
              ><span>{{ stat.label }}</span
              ><span class="stat-icon"><AdminIcon :name="stat.icon" /></span
            ></span>
            <span class="stat-value"
              >{{ loaded ? stat.count : "—" }}<small>則</small></span
            >
            <span class="stat-hint"
              >{{ stat.hint }}<AdminIcon name="arrow"
            /></span>
          </button>
        </section>
        <div class="workspace-heading">
          <nav class="manager-tabs" aria-label="管理項目">
            <button
              type="button"
              :aria-pressed="section === 'reports'"
              @click="section = 'reports'"
            >
              <AdminIcon name="inbox" /> 使用者回報
            </button>
            <button
              type="button"
              :aria-pressed="section === 'construction'"
              @click="section = 'construction'"
            >
              <AdminIcon name="construction" /> 校方施工公告
            </button>
            <button
              type="button"
              :aria-pressed="section === 'users'"
              @click="section = 'users'"
            >
              <AdminIcon name="shield" /> 使用者管理
            </button>
          </nav>
        </div>
        <section v-if="section === 'users'" class="users-panel">
          <div class="panel-heading">
            <div>
              <h2>已登入使用者</h2>
            </div>
            <button
              class="button reload-button"
              type="button"
              :disabled="usersLoading"
              @click="loadUsers"
            >
              <AdminIcon name="refresh" />
              {{ usersLoading ? "載入中…" : "重新載入" }}
            </button>
          </div>
          <div class="users-content" :aria-busy="usersLoading">
            <p v-if="usersError" role="alert">{{ usersError }}</p>
            <p v-if="usersMessage" role="status">{{ usersMessage }}</p>
            <p v-if="usersLoading && !usersLoaded">正在載入使用者…</p>
            <p v-else-if="!usersLoading && usersLoaded && !users.length">
              尚無登入過的使用者。
            </p>
            <div v-else-if="usersLoaded" class="users-list">
              <article
                v-for="user in users"
                :key="user.provider + ':' + user.subject"
                class="user-row"
              >
                <div class="user-details">
                  <strong>{{ user.name }}</strong>
                  <span
                    >{{ user.email || "未提供電子郵件"
                    }}{{
                      user.email && !user.email_verified ? "（未驗證）" : ""
                    }}</span
                  >
                  <small
                    >{{ user.provider }} · {{ user.subject }} · 最近登入：{{
                      formatTime(user.last_login_at)
                    }}</small
                  >
                </div>
                <div class="user-role">
                  <label :for="'role-' + user.provider + '-' + user.subject"
                    >權限</label
                  >
                  <select
                    :id="'role-' + user.provider + '-' + user.subject"
                    :value="user.role"
                    :disabled="usersBusy || usersLoading || user.owner"
                    @change="changeRole(user, $event)"
                  >
                    <option value="user">使用者</option>
                    <option value="admin">管理員</option>
                  </select>
                  <small v-if="user.owner">初始管理員，不可變更</small>
                </div>
              </article>
            </div>
          </div>
        </section>
        <section
          v-else-if="section === 'construction'"
          class="construction-panel"
        >
          <div class="panel-heading">
            <div>
              <h2>校方施工公告</h2>
            </div>
          </div>
          <OfficialConstructionAdmin />
        </section>
        <div v-else class="manager-grid">
          <section class="report-panel" aria-label="使用者回報管理">
            <div class="panel-heading">
              <div>
                <h2>
                  回報工作區
                  <span v-if="loaded" class="count-badge">{{
                    reports.length
                  }}</span>
                </h2>
              </div>
              <a
                :href="exportReportsUrl"
                class="button primary"
                title="匯出全部回報，包含所有審核狀態"
                ><AdminIcon name="download" /> 匯出 Excel</a
              >
            </div>
            <div class="toolbar">
              <label class="search-field"
                ><span class="field-label">搜尋回報</span
                ><span class="search-input"
                  ><AdminIcon name="search" /><input
                    v-model.trim="query"
                    type="search"
                    placeholder="搜尋標題、內容或帳號" /></span
              ></label>
              <label class="status-field">
                <span class="field-label">審核狀態</span>
                <select v-model="filter">
                  <option value="">所有狀態</option>
                  <option
                    v-for="(label, id) in reportStatuses"
                    :key="id"
                    :value="id"
                  >
                    {{ label }}
                  </option>
                </select>
              </label>
              <button
                class="button reload-button"
                type="button"
                :disabled="loading || busy"
                @click="loadReports"
              >
                <AdminIcon name="refresh" />
                {{ loading ? "載入中…" : "重新載入" }}
              </button>
            </div>
            <p v-if="message" class="feedback success" role="status">
              {{ message }}
            </p>
            <div v-if="error" class="feedback error" role="alert">
              <p>{{ error }}</p>
              <button
                type="button"
                class="button"
                :disabled="loading"
                @click="loadReports"
              >
                重試載入
              </button>
            </div>
            <div v-if="loading" class="loading-state" role="status">
              <span class="loading-ring" aria-hidden="true"></span
              >正在載入回報資料…
            </div>
            <div v-else-if="!filtered.length && !error" class="empty-state">
              <div class="empty-art" aria-hidden="true">
                <span class="art-orbit"></span><span class="art-dot"></span
                ><span class="art-document"
                  ><span></span><span></span><span></span
                  ><AdminIcon name="check"
                /></span>
              </div>
              <span class="empty-eyebrow">{{
                hasFilters ? "調整篩選，看看其他回報" : "回報工作區已準備就緒"
              }}</span>
              <h2>
                {{ hasFilters ? "沒有符合條件的回報" : "目前還沒有使用者回報" }}
              </h2>
              <p>
                {{
                  hasFilters
                    ? "試試其他關鍵字，或清除篩選以查看全部回報。"
                    : "收到新的校園狀況後，你可以在這裡查看詳情、審核公開，並匯出整理。"
                }}
              </p>
              <button
                v-if="hasFilters"
                type="button"
                class="button primary"
                @click="
                  filter = '';
                  query = '';
                "
              >
                清除篩選
              </button>
              <RouterLink v-else :to="{ name: 'campus' }" class="button primary"
                >前往校園地圖<AdminIcon name="arrow"
              /></RouterLink>
              <div v-if="!hasFilters" class="report-categories">
                <span>施工狀況</span><span>設施毀壞</span><span>閒置設施</span>
              </div>
            </div>
            <ul v-else-if="!error" class="reports">
              <li v-for="report in filtered" :key="report.id">
                <article class="report">
                  <div class="report-top">
                    <p>#{{ report.id }} · {{ kinds[report.kind] }}</p>
                    <span class="status">{{
                      report.deleted_at
                        ? "待永久刪除"
                        : reportStatuses[report.status]
                    }}</span>
                  </div>
                  <h2>{{ report.title }}</h2>
                  <p class="details">{{ report.details }}</p>
                  <dl>
                    <div>
                      <dt>位置</dt>
                      <dd>
                        {{ report.latitude.toFixed(5) }},
                        {{ report.longitude.toFixed(5) }}
                      </dd>
                    </div>
                    <div>
                      <dt>回報時間</dt>
                      <dd>{{ formatTime(report.created_at) }}</dd>
                    </div>
                    <div>
                      <dt>回報帳號</dt>
                      <dd>{{ report.reporter }}</dd>
                    </div>
                    <div v-if="report.reviewed_at">
                      <dt>審核更新</dt>
                      <dd>{{ formatTime(report.reviewed_at) }}</dd>
                    </div>
                  </dl>
                  <p v-if="report.road_closed" class="status">
                    涉及道路封閉 · 公開後路線將避開對應路段
                  </p>
                  <div class="actions">
                    <template v-if="!report.deleted_at">
                      <button
                        v-if="report.status !== 'approved'"
                        class="primary"
                        type="button"
                        :disabled="busy"
                        @click="review(report, 'approved')"
                      >
                        審核公開
                      </button>
                      <button
                        v-if="report.status !== 'rejected'"
                        type="button"
                        :disabled="busy"
                        @click="review(report, 'rejected')"
                      >
                        {{
                          report.status === "approved" ? "撤下標記" : "退回回報"
                        }}
                      </button>
                    </template>
                    <button
                      type="button"
                      :disabled="busy"
                      @click="deleteCandidate = report.id"
                    >
                      刪除回報
                    </button>
                  </div>
                  <div
                    v-if="deleteCandidate === report.id"
                    class="delete-confirmation"
                    role="group"
                    :aria-label="'刪除回報 #' + report.id"
                  >
                    <p>
                      確定永久刪除回報 #{{ report.id }}「{{
                        report.title
                      }}」？這會從資料庫移除整筆資料，刪除後無法還原。
                    </p>
                    <div class="actions">
                      <button
                        type="button"
                        :disabled="busy"
                        @click="remove(report)"
                      >
                        確認永久刪除
                      </button>
                      <button
                        type="button"
                        :disabled="busy"
                        @click="deleteCandidate = null"
                      >
                        取消
                      </button>
                    </div>
                  </div>
                </article>
              </li>
            </ul>
            <footer class="panel-footer">
              <span>{{
                loaded
                  ? "顯示 " +
                    filtered.length +
                    " 則 / 共 " +
                    reports.length +
                    " 則回報"
                  : "等待載入回報"
              }}</span
              ><span v-if="lastLoaded"
                >上次載入 {{ formatTime(lastLoaded) }}</span
              >
            </footer>
          </section>
        </div>
      </template>
      <section v-else class="access-panel">
        <AdminIcon name="shield" />
        <h2>{{ session ? "登入管理員帳號，開始管理" : "正在確認帳號權限" }}</h2>
        <p>
          {{
            session
              ? "請使用有管理員權限的帳號登入。登入選項位於頁面上方。"
              : "正在取得登入狀態，請稍候。"
          }}
        </p>
      </section>
    </div>
  </main>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import AdminIcon from "../components/AdminIcon.vue";
import CampusAccount from "../components/CampusAccount.vue";
import OfficialConstructionAdmin from "../components/OfficialConstructionAdmin.vue";
import {
  campusRequest,
  exportReportsUrl,
  formatTime,
  kinds,
  reportStatuses,
  useCampusAccount,
} from "../services/campusTools.js";

const { session } = useCampusAccount();
const admin = computed(() => Boolean(session.value?.account?.admin));
const reports = ref([]);
const users = ref([]);
const usersLoaded = ref(false);
const usersLoading = ref(false);
const usersBusy = ref(false);
const usersError = ref("");
const usersMessage = ref("");
const section = ref("reports");
const deleteCandidate = ref(null);
const filter = ref("");
const query = ref("");
const hasFilters = computed(() => Boolean(filter.value || query.value));
const filtered = computed(() =>
  reports.value.filter(
    (report) =>
      (!filter.value || report.status === filter.value) &&
      [
        report.title,
        report.details,
        report.reporter,
        report.id,
        kinds[report.kind],
      ]
        .join(" ")
        .toLocaleLowerCase()
        .includes(query.value.toLocaleLowerCase())
  )
);
const error = ref("");
const message = ref("");
const loading = ref(false);
const loaded = ref(false);
const lastLoaded = ref(null);
const busy = ref(false);
const refreshInterval = 10000;
let refreshTimer = null;
const stats = computed(() => [
  {
    id: "",
    label: "全部回報",
    count: reports.value.length,
    icon: "inbox",
    tone: "total",
    hint: "查看所有校園狀況",
  },
  {
    id: "pending",
    label: "待審核",
    count: reports.value.filter((r) => !r.deleted_at && r.status === "pending")
      .length,
    icon: "clock",
    tone: "pending",
    hint: "等待確認與處理",
  },
  {
    id: "approved",
    label: "已公開",
    count: reports.value.filter((r) => !r.deleted_at && r.status === "approved")
      .length,
    icon: "check",
    tone: "approved",
    hint: "已顯示於校園地圖",
  },
  {
    id: "rejected",
    label: "已退回",
    count: reports.value.filter((r) => !r.deleted_at && r.status === "rejected")
      .length,
    icon: "returned",
    tone: "rejected",
    hint: "已退回或撤下標記",
  },
]);
let loadId = 0;
let usersLoadId = 0;

async function loadUsers() {
  if (!admin.value) return;
  const id = ++usersLoadId;
  usersLoading.value = true;
  usersError.value = "";
  try {
    const result = await campusRequest("/admin/users");
    if (id === usersLoadId && admin.value) {
      users.value = result.users;
      usersLoaded.value = true;
    }
  } catch (cause) {
    if (id === usersLoadId && admin.value) usersError.value = cause.message;
  } finally {
    if (id === usersLoadId) usersLoading.value = false;
  }
}

async function changeRole(user, event) {
  const role = event.target.value;
  event.target.value = user.role;
  if (role === user.role) return;
  usersBusy.value = true;
  usersError.value = "";
  usersMessage.value = "";
  try {
    await campusRequest(
      "/admin/users/" +
        encodeURIComponent(user.provider) +
        "/" +
        encodeURIComponent(user.subject),
      "PATCH",
      { role, previous_role: user.role }
    );
    await loadUsers();
    if (!usersError.value) usersMessage.value = user.name + " 的權限已更新。";
    else if (users.value.includes(user)) user.role = role;
  } catch (cause) {
    usersError.value = cause.message;
  } finally {
    usersBusy.value = false;
  }
}

watch(section, (value) => {
  if (value === "users" && admin.value) loadUsers();
});

async function loadReports({ silent = false } = {}) {
  if (!admin.value || (silent && (loading.value || busy.value))) return;
  const id = ++loadId;
  if (!silent) {
    loading.value = true;
    error.value = "";
  }
  try {
    const result = await campusRequest("/admin/reports");
    if (id === loadId && admin.value) {
      reports.value = result.reports;
      loaded.value = true;
      lastLoaded.value = new Date().toISOString();
      error.value = "";
    }
  } catch (cause) {
    if (id === loadId && admin.value) error.value = cause.message;
  } finally {
    if (id === loadId && !silent) loading.value = false;
  }
}

async function review(report, status) {
  busy.value = true;
  error.value = "";
  message.value = "";
  try {
    await campusRequest("/admin/reports/" + report.id, "PATCH", {
      status,
      previous_status: report.status,
    });
    await loadReports();
    message.value = "回報 #" + report.id + "：" + reportStatuses[status];
  } catch (cause) {
    error.value = cause.message;
  } finally {
    busy.value = false;
  }
}

async function remove(report) {
  busy.value = true;
  error.value = "";
  message.value = "";
  try {
    const result = await campusRequest(
      "/admin/reports/" + report.id,
      "DELETE",
      {
        previous_status: report.status,
      }
    );
    deleteCandidate.value = null;
    await loadReports();
    message.value = result.message;
  } catch (cause) {
    error.value = cause.message;
  } finally {
    busy.value = false;
  }
}

watch(
  admin,
  (allowed) => {
    if (allowed) {
      loadReports();
      if (section.value === "users") loadUsers();
      if (!refreshTimer) {
        refreshTimer = window.setInterval(() => {
          if (!document.hidden) loadReports({ silent: true });
        }, refreshInterval);
      }
    } else {
      window.clearInterval(refreshTimer);
      refreshTimer = null;
      loadId += 1;
      reports.value = [];
      usersLoadId += 1;
      users.value = [];
      usersLoaded.value = false;
      usersLoading.value = false;
      usersError.value = "";
      usersMessage.value = "";
      loaded.value = false;
      lastLoaded.value = null;
      loading.value = false;
    }
  },
  { immediate: true }
);

function refreshWhenVisible() {
  if (!document.hidden) loadReports({ silent: true });
}

onMounted(() =>
  document.addEventListener("visibilitychange", refreshWhenVisible)
);
onBeforeUnmount(() => {
  window.clearInterval(refreshTimer);
  document.removeEventListener("visibilitychange", refreshWhenVisible);
  loadId += 1;
  usersLoadId += 1;
});
</script>

<style scoped src="../styles/campus-admin.css"></style>
