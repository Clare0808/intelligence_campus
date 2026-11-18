<template>
  <main class="admin">
    <div class="admin-content">
      <header class="topbar">
        <RouterLink :to="{ name: 'campus' }" class="brand"
          ><span class="brand-mark"><AdminIcon name="shield" /></span
          ><span
            ><strong>中大智慧校園</strong><small>校園管理中心</small></span
          ></RouterLink
        >
        <div class="account-area">
          <span v-if="admin" class="role-badge">管理員</span><CampusAccount />
        </div>
      </header>
      <div class="page-intro">
        <div>
          <p class="eyebrow">校園維運 · 管理總覽</p>
          <h1>讓每一則回報，都有回應。</h1>
          <p class="intro-copy">
            集中查看校園狀況、審核使用者回報，與維護地圖上的施工資訊。
          </p>
        </div>
        <RouterLink :to="{ name: 'campus' }" class="button back-link"
          ><AdminIcon name="back" /> 返回校園地圖</RouterLink
        >
      </div>
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
          </nav>
          <span class="workspace-note">校園資訊，一處管理</span>
        </div>
        <section v-if="section === 'construction'" class="construction-panel">
          <div class="panel-heading">
            <div>
              <h2>校方施工公告</h2>
              <p>查看官方來源，管理公告與施工標記的顯示狀態。</p>
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
                <p>施工、毀壞與閒置設施的回報，都會集中在這裡。</p>
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
          <aside class="management-help" aria-label="管理操作說明">
            <section class="guide-card">
              <span class="card-eyebrow">處理指南</span>
              <h2>從回報到地圖，三個步驟</h2>
              <ol class="workflow">
                <li>
                  <span class="step-number">01</span>
                  <div>
                    <h3>查看回報</h3>
                    <p>確認內容、位置與回報時間。</p>
                  </div>
                </li>
                <li>
                  <span class="step-number">02</span>
                  <div>
                    <h3>審核並公開</h3>
                    <p>公開後顯示於地圖，封路回報會影響路線規劃。</p>
                  </div>
                </li>
                <li>
                  <span class="step-number">03</span>
                  <div>
                    <h3>匯出與追蹤</h3>
                    <p>透過 Excel 整理全部回報與審核狀態。</p>
                  </div>
                </li>
              </ol>
              <p class="guide-note">
                <AdminIcon name="shield" /><span
                  >回報須經管理員審核，才會顯示在公開地圖。</span
                >
              </p>
            </section>
            <section class="shortcut-card">
              <span class="shortcut-icon"
                ><AdminIcon name="construction"
              /></span>
              <h2>管理校方施工公告</h2>
              <p>查看官方公告，或隱藏不需顯示的施工標記。</p>
              <button
                type="button"
                class="text-button"
                @click="section = 'construction'"
              >
                前往公告管理<AdminIcon name="arrow" />
              </button>
            </section>
            <p class="delete-note">
              刪除回報會永久移除資料。若只需從地圖撤下，請使用「撤下標記」。
            </p>
          </aside>
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
      <footer class="page-footer">
        <span>中大智慧校園</span><span>一起維護更好通行的校園</span>
      </footer>
    </div>
  </main>
</template>

<script setup>
import { computed, ref, watch } from "vue";
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

async function loadReports() {
  const id = ++loadId;
  loading.value = true;
  error.value = "";
  try {
    const result = await campusRequest("/admin/reports");
    if (id === loadId && admin.value) {
      reports.value = result.reports;
      loaded.value = true;
      lastLoaded.value = new Date().toISOString();
    }
  } catch (cause) {
    if (id === loadId && admin.value) error.value = cause.message;
  } finally {
    if (id === loadId) loading.value = false;
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
    if (allowed) loadReports();
    else {
      loadId += 1;
      reports.value = [];
      loaded.value = false;
      lastLoaded.value = null;
      loading.value = false;
    }
  },
  { immediate: true }
);
</script>

<style scoped src="../styles/campus-admin.css"></style>
