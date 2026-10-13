<script setup lang="ts">
import { X } from 'lucide-vue-next'

defineProps<{
  src: string
  show: boolean
}>()

const emit = defineEmits<{
  close: []
}>()
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="show"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm"
        @click.self="emit('close')"
      >
        <button
          class="absolute top-6 right-6 p-3 rounded-full bg-white/10 text-white hover:bg-white/20 transition-colors"
          @click="emit('close')"
        >
          <X class="w-6 h-6" />
        </button>
        <img
          :src="src"
          class="max-w-[95vw] max-h-[95vh] rounded-xl object-contain shadow-2xl"
        />
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.modal-enter-active {
  transition: opacity 0.3s cubic-bezier(0.35, 0, 0, 1);
}
.modal-leave-active {
  transition: opacity 0.2s cubic-bezier(0.35, 0, 0, 1);
}
.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
</style>
