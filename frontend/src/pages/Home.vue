<template>
  <div class="min-h-screen bg-gradient-to-b from-slate-50 to-white py-8 px-4">
    <div class="max-w-lg mx-auto">

      <!-- Header -->
      <div class=" mt-20 text-center mb-6">
        <h1 class="text-2xl font-bold bg-gradient-to-r from-indigo-600 to-violet-500 bg-clip-text text-transparent">
          Video to Notes
        </h1>
        <p class="text-xs text-slate-500 mt-1">AI-powered notes from lectures & meetings</p>
      </div>

      <!-- Main Card -->
      <div class="bg-white/80 backdrop-blur-sm rounded-2xl shadow-sm shadow-slate-200/60 p-5 border border-slate-100 transition-all duration-300">

        <!-- Upload Section (shown when idle or after completion) -->
        <Transition name="fade" mode="out-in">
          <div v-if="!isProcessing" key="upload" class="space-y-4">

            <!-- Drop Zone -->
            <div
              class="border-2 border-dashed border-slate-200 hover:border-indigo-300 hover:bg-indigo-50/30 rounded-xl p-6 transition-all duration-200 cursor-pointer group"
              @click="triggerFileInput"
              @drop.prevent="handleDrop"
              @dragover.prevent
            >
              <div class="flex flex-col items-center">
                <span class="text-3xl mb-2 text-slate-300 group-hover:text-indigo-400 transition-colors">📤</span>
                <p class="text-sm font-medium text-slate-600 group-hover:text-indigo-600 transition-colors">
                  Drop video or click to upload
                </p>
                <p class="text-xs text-slate-400 mt-1">MP4, MOV • Max 2GB</p>
              </div>
            </div>

            <!-- Hidden Input -->
            <input ref="fileInput" type="file" accept="video/*" class="hidden" @change="handleFileSelect" />

            <!-- Selected File -->
            <Transition name="slide">
              <div v-if="selectedFile" class="bg-slate-50 rounded-xl p-3 flex items-center gap-3">
                <span class="text-lg">🎞️</span>
                <div class="flex-1 min-w-0">
                  <p class="text-sm font-medium text-slate-700 truncate">{{ selectedFile.name }}</p>
                  <p class="text-xs text-slate-400">{{ formatFileSize(selectedFile.size) }}</p>
                </div>
                <button
                  @click="removeFile"
                  class="text-slate-400 hover:text-rose-500 text-xs font-medium transition-colors px-2 py-1 rounded-lg hover:bg-rose-50"
                >
                  ✕
                </button>
              </div>
            </Transition>

            <!-- Generate Button -->
            <button
              :disabled="!selectedFile || isUploading"
              @click="uploadVideo"
              class="w-full bg-gradient-to-r from-indigo-500 to-violet-500 hover:from-indigo-600 hover:to-violet-600 disabled:from-slate-300 disabled:to-slate-300 text-white font-medium py-3 rounded-xl transition-all duration-200 flex items-center justify-center gap-2 text-sm shadow-sm shadow-indigo-200/40 hover:shadow-indigo-300/60 disabled:shadow-none active:scale-[0.98]"
            >
              <Transition mode="out-in">
                <span v-if="isUploading" key="loading" class="flex items-center gap-2">
                  <span class="w-4 h-4 border-2 border-white/60 border-t-white rounded-full animate-spin"></span>
                  Uploading...
                </span>
                <span v-else key="idle">Generate Notes ✨</span>
              </Transition>
            </button>
          </div>

          <!-- Processing Section (replaces upload while AI works) -->
          <div v-else key="processing" class="space-y-4">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 bg-indigo-50 rounded-xl flex items-center justify-center">
                  <span class="text-xl animate-pulse">🤖</span>
                </div>
                <div>
                  <p class="text-sm font-medium text-slate-700">AI is working...</p>
                  <p class="text-xs text-slate-400">This may take 1–4 minutes</p>
                </div>
              </div>

              <!-- Cancel Button -->
              <button
                @click="cancelProcessing"
                :disabled="isCanceling"
                class="text-xs font-medium text-rose-500 hover:text-rose-600 hover:bg-rose-50 px-3 py-1.5 rounded-lg transition-all active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
              >
                <Transition mode="out-in">
                  <span v-if="isCanceling" key="canceling" class="flex items-center gap-1">
                    <span class="w-3 h-3 border-2 border-rose-400 border-t-transparent rounded-full animate-spin"></span>
                    Stopping...
                  </span>
                  <span v-else key="idle">✕ Cancel</span>
                </Transition>
              </button>
            </div>

            <!-- Progress -->
            <div>
              <div class="flex justify-between text-xs mb-1.5">
                <span class="text-slate-500">Progress</span>
                <span class="font-medium text-indigo-600">{{ Math.round(progress) }}%</span>
              </div>
              <div class="h-2 bg-slate-100 rounded-full overflow-hidden">
                <div
                  class="h-full bg-gradient-to-r from-indigo-500 to-violet-500 transition-all duration-500 ease-out"
                  :style="{ width: progress + '%' }"
                ></div>
              </div>
            </div>

            <p class="text-xs text-slate-400 text-center pt-1">
              Keep this tab open • You can cancel anytime
            </p>
          </div>
        </Transition>

        <!-- Result Section (appears below after completion) -->
        <Transition name="slide-up">
          <div v-if="isDone && jobId" class="mt-4 pt-4 border-t border-slate-100">

            <!-- Success State -->
            <div class="flex items-start gap-3">
              <!-- Soft success icon -->
              <div class="shrink-0 w-8 h-8 bg-emerald-50 rounded-lg flex items-center justify-center">
                <span class="text-lg animate-[bounce_0.6s_ease-out]">✨</span>
              </div>

              <!-- Message + Actions -->
              <div class="flex-1 min-w-0">
                <p class="text-sm font-medium text-slate-700">
                  Your notes are ready
                </p>
                <p class="text-xs text-slate-400 mt-0.5">
                  Download or start a new video anytime
                </p>

                <!-- Elegant Button Group -->
                <div class="flex gap-2 mt-3">
                  <!-- Primary: Download -->
                  <button
                    @click="downloadNotes"
                    class="group flex-1 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white text-xs font-medium py-2.5 rounded-xl transition-all duration-200 flex items-center justify-center gap-1.5 shadow-sm shadow-emerald-200/40 hover:shadow-emerald-300/60 active:scale-[0.98] active:shadow-none"
                  >
                    <span class="transition-transform group-hover:-translate-y-0.5">↓</span>
                    <span>Get notes.md</span>
                  </button>

                  <!-- Secondary: New Video -->
                  <button
                    @click="resetForNext"
                    class="group px-4 bg-white hover:bg-slate-50 text-slate-600 hover:text-slate-800 text-xs font-medium py-2.5 rounded-xl border border-slate-200 hover:border-slate-300 transition-all duration-200 active:scale-[0.98] shadow-sm shadow-slate-100/40 hover:shadow-slate-200/60"
                  >
                    <span class="transition-transform group-hover:translate-x-0.5">New →</span>
                  </button>
                </div>
              </div>
            </div>

          </div>
        </Transition>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onUnmounted } from 'vue'

const fileInput = ref<HTMLInputElement | null>(null)
const selectedFile = ref<File | null>(null)
const isUploading = ref(false)
const isProcessing = ref(false)
const isCanceling = ref(false)
const isDone = ref(false)
const jobId = ref<string | null>(null)
const progress = ref(0)
const markdownContent = ref<string>('')

let pollInterval: number | null = null
let abortController: AbortController | null = null

const triggerFileInput = () => fileInput.value?.click()

const handleFileSelect = (e: Event) => {
  const target = e.target as HTMLInputElement
  if (target.files?.[0]) selectedFile.value = target.files[0]
}

const handleDrop = (e: DragEvent) => {
  const file = e.dataTransfer?.files?.[0]
  if (file?.type.startsWith('video/')) selectedFile.value = file
}

const removeFile = () => {
  selectedFile.value = null
  if (fileInput.value) fileInput.value.value = ''
}

const formatFileSize = (bytes: number): string => {
  if (!bytes) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / k ** i).toFixed(2))} ${sizes[i]}`
}

const startPolling = (id: string) => {
  if (pollInterval) clearInterval(pollInterval)

  pollInterval = setInterval(async () => {
    try {
      const res = await fetch(`http://127.0.0.1:5000/api/status/${id}`)
      const data = await res.json()

      if (data.status === 'done') {
        clearInterval(pollInterval!)
        progress.value = 100

        try {
          const notesRes = await fetch(`http://127.0.0.1:5000/api/notes/${id}`)
          markdownContent.value = await notesRes.text()
          isDone.value = true
          isProcessing.value = false
        } catch {
          markdownContent.value = 'Notes generated (preview unavailable)'
          isDone.value = true
          isProcessing.value = false
        }
      } else if (data.status === 'failed') {
        clearInterval(pollInterval!)
        alert('Processing failed: ' + (data.error || 'Unknown error'))
        isProcessing.value = false
      } else if (data.status === 'canceled') {
        // Backend confirmed cancellation
        clearInterval(pollInterval!)
        isProcessing.value = false
        isCanceling.value = false
      } else {
        if (progress.value < 92) {
          progress.value += Math.random() * 6 + 1
        }
      }
    } catch (err) {
      console.error('Polling error:', err)
    }
  }, 2000)
}

const uploadVideo = async () => {
  if (!selectedFile.value) return

  isUploading.value = true
  isProcessing.value = true
  isDone.value = false
  isCanceling.value = false
  progress.value = 5
  markdownContent.value = ''
  abortController = new AbortController()

  const formData = new FormData()
  formData.append('video', selectedFile.value)

  try {
    const res = await fetch('http://127.0.0.1:5000/api/process', {
      method: 'POST',
      body: formData,
      signal: abortController.signal
    })
    const data = await res.json()

    if (res.ok && data.job_id) {
      jobId.value = data.job_id
      startPolling(data.job_id)
    } else {
      alert(data.error || 'Failed to start processing')
      isProcessing.value = false
    }
  } catch (err: any) {
    if (err.name === 'AbortError') {
      // Upload was canceled - expected
      console.log('Upload canceled')
    } else {
      alert('Cannot connect to server')
    }
    isProcessing.value = false
  } finally {
    isUploading.value = false
  }
}

const cancelProcessing = async () => {
  if (!jobId.value || isCanceling.value) return

  isCanceling.value = true

  // Stop polling first
  if (pollInterval) {
    clearInterval(pollInterval)
    pollInterval = null
  }

  // Abort any pending upload request
  if (abortController) {
    abortController.abort()
    abortController = null
  }

  try {
    // Try to notify backend (graceful if endpoint doesn't exist)
    await fetch(`http://127.0.0.1:5000/api/cancel/${jobId.value}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    }).catch(() => {
      // Backend may not have cancel endpoint - that's okay
      console.log('Cancel endpoint not available, cleaning up locally')
    })
  } finally {
    // Reset UI state
    isProcessing.value = false
    isCanceling.value = false
    isDone.value = false
    progress.value = 0
    markdownContent.value = ''

    // Keep selectedFile so user can retry or remove
  }
}

const downloadNotes = () => {
  if (jobId.value) {
    window.open(`http://127.0.0.1:5000/api/notes/${jobId.value}`, '_blank')
  }
}

const resetForNext = () => {
  selectedFile.value = null
  jobId.value = null
  markdownContent.value = ''
  isDone.value = false
  isProcessing.value = false
  isCanceling.value = false
  progress.value = 0
  if (fileInput.value) fileInput.value.value = ''
}

onUnmounted(() => {
  if (pollInterval) clearInterval(pollInterval)
  if (abortController) abortController.abort()
})
</script>

<style scoped>
/* Transitions */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-enter-active,
.slide-leave-active {
  transition: all 0.25s ease-out;
}
.slide-enter-from {
  opacity: 0;
  transform: translateY(-6px);
}
.slide-leave-to {
  opacity: 0;
  transform: translateY(6px);
}

.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.slide-up-enter-from {
  opacity: 0;
  transform: translateY(12px);
}
.slide-up-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

/* Focus states */
button:focus-visible {
  outline: 2px solid rgb(129 140 248 / 0.35);
  outline-offset: 2px;
}

/* Scrollbar for preview */
pre::-webkit-scrollbar {
  height: 4px;
}
pre::-webkit-scrollbar-track {
  background: transparent;
}
pre::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 2px;
}
pre::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}
</style>