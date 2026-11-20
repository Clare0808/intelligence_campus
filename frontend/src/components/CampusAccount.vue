<template>
  <section class="account" aria-label="校園帳號">
    <p v-if="!account && !loadError" role="status">正在取得登入選項…</p>
    <template v-else-if="account">
      <div v-if="account.account" class="account-row">
        <span>{{ account.account.name }}</span>
        <slot name="before-sign-out" />
        <button
          type="button"
          :disabled="busy"
          :aria-label="iconSignOut ? '登出' : undefined"
          :title="iconSignOut ? '登出' : undefined"
          :class="{ 'sign-out-icon': iconSignOut }"
          @click="act(signOut)"
        >
          <svg
            v-if="iconSignOut"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
            aria-hidden="true"
            focusable="false"
          >
            <path d="M10 4H5a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h5" />
            <path d="m15 16 4-4-4-4M19 12H9" />
          </svg>
          <template v-else>登出</template>
        </button>
      </div>
      <template v-else>
        <div class="account-row">
          <template v-for="provider in account.providers" :key="provider.id">
            <a v-if="provider.enabled" :href="loginUrl(provider.id)">
              {{ provider.label }} 登入
            </a>
            <button v-else type="button" disabled>
              {{ provider.label }} 未設定
            </button>
          </template>
        </div>
        <div v-if="account.preview" class="preview">
          <p>本機預覽可切換角色，回報使用獨立資料庫。</p>
          <div class="account-row">
            <button
              type="button"
              :disabled="busy"
              @click="act(() => signInAs('reporter'))"
            >
              預覽回報者
            </button>
            <button
              type="button"
              :disabled="busy"
              @click="act(() => signInAs('reviewer'))"
            >
              預覽管理員
            </button>
          </div>
        </div>
      </template>
    </template>
    <p v-if="loginError" role="alert">
      登入未完成。請確認登入服務的設定後重試。
    </p>
    <div v-if="loadError" role="alert">
      <p>{{ loadError }}</p>
      <button type="button" :disabled="busy" @click="act(refresh)">重試</button>
    </div>
  </section>
</template>

<script setup>
import { onMounted, computed, ref } from "vue";
import { useRoute } from "vue-router";
import { useCampusAccount } from "../services/campusTools.js";

/* global defineProps */
defineProps({ iconSignOut: { type: Boolean, default: false } });

const {
  session: account,
  refresh,
  signInAs,
  signOut,
  loginUrl,
} = useCampusAccount();
const route = useRoute();
const loginError = computed(() =>
  route.query.login === "failed" || route.query.login === "unavailable"
);
const loadError = ref("");
const busy = ref(false);

async function act(action) {
  busy.value = true;
  loadError.value = "";
  try {
    await action();
  } catch (error) {
    loadError.value = error.message;
  } finally {
    busy.value = false;
  }
}

onMounted(() => act(refresh));
</script>

<style scoped>
.account {
  display: grid;
  gap: 8px;
}
.account-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}
.account-row a,
.account button {
  display: inline-flex;
  align-items: center;
  min-height: 44px;
  padding: 5px 10px;
  border: 1px solid var(--line, #b8c6cd);
  border-radius: 5px;
  background: var(--panel-soft, #eaf1f4);
  color: inherit;
  font-size: 0.875rem;
}
.account button:disabled {
  color: var(--muted, #536774);
  cursor: default;
}
.account .sign-out-icon {
  justify-content: center;
  width: 44px;
  padding: 5px;
}
.sign-out-icon svg {
  width: 20px;
  height: 20px;
}
.account p {
  margin: 0 0 6px;
  font-size: 0.875rem;
  line-height: 1.55;
}
.preview {
  padding-top: 7px;
}
</style>
