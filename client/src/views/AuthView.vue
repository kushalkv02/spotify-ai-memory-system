<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store/user'

const router = useRouter()
const userStore = useUserStore()
const mode = ref('login')
const login = ref('')
const email = ref('')
const displayName = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function submit() {
  error.value = ''
  loading.value = true
  try {
    if (mode.value === 'login') await userStore.login({ login: login.value, password: password.value })
    else await userStore.signup({ login: login.value, email: email.value, display_name: displayName.value, password: password.value })
    router.replace('/')
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <main class="auth-page">
    <section class="auth-card">
      <p class="eyebrow">Reverie</p>
      <h1>{{ mode === 'login' ? 'Welcome back' : 'Start listening' }}</h1>
      <p class="auth-copy">{{ mode === 'login' ? 'Log in to return to your listening room.' : 'Create your personal listening room.' }}</p>

      <form @submit.prevent="submit">
        <label>Login <input v-model.trim="login" autocomplete="username" minlength="3" required placeholder="your-login" /></label>
        <label v-if="mode === 'signup'">Display name <input v-model.trim="displayName" autocomplete="name" required placeholder="How should we call you?" /></label>
        <label v-if="mode === 'signup'">Email <input v-model.trim="email" type="email" autocomplete="email" required placeholder="you@example.com" /></label>
        <label>Password <input v-model="password" type="password" :autocomplete="mode === 'login' ? 'current-password' : 'new-password'" minlength="8" required placeholder="At least 8 characters" /></label>
        <p v-if="error" class="auth-error" role="alert">{{ error }}</p>
        <button class="btn-pill auth-submit" :disabled="loading">{{ loading ? 'Please wait…' : mode === 'login' ? 'Log in' : 'Create account' }}</button>
      </form>

      <button class="auth-switch" @click="mode = mode === 'login' ? 'signup' : 'login'; error = ''">
        {{ mode === 'login' ? 'New to Reverie? Create an account' : 'Already have an account? Log in' }}
      </button>
    </section>
  </main>
</template>

<style scoped>
.auth-page { min-height: 100vh; display: grid; place-items: center; padding: 24px; background: radial-gradient(circle at 20% 0%, #332146, var(--bg-void) 50%); }
.auth-card { width: min(100%, 420px); padding: 38px; border: 1px solid var(--line); border-radius: var(--radius-lg); background: var(--bg-panel); box-shadow: var(--shadow-panel); }
h1 { margin-top: 8px; font-size: 36px; }
.auth-copy { color: var(--text-secondary); margin: 8px 0 26px; }
form { display: grid; gap: 15px; }
label { display: grid; gap: 6px; color: var(--text-secondary); font-size: 12px; font-weight: 700; }
input { width: 100%; padding: 11px 12px; border: 1px solid var(--line); border-radius: var(--radius-sm); background: var(--bg-raised); color: var(--text-primary); }
.auth-submit { justify-content: center; margin-top: 8px; }
.auth-switch { margin-top: 20px; color: var(--accent); font-size: 13px; }
.auth-error { margin: 0; color: var(--danger); font-size: 13px; }
</style>
