<template>
  <section class="account" aria-label="校園帳號">
    <p v-if="!account && !loadError" role="status">正在取得登入選項…</p>
    <template v-else-if="account">
      <div
        v-if="account.account"
        class="account-row"
        :class="{ 'account-row-sidebar': sidebarLayout }"
      >
        <span>{{ account.account.name }}</span>
        <slot name="before-sign-out" />
        <button
          ref="signOutButton"
          type="button"
          :disabled="busy"
          :aria-label="iconSignOut ? '登出' : undefined"
          :title="iconSignOut ? '登出' : undefined"
          :class="{ 'sign-out-icon': iconSignOut }"
          @click="openSignOutConfirmation"
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
              @click="act(() => signInAs('reporter'), '登入成功！')"
            >
              預覽回報者
            </button>
            <button
              type="button"
              :disabled="busy"
              @click="act(() => signInAs('reviewer'), '登入成功！')"
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
    <div v-if="loadError && !confirmingSignOut" role="alert">
      <p>{{ loadError }}</p>
      <button type="button" :disabled="busy" @click="act(refresh)">重試</button>
    </div>
  </section>
  <Teleport to="body">
    <div v-if="confirmingSignOut" class="sign-out-backdrop">
      <div
        ref="confirmDialog"
        class="sign-out-dialog"
        :class="{ 'sign-out-dialog-light': lightDialog }"
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="sign-out-title"
        aria-describedby="sign-out-description"
        tabindex="-1"
        @keydown="onConfirmationKeydown"
      >
        <h2 id="sign-out-title">確認登出</h2>
        <p id="sign-out-description">確定要登出目前的帳號嗎？</p>
        <p v-if="loadError" role="alert">{{ loadError }}</p>
        <div class="sign-out-actions">
          <button
            ref="cancelButton"
            type="button"
            :disabled="busy"
            @click="cancelSignOut"
          >
            取消
          </button>
          <button type="button" :disabled="busy" @click="confirmSignOut">
            {{ busy ? "登出中…" : "確認登出" }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { onMounted, computed, nextTick, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useCampusAccount } from "../services/campusTools.js";
import { showNotification } from "../services/notifications.js";

/* global defineProps */
defineProps({
  iconSignOut: { type: Boolean, default: false },
  sidebarLayout: { type: Boolean, default: false },
});

const {
  session: account,
  refresh,
  signInAs,
  signOut,
  loginUrl,
} = useCampusAccount();
const route = useRoute();
const router = useRouter();
const loginError = computed(
  () => route.query.login === "failed" || route.query.login === "unavailable"
);
const loadError = ref("");
const busy = ref(false);
const confirmingSignOut = ref(false);
const signOutButton = ref(null);
const confirmDialog = ref(null);
const cancelButton = ref(null);
const lightDialog = ref(false);

async function openSignOutConfirmation() {
  if (busy.value) return;
  lightDialog.value = Boolean(signOutButton.value?.closest(".theme-light"));
  confirmingSignOut.value = true;
  await nextTick();
  cancelButton.value?.focus();
}

function cancelSignOut() {
  if (busy.value) return;
  confirmingSignOut.value = false;
  loadError.value = "";
  nextTick(() => signOutButton.value?.focus());
}

async function confirmSignOut() {
  if (busy.value) return;
  const succeeded = await act(signOut);
  if (succeeded) {
    confirmingSignOut.value = false;
    await nextTick();
    (signOutButton.value || document.querySelector(".account button"))?.focus();
  }
}

function onConfirmationKeydown(event) {
  if (event.key === "Escape") {
    event.preventDefault();
    cancelSignOut();
  }
  if (event.key !== "Tab") return;
  const buttons = [...confirmDialog.value.querySelectorAll("button")];
  if (event.shiftKey && document.activeElement === buttons[0]) {
    event.preventDefault();
    buttons[buttons.length - 1].focus();
  } else if (
    !event.shiftKey &&
    document.activeElement === buttons[buttons.length - 1]
  ) {
    event.preventDefault();
    buttons[0].focus();
  }
}

async function act(action, successMessage = "") {
  busy.value = true;
  loadError.value = "";
  try {
    await action();
    if (successMessage) showNotification(successMessage);
    if (route.query.login === "success" && account.value?.account) {
      showNotification("登入成功！");
      await router.replace({ query: { ...route.query, login: undefined } });
    }
    return true;
  } catch (error) {
    loadError.value = error.message;
    return false;
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
.account-row-sidebar .sign-out-icon {
  margin-left: auto;
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
.account-row a {
  justify-content: center;
  width: 100%;
  box-sizing: border-box;
  text-decoration: none;
}
.account button:disabled {
  color: var(--muted, #536774);
  cursor: default;
}
.account .sign-out-icon {
  flex: 0 0 44px;
  justify-content: center;
  width: 44px;
  height: 44px;
  min-height: 44px;
  box-sizing: border-box;
  padding: 9px;
}
.account .account-row-sidebar .sign-out-icon {
  flex: 0 0 29px;
  width: 29px;
  height: 29px;
  min-height: 29px;
  padding: 5px;
  border-radius: 3px;
}
.sign-out-icon svg {
  width: 19px;
  height: 19px;
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

<style scoped>
.sign-out-backdrop {
  position: fixed;
  z-index: 1100;
  inset: 0;
  display: grid;
  place-items: center;
  padding: 20px;
  background: rgba(3, 14, 27, 0.72);
}
.sign-out-dialog {
  --dialog-panel: #091b31;
  --dialog-soft: #0c2642;
  --dialog-line: #35678a;
  --dialog-ink: #e5f6ff;
  --dialog-glow: #58c8fa;
  width: min(100%, 380px);
  box-sizing: border-box;
  padding: 24px;
  border: 1px solid var(--dialog-line);
  border-radius: 10px;
  background: var(--dialog-panel);
  color: var(--dialog-ink);
  box-shadow: 0 12px 36px #020b18aa;
}
.sign-out-dialog-light {
  --dialog-panel: #fff;
  --dialog-soft: #eef3f5;
  --dialog-line: #b5c4cc;
  --dialog-ink: #17252d;
  --dialog-glow: #205b77;
}
.sign-out-dialog h2 {
  margin: 0 0 12px;
  font-size: 1.25rem;
}
.sign-out-dialog p {
  margin: 0 0 20px;
  line-height: 1.55;
}
.sign-out-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
.sign-out-actions button {
  min-height: 44px;
  padding: 8px 12px;
  border: 1px solid var(--dialog-line);
  border-radius: 5px;
  background: var(--dialog-soft);
  color: inherit;
  cursor: pointer;
}
.sign-out-actions button:focus-visible {
  outline: 2px solid var(--dialog-glow);
  outline-offset: 2px;
}
.sign-out-actions button:disabled {
  cursor: default;
  opacity: 0.6;
}
</style>
