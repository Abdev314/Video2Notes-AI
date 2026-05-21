<template>
  <div class="min-h-screen bg-gradient-to-b from-slate-50 to-white py-8 px-4">
    <div class="max-w-lg mx-auto">

      <!-- Header -->
      <div class="mt-20 text-center mb-6">
        <h1 class="text-2xl font-bold bg-gradient-to-r from-indigo-600 to-violet-500 bg-clip-text text-transparent">
          Video to Notes
        </h1>
        <p class="text-xs text-slate-500 mt-1">AI-powered notes from lectures & meetings</p>
      </div>

      <!-- Main Card -->
      <div class="bg-white/80 backdrop-blur-sm rounded-2xl shadow-sm shadow-slate-200/60 p-5 border border-slate-100 transition-all duration-300">

        <!-- Upload Section -->
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
                <span class="text-3xl mb-2 text-slate-300 group-hover:text-indigo-400 transition-colors">↓</span>
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
                <span class="text-lg">🎬</span>
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

          <!-- Processing Section -->
          <div v-else key="processing" class="space-y-4">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 bg-indigo-50 rounded-xl flex items-center justify-center">
                  <span class="text-xl animate-pulse">⚙️</span>
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

        <!-- Result Section -->
        <Transition name="slide-up">
          <div v-if="isDone && jobId" class="mt-5 pt-5 border-t border-slate-100 space-y-4">

            <!-- Success Header -->
            <div class="flex items-center gap-3">
              <div class="w-9 h-9 bg-emerald-50 rounded-xl flex items-center justify-center">
                <span class="text-lg animate-[bounce_0.5s_ease-out]">✨</span>
              </div>
              <div>
                <p class="text-sm font-medium text-slate-800">Your notes are ready</p>
                <p class="text-xs text-slate-400">Download in your preferred format</p>
              </div>
            </div>

            <!-- Download Button with Format Selector -->
            <div class="relative" ref="dropdownRef">
              <div class="flex shadow-sm rounded-xl overflow-hidden">
                <!-- Primary Download Button (dynamic label) -->
                <button
                  @click="downloadCurrentFormat"
                  class="flex-1 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white text-sm font-medium py-2.5 transition-all duration-200 active:scale-[0.98] flex items-center justify-center gap-2"
                >
                  <span>↓ Get notes.{{ currentFormatExt }}</span>
                </button>

                <!-- Format Selector Toggle -->
                <button
                  @click.stop="toggleMenu"
                  class="w-10 bg-emerald-600/90 hover:bg-emerald-700 text-white/90 transition-all duration-200 active:scale-[0.98] flex items-center justify-center border-l border-white/20"
                  :aria-label="'Change format'"
                >
                  <svg class="w-4 h-4 transition-transform duration-200" :class="{ 'rotate-180': showDownloadMenu }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
                  </svg>
                </button>
              </div>

              <!-- Format Dropdown Menu -->
              <Transition name="fade-scale">
                <div
                  v-if="showDownloadMenu"
                  class="absolute right-0 mt-2 w-48 bg-white/95 backdrop-blur-sm rounded-xl shadow-lg border border-slate-100 py-1.5 z-20 origin-top-right"
                  @click.stop
                >
                  <button
                    v-for="fmt in formats"
                    :key="fmt.value"
                    @click="selectFormat(fmt.value); closeMenu()"
                    class="w-full px-4 py-2.5 text-left hover:bg-slate-50 flex items-center justify-between transition-colors"
                    :class="{ 'bg-slate-50': selectedFormat === fmt.value }"
                  >
                    <span class="text-sm font-medium text-slate-700">{{ fmt.label }}</span>
                    <span class="text-[10px] text-slate-400">.{{ fmt.ext }}</span>
                  </button>
                </div>
              </Transition>
            </div>

            <!-- New Video -->
            <button
              @click="resetForNext"
              class="w-full text-xs text-slate-400 hover:text-slate-600 py-2 transition-colors flex items-center justify-center gap-1"
            >
              <span>↻</span> Upload another video
            </button>
          </div>
        </Transition>

      </div>


  </div>
          <!-- AI Status Dashboard - Full Page Section -->
    <div class="mt-16">
      <h2 class="text-2xl font-semibold mb-6 text-center">System Status</h2>
      <AIStatusPanel />
    </div>
  </div>


</template>

<script setup lang="ts">
import {ref, onUnmounted, onMounted, computed} from 'vue'
import { saveAs } from 'file-saver'
import jsPDF from 'jspdf'
import { Document, Packer, Paragraph, TextRun, HeadingLevel, ImageRun } from 'docx'
import AIStatusPanel from "@/pages/AIStatusPanel.vue";
// State
const fileInput = ref<HTMLInputElement | null>(null)
const selectedFile = ref<File | null>(null)
const isUploading = ref(false)
const isProcessing = ref(false)
const isCanceling = ref(false)
const isDone = ref(false)
const jobId = ref<string | null>(null)
const progress = ref(0)
const markdownContent = ref<string>('')

// Download format state
const selectedFormat = ref<'md' | 'pdf' | 'docx'>('md')
const showDownloadMenu = ref(false)
const dropdownRef = ref<HTMLElement | null>(null)

const formats = [
  { label: 'Markdown', value: 'md' as const, ext: 'md' },
  { label: 'PDF', value: 'pdf' as const, ext: 'pdf' },
  { label: 'Word', value: 'docx' as const, ext: 'docx' }
] as const

const currentFormatExt = computed(() =>
  formats.find(f => f.value === selectedFormat.value)?.ext || 'md'
)

// Dropdown handlers
const toggleMenu = () => showDownloadMenu.value = !showDownloadMenu.value
const closeMenu = () => showDownloadMenu.value = false
const selectFormat = (fmt: 'md' | 'pdf' | 'docx') => { selectedFormat.value = fmt }

const handleClickOutside = (e: MouseEvent) => {
  if (dropdownRef.value && !dropdownRef.value.contains(e.target as Node)) {
    closeMenu()
  }
}

onMounted(() => document.addEventListener('click', handleClickOutside))
onUnmounted(() => document.removeEventListener('click', handleClickOutside))

// Download functions (backend-agnostic)
const downloadCurrentFormat = async () => {
  if (!markdownContent.value || !jobId.value) return
  const filename = `notes-${jobId.value.slice(0, 8)}`

  if (selectedFormat.value === 'md') {
    downloadMarkdown(filename)
  } else if (selectedFormat.value === 'pdf') {
    await downloadPDF(filename)
  } else if (selectedFormat.value === 'docx') {
    await downloadWord(filename)
  }
}

const downloadMarkdown = (filename: string) => {
  const blob = new Blob([markdownContent.value], { type: 'text/markdown;charset=utf-8' })
  saveAs(blob, `${filename}.md`)
}

type ParsedChapter = {
  id: string
  title: string
  timestampLabel?: string
  durationLabel?: string
  summary?: string
  keyPoints: string[]
  imageSrc?: string
}

const parseNotesMarkdown = (md: string): { title: string, chapters: ParsedChapter[] } => {
  const lines = md.split(/\r?\n/)
  let docTitle = "Video Notes"

  for (const line of lines) {
    const m = line.match(/^#\s+(.+)\s*$/)
    if (m && m[1]) { docTitle = m[1].trim(); break }
  }

  const chapters: ParsedChapter[] = []
  let i = 0
  while (i < lines.length) {
    const line0 = lines[i] ?? ""
    const start = line0.match(/^##\s+Chapter\s+(\d+)\s+—\s+(.+)\s*$/)
    if (!start) { i++; continue }

    const chapter: ParsedChapter = {
      id: start[1]!,
      title: (start[2] || "").trim(),
      keyPoints: [],
    }
    i += 1

    // Scan until next chapter heading (or EOF)
    const summaryLines: string[] = []
    let inKeyPoints = false
    let inTranscript = false
    while (i < lines.length && !(lines[i] ?? "").startsWith("## Chapter ")) {
      const line = lines[i] ?? ""

      if (line.startsWith("<details>")) inTranscript = true
      if (inTranscript) {
        if (line.startsWith("</details>")) inTranscript = false
        i += 1
        continue
      }

      const ts = line.match(/⏱\s+\*\*(.*?)\*\*\s*·\s*(.+)\s*$/)
      if (ts) {
        chapter.timestampLabel = (ts[1] || "").trim()
        chapter.durationLabel = (ts[2] || "").trim()
        i += 1
        continue
      }

      const img = line.match(/!\[[^\]]*\]\(([^)]+)\)/)
      if (img) {
        chapter.imageSrc = (img[1] || "").trim()
        i += 1
        continue
      }

      if (line.trim() === "**Key points:**") {
        inKeyPoints = true
        i += 1
        continue
      }

      if (inKeyPoints) {
        const kp = line.match(/^\-\s+(.+)\s*$/)
        if (kp) {
          chapter.keyPoints.push((kp[1] || "").trim())
          i += 1
          continue
        }
        // End key points section when we hit a blank or non-bullet.
        if (line.trim() === "" || !line.trim().startsWith("-")) {
          inKeyPoints = false
          i += 1
          continue
        }
      }

      // Ignore footer separator
      if (line.trim() === "---") break

      if (line.trim() !== "") summaryLines.push(line)
      i += 1
    }

    const summary = summaryLines.join("\n").trim()
    if (summary) chapter.summary = summary
    chapters.push(chapter)
  }

  return { title: docTitle, chapters }
}

const dataUriToBytes = async (dataUri: string): Promise<Uint8Array> => {
  const res = await fetch(dataUri)
  const buf = await res.arrayBuffer()
  return new Uint8Array(buf)
}

const dataUriToDocxType = (dataUri: string): "jpg" | "png" | "gif" | "bmp" | null => {
  const m = dataUri.match(/^data:image\/([a-zA-Z0-9+.-]+);base64,/)
  if (!m) return null
  const fmt = (m[1] || "").toLowerCase()
  if (fmt === "jpeg" || fmt === "jpg") return "jpg"
  if (fmt === "png") return "png"
  if (fmt === "gif") return "gif"
  if (fmt === "bmp") return "bmp"
  return null
}

const loadImageSize = (src: string): Promise<{ width: number, height: number }> =>
  new Promise((resolve, reject) => {
    const img = new Image()
    img.onload = () => resolve({ width: img.naturalWidth || img.width, height: img.naturalHeight || img.height })
    img.onerror = (e) => reject(e)
    img.src = src
  })

const downloadPDF = async (filename: string) => {
  const parsed = parseNotesMarkdown(markdownContent.value)
  const doc = new jsPDF('p', 'mm', 'a4')
  const margin = 20
  const pageWidth = doc.internal.pageSize.getWidth()
  const pageHeight = doc.internal.pageSize.getHeight()
  const textWidth = pageWidth - 2 * margin

  let y = 20

  const ensureSpace = (neededMm: number) => {
    if (y + neededMm <= pageHeight - margin) return
    doc.addPage()
    y = margin
  }

  const addWrappedText = (text: string, fontSize = 11, extraSpacing = 2) => {
    doc.setFontSize(fontSize)
    const lines = doc.splitTextToSize(text, textWidth)
    ensureSpace(lines.length * (fontSize * 0.42) + 4)
    doc.text(lines, margin, y)
    y += lines.length * (fontSize * 0.42) + extraSpacing
  }

  doc.setFontSize(18)
  doc.text(parsed.title || "Video Notes", pageWidth / 2, y, { align: 'center' })
  y += 10

  for (const ch of parsed.chapters) {
    ensureSpace(12)
    doc.setFontSize(14)
    doc.text(`Chapter ${ch.id} - ${ch.title || "Untitled"}`, margin, y)
    y += 7

    const tsParts = [ch.timestampLabel ? `Time: ${ch.timestampLabel}` : null, ch.durationLabel ? `Duration: ${ch.durationLabel}` : null]
      .filter(Boolean)
      .join("   ")
    if (tsParts) addWrappedText(tsParts, 10, 3)

    if (ch.imageSrc && ch.imageSrc.startsWith("data:image/")) {
      try {
        const { width, height } = await loadImageSize(ch.imageSrc)
        const maxW = textWidth
        const maxH = 90
        const pxToMm = 0.264583 // 96dpi px -> mm
        const wMm0 = width * pxToMm
        const hMm0 = height * pxToMm
        const ratio = Math.min(maxW / wMm0, maxH / hMm0, 1)
        const wMm = wMm0 * ratio
        const hMm = hMm0 * ratio
        ensureSpace(hMm + 6)

        const fmt = (ch.imageSrc.match(/^data:image\/(png|jpeg|jpg|webp)/)?.[1] || "jpeg")
          .toUpperCase()
          .replace("JPG", "JPEG")
        doc.addImage(ch.imageSrc, fmt as any, margin, y, wMm, hMm)
        y += hMm + 4
      } catch {}
    }

    if (ch.summary) addWrappedText(ch.summary, 11, 4)

    if (ch.keyPoints.length) {
      addWrappedText("Key points:", 11, 2)
      for (const p of ch.keyPoints) addWrappedText(`• ${p}`, 11, 1)
      y += 2
    }
  }

  doc.save(`${filename}.pdf`)
}

const downloadWord = async (filename: string) => {
  const parsed = parseNotesMarkdown(markdownContent.value)
  const children: Paragraph[] = []

  children.push(new Paragraph({ text: parsed.title || "Video Notes", heading: HeadingLevel.HEADING_1 }))

  for (const ch of parsed.chapters) {
    children.push(new Paragraph({ text: `Chapter ${ch.id} - ${ch.title || "Untitled"}`, heading: HeadingLevel.HEADING_2 }))

    const ts = [ch.timestampLabel ? `Time: ${ch.timestampLabel}` : null, ch.durationLabel ? `Duration: ${ch.durationLabel}` : null]
      .filter(Boolean)
      .join("    ")
    if (ts) children.push(new Paragraph({ children: [new TextRun({ text: ts, size: 20 })] }))

    if (ch.imageSrc && ch.imageSrc.startsWith("data:image/")) {
      try {
        const bytes = await dataUriToBytes(ch.imageSrc)
        const { width, height } = await loadImageSize(ch.imageSrc)
        const docxType = dataUriToDocxType(ch.imageSrc)
        if (!docxType) throw new Error("unsupported image type")
        const maxW = 560
        const maxH = 360
        const ratio = Math.min(maxW / width, maxH / height, 1)
        children.push(new Paragraph({
          children: [
            new ImageRun({
              type: docxType,
              data: bytes,
              transformation: {
                width: Math.round(width * ratio),
                height: Math.round(height * ratio),
              }
            })
          ]
        }))
      } catch {}
    }

    if (ch.summary) {
      for (const para of ch.summary.split(/\n\s*\n/)) {
        const t = para.trim()
        if (t) children.push(new Paragraph({ children: [new TextRun({ text: t, size: 24 })] }))
      }
    }

    if (ch.keyPoints.length) {
      children.push(new Paragraph({ children: [new TextRun({ text: "Key points:", size: 24 })] }))
      for (const p of ch.keyPoints) children.push(new Paragraph({ text: p, bullet: { level: 0 } }))
    }
  }

  const doc = new Document({ sections: [{ properties: {}, children }] })
  const blob = await Packer.toBlob(doc)
  saveAs(blob, `${filename}.docx`)
}

// File handling
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

// Polling & upload
let pollInterval: ReturnType<typeof setInterval> | null = null
let abortController: AbortController | null = null

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
        } catch {}
        isDone.value = true
        isProcessing.value = false

      } else if (data.status === 'failed') {
        clearInterval(pollInterval!)
        alert('Processing failed: ' + (data.error || 'Unknown error'))
        isProcessing.value = false

      } else if (data.status === 'canceled') {
        clearInterval(pollInterval!)
        isProcessing.value = false
        isCanceling.value = false
        progress.value = 0
        // Optional: show message
        // alert('Processing was canceled.')
      }
      else {
        // Still processing
        if (progress.value < 92) {
          progress.value += Math.random() * 6 + 1
        }
      }
    } catch (err) {
      console.error('Polling error:', err)
    }
  }, 1500)
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
      method: 'POST', body: formData, signal: abortController.signal
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
    if (err.name !== 'AbortError') alert('Cannot connect to server')
    isProcessing.value = false
  } finally { isUploading.value = false }
}

const cancelProcessing = async () => {
  if (!jobId.value || isCanceling.value) return

  isCanceling.value = true

  // Stop polling
  if (pollInterval) {
    clearInterval(pollInterval)
    pollInterval = null
  }

  // Abort upload if still uploading
  if (abortController) {
    abortController.abort()
    abortController = null
  }

  try {
    await fetch(`http://127.0.0.1:5000/api/cancel/${jobId.value}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    }).catch(() => {})
  } finally {
    // Full reset
    isProcessing.value = false
    isCanceling.value = false
    isDone.value = false
    progress.value = 0
    markdownContent.value = ''
    jobId.value = null
    selectedFile.value = null
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
  selectedFormat.value = 'md'
  if (fileInput.value) fileInput.value.value = ''
}

onUnmounted(() => {
  if (pollInterval) clearInterval(pollInterval)
  if (abortController) abortController.abort()
})
</script>

<style scoped>
/* Smooth, relaxing transitions */
.fade-enter-active,
.fade-leave-active { transition: opacity 0.25s cubic-bezier(0.4, 0, 0.2, 1); }
.fade-enter-from, .fade-leave-to { opacity: 0; }

.slide-enter-active,
.slide-leave-active { transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); }
.slide-enter-from { opacity: 0; transform: translateY(-8px); }
.slide-leave-to { opacity: 0; transform: translateY(8px); }

.slide-up-enter-active,
.slide-up-leave-active { transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1); }
.slide-up-enter-from { opacity: 0; transform: translateY(16px); }
.slide-up-leave-to { opacity: 0; transform: translateY(-10px); }

.fade-scale-enter-active,
.fade-scale-leave-active { transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1); }
.fade-scale-enter-from { opacity: 0; transform: scale(0.97) translateY(-4px); }
.fade-scale-leave-to { opacity: 0; transform: scale(0.98) translateY(-2px); }

/* Gentle focus */
button:focus-visible {
  outline: 2px solid rgb(129 140 248 / 0.35);
  outline-offset: 2px;
}

/* Subtle bounce for success */
@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-3px); }
}

/* Respect reduced motion */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
</style>
