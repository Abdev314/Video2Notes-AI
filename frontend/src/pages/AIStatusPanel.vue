<template>
  <div class="space-y-8 p-6 max-w-7xl mx-auto">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <button
        @click="refreshStatus"
        :disabled="loading"
        class="flex items-center gap-2 px-5 py-2.5 bg-white border border-gray-300 rounded-xl hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <RefreshCw class="w-4 h-4" :class="{ 'animate-spin': loading }" />
        {{ loading ? 'Refreshing…' : 'Refresh Status' }}
      </button>
    </div>

    <!-- Error Banner -->
    <div
      v-if="error"
      class="bg-red-50 border border-red-200 text-red-700 rounded-xl px-5 py-3 flex items-center gap-3 text-sm"
    >
      <AlertCircle class="w-4 h-4 flex-shrink-0" />
      {{ error }}
    </div>

    <!-- AI Models -->
    <div>
      <h2 class="text-xl font-semibold mb-4 flex items-center gap-2">
        <Cpu class="w-5 h-5" /> AI Models &amp; Configurations
      </h2>

      <!-- Skeleton while loading -->
      <div v-if="loading && aiModels.length === 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div v-for="n in 3" :key="n" class="bg-white border border-gray-200 rounded-2xl p-6 animate-pulse">
          <div class="h-5 bg-gray-200 rounded w-3/4 mb-2"></div>
          <div class="h-3 bg-gray-100 rounded w-1/2 mb-4"></div>
          <div class="space-y-3">
            <div class="h-3 bg-gray-100 rounded"></div>
            <div class="h-3 bg-gray-100 rounded w-5/6"></div>
          </div>
        </div>
      </div>

      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div
          v-for="(model, idx) in aiModels"
          :key="idx"
          class="bg-white border border-gray-200 rounded-2xl p-6 hover:shadow-md transition-shadow"
        >
          <div class="flex justify-between items-start mb-4">
            <div>
              <h3 class="font-semibold text-lg">{{ model.name }}</h3>
              <p class="text-sm text-gray-500">{{ model.provider }}</p>
            </div>
            <StatusBadge :status="model.status" />
          </div>
          <div class="space-y-3 text-sm">
            <div class="flex justify-between">
              <span class="text-gray-600">Model ID</span>
              <span class="font-mono text-xs bg-gray-100 px-2 py-1 rounded">{{ model.model }}</span>
            </div>
            <div class="flex justify-between items-center">
              <span class="text-gray-600">Health</span>
              <div :class="getHealthClass(model.health)" class="flex items-center gap-1.5">
                <div
                  :class="[
                    'w-2.5 h-2.5 rounded-full',
                    model.health === 'healthy' ? 'bg-green-500' :
                    model.health === 'degraded' ? 'bg-amber-500' : 'bg-red-500'
                  ]"
                ></div>
                <span class="capitalize font-medium">{{ model.health }}</span>
              </div>
            </div>
            <div class="text-xs text-gray-500">
              Last used: <span class="font-medium text-gray-700">{{ model.lastUsed }}</span>
            </div>
            <div v-if="model.status === 'pulling' && model.pullProgress !== undefined" class="pt-2">
              <div class="flex justify-between text-xs mb-1">
                <span>Pulling model...</span>
                <span>{{ model.pullProgress }}%</span>
              </div>
              <div class="w-full bg-gray-200 rounded-full h-1.5">
                <div
                  class="bg-violet-600 h-1.5 rounded-full transition-all duration-300"
                  :style="{ width: model.pullProgress + '%' }"
                ></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import {
  Cpu,
  RefreshCw,
  AlertCircle
} from 'lucide-vue-next'

// ─── Types ────────────────────────────────────────────────────────────────────

interface AIModel {
  name: string
  provider: string
  model: string
  status: 'running' | 'pulled' | 'pulling' | 'not_pulled' | 'error'
  health: 'healthy' | 'degraded' | 'offline'
  lastUsed: string
  pullProgress?: number
}

interface VideoProcessing {
  id: string
  filename: string
  status: 'processing' | 'completed' | 'queued' | 'failed'
  progress: number
  duration: string
  notesGenerated: number
  currentStep?: string
}

interface SystemStats {
  uptime: string | null
  modelsActive: number | null
  videosToday: number | null
  avgInference: string | null
}

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

const OLLAMA_BASE = import.meta.env.VITE_OLLAMA_URL ?? 'http://localhost:11434'

// ─── State ────────────────────────────────────────────────────────────────────

const aiModels = ref<AIModel[]>([])
const videos = ref<VideoProcessing[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

const systemStats = ref<SystemStats>({
  uptime: null,
  modelsActive: null,
  videosToday: null,
  avgInference: null,
})

let pollInterval: ReturnType<typeof setInterval> | null = null

async function fetchModels(): Promise<void> {
  try {
    // ── Strategy 1: dedicated backend route ──────────────────────────────────
    const res = await fetch(`${API_BASE}/api/v1/models`, {
      signal: AbortSignal.timeout(5000),
    })
    if (res.ok) {
      const data = await res.json()
      aiModels.value = (data.models ?? []).map((m: any) => ({
        name: m.name,
        provider: m.provider,
        model: m.model_id,
        status: m.status,
        health: m.health,
        lastUsed: formatLastUsed(m.last_used),
        pullProgress: m.pull_progress,
      }))
      return
    }
  } catch {
    // Fall through to direct Ollama query
  }

  // ── Strategy 2: query Ollama directly + config endpoint ──────────────────
  try {
    const [ollamaRes, configRes] = await Promise.allSettled([
      fetch(`${OLLAMA_BASE}/api/tags`, { signal: AbortSignal.timeout(4000) }),
      fetch(`${API_BASE}/api/v1/config`, { signal: AbortSignal.timeout(4000) }),
    ])

    let ollamaTags: any[] = []
    if (ollamaRes.status === 'fulfilled' && ollamaRes.value.ok) {
      const data = await ollamaRes.value.json()
      ollamaTags = data.models ?? []
    }

    let configAI: any = {}
    if (configRes.status === 'fulfilled' && configRes.value.ok) {
      const data = await configRes.value.json()
      configAI = data.ai ?? {}
    }

    const configuredModel: string = configAI.model ?? ''
    const models: AIModel[] = ollamaTags.map((tag: any) => {
      const isConfigured = tag.name === configuredModel
      return {
        name: friendlyModelName(tag.name),
        provider: 'Ollama',
        model: tag.name,
        status: isConfigured ? 'running' : 'pulled',
        health: 'healthy',
        lastUsed: tag.size ? `${(tag.size / 1e9).toFixed(1)} GB` : 'Available',
      }
    })

    // Prepend Whisper from config (always present when pipeline is configured)
    const whisperSize: string = configAI.whisper_model_size // may be undefined
      ?? (configRes.status === 'fulfilled' ? 'base' : 'base')
    models.unshift({
      name: `Whisper ${getWhisperLabel(whisperSize)}`,
      provider: 'Local / faster-whisper',
      model: `whisper-${whisperSize}`,
      status: 'running',
      health: 'healthy',
      lastUsed: 'Active',
    })

    aiModels.value = models.length > 0 ? models : fallbackModels()
  } catch (err) {
    console.error('Model fetch failed:', err)
    aiModels.value = fallbackModels()
  }
}

async function fetchJobs(): Promise<void> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/jobs`, {
      signal: AbortSignal.timeout(5000),
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const data = await res.json()
    videos.value = (data.jobs ?? []).map((j: any) => ({
      id: j.id,
      filename: j.filename,
      status: j.status,
      progress: j.progress ?? 0,
      duration: typeof j.duration === 'number' ? formatSeconds(j.duration) : (j.duration ?? '—'),
      notesGenerated: j.notes_generated ?? 0,
      currentStep: j.current_step,
    }))
  } catch (err) {
    // Jobs endpoint not yet implemented — silently show empty state
    console.warn('Jobs endpoint unavailable:', err)
    videos.value = []
  }
}

async function fetchStats(): Promise<void> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/stats`, {
      signal: AbortSignal.timeout(5000),
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const data = await res.json()
    systemStats.value = {
      uptime: data.uptime_percent != null ? Number(data.uptime_percent).toFixed(1) : null,
      modelsActive: data.models_active ?? aiModels.value.filter(m => m.health === 'healthy').length,
      videosToday: data.videos_today ?? null,
      avgInference: data.avg_inference_seconds != null ? Number(data.avg_inference_seconds).toFixed(1) : null,
    }
  } catch {
    systemStats.value = {
      ...systemStats.value,
      modelsActive: aiModels.value.filter(m => m.health === 'healthy').length,
    }
  }
}

// ─── Orchestration ────────────────────────────────────────────────────────────

async function loadAll(): Promise<void> {
  loading.value = true
  error.value = null
  try {
    await Promise.all([fetchModels(), fetchJobs()])
    await fetchStats()
  } catch (err: any) {
    error.value = `Failed to load status: ${err?.message ?? 'Unknown error'}`
  } finally {
    loading.value = false
  }
}

async function refreshStatus(): Promise<void> {
  await loadAll()
}

// ─── Lifecycle ────────────────────────────────────────────────────────────────

onMounted(() => {
  loadAll()
  // Poll every 10 s so processing progress stays live
  pollInterval = setInterval(() => {
    if (videos.value.some(v => v.status === 'processing')) {
      fetchJobs()
    }
  }, 10_000)
})

onUnmounted(() => {
  if (pollInterval) clearInterval(pollInterval)
})

// ─── Helpers ─────────────────────────────────────────────────────────────────

function getHealthClass(health: string): string {
  if (health === 'healthy') return 'text-green-600'
  if (health === 'degraded') return 'text-amber-600'
  return 'text-red-600'
}

/** Format an ISO date string or "N min ago" string into a human label */
function formatLastUsed(value: string): string {
  if (!value) return 'Unknown'
  // Already human-readable (e.g. "2 min ago")
  if (!/^\d{4}-/.test(value)) return value
  try {
    const diff = Date.now() - new Date(value).getTime()
    const mins = Math.floor(diff / 60_000)
    if (mins < 1) return 'Just now'
    if (mins < 60) return `${mins} min ago`
    const hrs = Math.floor(mins / 60)
    return `${hrs}h ago`
  } catch {
    return value
  }
}

function formatSeconds(secs: number): string {
  const h = Math.floor(secs / 3600)
  const m = Math.floor((secs % 3600) / 60)
  const s = Math.floor(secs % 60)
  const mm = String(m).padStart(2, '0')
  const ss = String(s).padStart(2, '0')
  return h > 0 ? `${h}:${mm}:${ss}` : `${mm}:${ss}`
}

function friendlyModelName(tag: string): string {
  const map: Record<string, string> = {
    'llama3.1:8b': 'Llama 3.1 8B',
    'llama3.1:70b': 'Llama 3.1 70B',
    'mistral:7b': 'Mistral 7B',
    'gemma2:9b': 'Gemma 2 9B',
    'phi3:mini': 'Phi-3 Mini',
  }
  return map[tag] ?? tag
}

function getWhisperLabel(size: string): string {
  const map: Record<string, string> = {
    tiny: 'Tiny',
    base: 'Base',
    small: 'Small',
    medium: 'Medium',
    'large-v3': 'Large V3',
  }
  return map[size] ?? size
}

/** Shown when all fetch strategies fail — prevents empty screen */
function fallbackModels(): AIModel[] {
  return [
    {
      name: 'Whisper (config)',
      provider: 'Local / faster-whisper',
      model: 'whisper-base',
      status: 'error',
      health: 'offline',
      lastUsed: 'Unknown',
    },
  ]
}
</script>