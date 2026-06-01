<template>
  <a-config-provider :theme="theme">
    <div class="app-shell">
      <header class="topbar">
        <router-link class="brand" to="/">
          <span class="brand-mark">AI</span>
          <span>
            <strong>云途智旅 <b>AI</b></strong>
            <small>adaptive trip planner</small>
          </span>
        </router-link>
      </header>

      <main class="app-main">
        <router-view />
      </main>
    </div>
  </a-config-provider>
</template>

<script setup lang="ts">
const theme = {
  token: {
    colorPrimary: '#087ee5',
    colorInfo: '#087ee5',
    colorSuccess: '#19a981',
    colorWarning: '#d99021',
    borderRadius: 8,
    fontFamily:
      'Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
  }
}
</script>

<style>
* {
  box-sizing: border-box;
}

html {
  background: #eef8ff;
}

body {
  min-width: 320px;
  margin: 0;
  color: #102534;
  background: #eef8ff;
}

a {
  color: inherit;
  text-decoration: none;
}

.app-shell {
  min-height: 100vh;
}

.topbar {
  position: sticky;
  top: 0;
  z-index: 20;
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 62px;
  padding: 0 36px;
  border-bottom: 1px solid rgba(8, 126, 229, 0.12);
  background: rgba(235, 249, 255, 0.84);
  backdrop-filter: blur(16px);
}

.brand {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.brand-mark {
  display: inline-grid;
  width: 34px;
  height: 34px;
  place-items: center;
  border: 2px solid rgba(8, 126, 229, 0.18);
  border-radius: 50%;
  background: #fff;
  color: #087ee5;
  font-size: 11px;
  font-weight: 900;
}

.brand strong,
.brand small {
  display: block;
  line-height: 1.1;
}

.brand strong {
  color: #0c2638;
  font-size: 18px;
  letter-spacing: 0;
}

.brand strong b {
  color: #087ee5;
}

.brand small {
  margin-top: 4px;
  color: #5f7888;
  font-size: 12px;
}

.app-main {
  min-height: calc(100vh - 62px);
}

@media (max-width: 760px) {
  .topbar {
    padding: 0 18px;
  }

}
</style>
