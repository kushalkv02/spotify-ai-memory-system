<script setup>
defineProps({
  replies: { type: Array, default: () => [] },
  disabled: { type: Boolean, default: false }
})

const emit = defineEmits(['select'])
</script>

<template>
  <div v-if="replies.length" class="quick-replies">
    <button
      v-for="reply in replies"
      :key="reply.id"
      class="quick-replies__chip"
      :disabled="disabled"
      @click="emit('select', reply)"
    >
      {{ reply.label }}
    </button>
  </div>
</template>

<style scoped>
.quick-replies {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding: 4px 2px 2px;
}

.quick-replies__chip {
  padding: 6px 12px;
  border-radius: var(--radius-pill);
  border: 1px solid var(--line);
  background: var(--bg-panel);
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
  transition: border-color 0.15s ease, color 0.15s ease, background 0.15s ease;
}
.quick-replies__chip:hover:not(:disabled) {
  border-color: var(--accent-dim);
  color: var(--accent-strong);
  background: var(--accent-wash);
}
.quick-replies__chip:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
