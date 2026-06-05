import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  BarChart3,
  Bell,
  Camera,
  Cloud,
  Image as ImageIcon,
  Info,
  LayoutDashboard,
  Monitor,
  RefreshCw,
  Settings,
  Video,
  X,
} from 'lucide-react'
import './App.css'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const EDGE_MJPEG_URL = import.meta.env.VITE_EDGE_MJPEG_URL || 'http://localhost:8765/stream.mjpg'

const NAV_ITEMS = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'live', label: 'Live', icon: Video },
  { id: 'events', label: 'Events', icon: Bell },
  { id: 'analytics_addons', label: 'Analytics', icon: BarChart3 },
  { id: 'cameras', label: 'Cameras', icon: Monitor },
  { id: 'settings', label: 'Settings', icon: Settings },
]

const ADMIN_NAV_IDS = new Set(['dashboard', 'live', 'events', 'analytics_addons', 'cameras', 'settings'])
const USER_NAV_IDS = new Set(['dashboard', 'live'])

const PAGE_META = {
  dashboard: {
    eyebrow: 'Live Safety Command',
    title: 'Monitoring Center',
    description: 'Pilih kamera terdaftar untuk melihat live feed dan event terbaru.',
  },
  live: {
    eyebrow: 'Real-time',
    title: 'Live Feed',
    description: 'Streaming berdasarkan kamera yang dipilih dari daftar kamera aktif.',
  },
  events: {
    eyebrow: 'Incident Timeline',
    title: 'Events',
    description: 'Daftar pelanggaran APD terbaru dengan filter kamera dan status.',
  },
  analytics_addons: {
    eyebrow: 'Deep Insights',
    title: 'Analytics Add-ons',
    description: 'Ringkasan kepatuhan dan statistik deteksi per kamera.',
  },
  cameras: {
    eyebrow: 'Camera Operations',
    title: 'Camera Inventory',
    description: 'Kelola kamera yang terdaftar dan sumber stream kamera.',
  },
  settings: {
    eyebrow: 'System Control',
    title: 'Settings',
    description: 'Informasi user aktif dan endpoint sistem utama.',
  },
}

const CAMERA_STATUS_OPTIONS = ['Active', 'Maintenance', 'Inactive']
const VIOLATION_STATUS_OPTIONS = ['Unverified', 'Verified', 'False_Positive']

const FALLBACK_CAMERAS = [
  {
    id: 'local-01',
    name: 'Lokasi Produksi A',
    location: 'Lantai 1 - Area Produksi',
    status: 'Active',
    rtsp_url: 'local://webcam',
  },
  {
    id: 'local-02',
    name: 'Lokasi Produksi B',
    location: 'Lantai 2 - Area Produksi',
    status: 'Maintenance',
    rtsp_url: 'local://placeholder',
  },
  {
    id: 'local-03',
    name: 'Lokasi Warehouse',
    location: 'Gudang - Area Penyimpanan',
    status: 'Inactive',
    rtsp_url: 'local://placeholder',
  },
]

const FALLBACK_VIOLATIONS = [
  {
    id: 'violation-01',
    camera_id: 'local-01',
    missing_apd: { helmet: true, vest: false, boots: false },
    confidence_score: 0.62,
    timestamp: new Date(Date.now() - 1000 * 60 * 12).toISOString(),
    status: 'Unverified',
    snapshot_path: '',
  },
]

const createCameraDraft = (camera = {}) => ({
  name: camera.name || '',
  location: camera.location || '',
  rtsp_url: camera.rtsp_url || 'local://webcam',
  status: camera.status || 'Active',
})

const formatTimestamp = (value) => {
  if (!value) return 'No data'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return 'No data'
  return new Intl.DateTimeFormat('id-ID', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}

const formatPercent = (value) => {
  if (value === null || value === undefined) return 'No data'
  const numberValue = Number(value)
  if (!Number.isFinite(numberValue)) return 'No data'
  return `${numberValue.toFixed(1)}%`
}

const formatMissingApd = (missingApd) => {
  if (!missingApd || typeof missingApd !== 'object') return 'None'
  const missing = Object.entries(missingApd)
    .filter(([, value]) => value)
    .map(([key]) => key.replace(/_/g, ' '))
  return missing.length ? missing.join(', ') : 'None'
}

const getStatusTone = (status = '') => {
  const value = status.toLowerCase()
  if (value.includes('inactive')) return 'status muted'
  if (value.includes('maintenance')) return 'status hold'
  if (value.includes('active')) return 'status good'
  return 'status neutral'
}

const getViolationTone = (status = '') => {
  if (status === 'Verified') return 'status good'
  if (status === 'False_Positive') return 'status muted'
  if (status === 'Unverified') return 'status warn'
  return 'status neutral'
}

const buildSnapshotUrl = (path) => {
  if (!path) return ''
  const normalized = path.startsWith('/') ? path : `/${path}`
  const base = API_BASE_URL.endsWith('/') ? API_BASE_URL.slice(0, -1) : API_BASE_URL
  return `${base}${normalized}`
}

const resolveCameraSource = (camera) => {
  const rawSource = (camera?.rtsp_url || '').trim()
  if (rawSource) return rawSource

  const hints = `${camera?.name || ''} ${camera?.location || ''}`.toLowerCase()
  if (/webcam|local|usb|laptop\s*camera|builtin\s*camera|camera\s*test/.test(hints)) {
    return 'local://webcam'
  }

  return ''
}

const parseFilename = (disposition) => {
  if (!disposition) return ''
  const match = disposition.match(/filename="?([^";]+)"?/) || disposition.match(/filename\*=UTF-8''(.+)/)
  if (!match) return ''
  return decodeURIComponent(match[1])
}

const toIsoDateTime = (value, endOfDay = false) => {
  if (!value) return ''
  return `${value}T${endOfDay ? '23:59:59' : '00:00:00'}`
}

const toQuery = (params) => {
  const searchParams = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value !== '' && value !== null && value !== undefined) {
      searchParams.append(key, value)
    }
  })
  return searchParams.toString()
}

function App() {
  const [token, setToken] = useState(() => localStorage.getItem('apd_token') || '')
  const [user, setUser] = useState(null)
  const [authStatus, setAuthStatus] = useState(token ? 'checking' : 'anon')
  const [loginForm, setLoginForm] = useState({ username: '', password: '' })
  const [loginError, setLoginError] = useState('')
  const [isLoggingIn, setIsLoggingIn] = useState(false)

  const [cameras, setCameras] = useState([])
  const [violations, setViolations] = useState([])
  const [violationsFull, setViolationsFull] = useState([])
  const [detectionSeries, setDetectionSeries] = useState([])
  const [stats, setStats] = useState(null)

  const [cameraLoadFailed, setCameraLoadFailed] = useState(false)
  const [violationLoadFailed, setViolationLoadFailed] = useState(false)
  const [apiHealth, setApiHealth] = useState('checking')

  const [activeNav, setActiveNav] = useState('dashboard')
  const [selectedCameraId, setSelectedCameraId] = useState('')
  const [eventStatusFilter, setEventStatusFilter] = useState('')

  const [violationsLoading, setViolationsLoading] = useState(false)
  const [detectionLoading, setDetectionLoading] = useState(false)

  const [showCameraForm, setShowCameraForm] = useState(false)
  const [cameraFormMode, setCameraFormMode] = useState('create')
  const [editingCameraId, setEditingCameraId] = useState('')
  const [cameraForm, setCameraForm] = useState({
    name: '',
    location: '',
    rtsp_url: 'local://webcam',
    status: 'Active',
  })
  const [cameraFormError, setCameraFormError] = useState('')
  const [isSavingCamera, setIsSavingCamera] = useState(false)
  const [isDeletingCameraId, setIsDeletingCameraId] = useState('')

  const [reportOpen, setReportOpen] = useState(false)
  const [reportFilters, setReportFilters] = useState({
    camera_id: '',
    status_filter: '',
    start_date: '',
    end_date: '',
  })
  const [reportStatus, setReportStatus] = useState(null)
  const [isExporting, setIsExporting] = useState(false)

  const [inspectionModal, setInspectionModal] = useState(null)

  const [streamStatus, setStreamStatus] = useState('idle')
  const [selectedCameraDetail, setSelectedCameraDetail] = useState(null)
  const [updatingViolationId, setUpdatingViolationId] = useState('')

  const cameraList = useMemo(
    () => (cameraLoadFailed || !cameras.length ? FALLBACK_CAMERAS : cameras),
    [cameraLoadFailed, cameras],
  )

  const selectedCamera = useMemo(() => {
    if (!cameraList.length) return null
    const found = cameraList.find((camera) => String(camera.id) === selectedCameraId)
    const baseCamera = found || cameraList[0]
    if (!baseCamera) return null

    if (selectedCameraDetail && String(selectedCameraDetail.id) === String(baseCamera.id)) {
      return { ...baseCamera, ...selectedCameraDetail }
    }

    return baseCamera
  }, [cameraList, selectedCameraId, selectedCameraDetail])

  const cameraMap = useMemo(() => {
    const map = new Map()
    cameraList.forEach((camera) => map.set(String(camera.id), camera))
    return map
  }, [cameraList])

  const filteredViolations = useMemo(() => {
    const source = violationsFull.length
      ? violationsFull
      : violationLoadFailed
        ? FALLBACK_VIOLATIONS
        : violations

    return source.filter((violation) => {
      const byCamera = !selectedCameraId || String(violation.camera_id) === selectedCameraId
      const byStatus = !eventStatusFilter || violation.status === eventStatusFilter
      return byCamera && byStatus
    })
  }, [violations, violationsFull, violationLoadFailed, selectedCameraId, eventStatusFilter])

  const selectedCameraCompliance = useMemo(() => {
    if (!detectionSeries.length) return null
    const totals = detectionSeries.reduce(
      (acc, item) => {
        acc.total += item.total_workers || 0
        acc.compliant += item.compliant_workers || 0
        acc.violating += item.violating_workers || 0
        return acc
      },
      { total: 0, compliant: 0, violating: 0 },
    )

    if (!totals.total) {
      return {
        rate: 0,
        totalWorkers: 0,
        violations: totals.violating,
      }
    }

    return {
      rate: (totals.compliant / totals.total) * 100,
      totalWorkers: totals.total,
      violations: totals.violating,
    }
  }, [detectionSeries])

  // Group violations by day (last 7 days) for the Bar Chart
  const dailyTrend = useMemo(() => {
    const days = []
    const dateCounts = {}
    
    for (let i = 6; i >= 0; i--) {
      const d = new Date()
      d.setDate(d.getDate() - i)
      const dateStr = d.toLocaleDateString('id-ID', { weekday: 'short', day: 'numeric' })
      const key = d.toISOString().slice(0, 10)
      days.push({ key, label: dateStr, count: 0 })
      dateCounts[key] = 0
    }
    
    const source = violationsFull.length
      ? violationsFull
      : violationLoadFailed
        ? FALLBACK_VIOLATIONS
        : violations
        
    source.forEach(v => {
      const matchCamera = !selectedCameraId || String(v.camera_id) === selectedCameraId
      if (matchCamera && v.timestamp) {
        const dateKey = v.timestamp.slice(0, 10)
        if (dateCounts[dateKey] !== undefined) {
          dateCounts[dateKey]++
        }
      }
    })
    
    return days.map(day => ({
      ...day,
      count: dateCounts[day.key] || 0
    }))
  }, [violations, violationsFull, violationLoadFailed, selectedCameraId])

  // Aggregate violation types for the Pie Chart
  const violationDistribution = useMemo(() => {
    let helm = 0
    let rompi = 0
    let boot = 0
    
    const source = violationsFull.length
      ? violationsFull
      : violationLoadFailed
        ? FALLBACK_VIOLATIONS
        : violations
        
    source.forEach(v => {
      const matchCamera = !selectedCameraId || String(v.camera_id) === selectedCameraId
      if (matchCamera && v.missing_apd && typeof v.missing_apd === 'object') {
        Object.entries(v.missing_apd).forEach(([key, val]) => {
          if (val === true || val === 'true') {
            const k = key.toLowerCase()
            if (k.includes('helmet') || k.includes('hardhat')) {
              helm++
            } else if (k.includes('vest')) {
              rompi++
            } else if (k.includes('boot')) {
              boot++
            }
          }
        })
      }
    })
    
    const total = helm + rompi + boot
    return { helm, rompi, boot, total }
  }, [violations, violationsFull, violationLoadFailed, selectedCameraId])

  const authHeaders = useMemo(
    () => ({ Authorization: `Bearer ${token}` }),
    [token],
  )

  const canManageCameras = user?.role === 'Admin_IT'
  const visibleNavItems = useMemo(() => {
    const allowedIds = canManageCameras ? ADMIN_NAV_IDS : USER_NAV_IDS
    return NAV_ITEMS.filter((item) => allowedIds.has(item.id))
  }, [canManageCameras])

  useEffect(() => {
    if (!visibleNavItems.length) return
    if (!visibleNavItems.some((item) => item.id === activeNav)) {
      setActiveNav(visibleNavItems[0].id)
    }
  }, [activeNav, visibleNavItems])

  useEffect(() => {
    if (!selectedCameraId && cameraList.length) {
      setSelectedCameraId(String(cameraList[0].id))
    }
  }, [selectedCameraId, cameraList])

  useEffect(() => {
    if (authStatus !== 'ready' || !selectedCameraId) {
      setSelectedCameraDetail(null)
      return undefined
    }

    let isMounted = true

    fetch(`${API_BASE_URL}/api/cameras/${selectedCameraId}`, {
      headers: authHeaders,
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error('Failed to load camera detail')
        }
        return response.json()
      })
      .then((data) => {
        if (isMounted) setSelectedCameraDetail(data)
      })
      .catch(() => {
        if (isMounted) setSelectedCameraDetail(null)
      })

    return () => {
      isMounted = false
    }
  }, [authStatus, authHeaders, selectedCameraId])

  useEffect(() => {
    let isMounted = true
    fetch(`${API_BASE_URL}/health`)
      .then((response) => {
        if (!isMounted) return
        setApiHealth(response.ok ? 'online' : 'offline')
      })
      .catch(() => {
        if (isMounted) setApiHealth('offline')
      })

    return () => {
      isMounted = false
    }
  }, [])

  useEffect(() => {
    if (!token) {
      setAuthStatus('anon')
      return
    }

    setAuthStatus('checking')

    fetch(`${API_BASE_URL}/api/auth/me`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error('Unauthorized')
        }
        return response.json()
      })
      .then((data) => {
        setUser(data)
        setAuthStatus('ready')
      })
      .catch(() => {
        setUser(null)
        setAuthStatus('anon')
        setToken('')
        localStorage.removeItem('apd_token')
      })
  }, [token])

  const loadOverview = useCallback(async () => {
    if (authStatus !== 'ready') return

    const cameraPromise = fetch(`${API_BASE_URL}/api/cameras`, { headers: authHeaders })
      .then(async (response) => {
        if (!response.ok) throw new Error('Camera fetch failed')
        return response.json()
      })
      .then((data) => {
        setCameras(Array.isArray(data) ? data : [])
        setCameraLoadFailed(false)
      })
      .catch(() => {
        setCameras([])
        setCameraLoadFailed(true)
      })

    const recentViolationsQuery = toQuery({ limit: 8, camera_id: selectedCameraId || undefined })
    const violationPromise = fetch(`${API_BASE_URL}/api/violations?${recentViolationsQuery}`, {
      headers: authHeaders,
    })
      .then(async (response) => {
        if (!response.ok) throw new Error('Violation fetch failed')
        return response.json()
      })
      .then((data) => {
        setViolations(Array.isArray(data) ? data : [])
        setViolationLoadFailed(false)
      })
      .catch(() => {
        setViolations([])
        setViolationLoadFailed(true)
      })

    const summaryQuery = toQuery({ camera_id: selectedCameraId || undefined })
    const summaryPromise = fetch(`${API_BASE_URL}/api/detections/stats/summary?${summaryQuery}`, {
      headers: authHeaders,
    })
      .then(async (response) => {
        if (!response.ok) throw new Error('Summary fetch failed')
        return response.json()
      })
      .then((data) => setStats(data))
      .catch(() => setStats(null))

    await Promise.all([cameraPromise, violationPromise, summaryPromise])
  }, [authHeaders, authStatus, selectedCameraId])

  const loadDetailedData = useCallback(async () => {
    if (authStatus !== 'ready') return

    const violationsQuery = toQuery({
      limit: 200,
      camera_id: selectedCameraId || undefined,
      status_filter: eventStatusFilter || undefined,
    })

    const statsQuery = toQuery({ limit: 240, camera_id: selectedCameraId || undefined })

    setViolationsLoading(true)
    setDetectionLoading(true)

    const violationsPromise = fetch(`${API_BASE_URL}/api/violations?${violationsQuery}`, {
      headers: authHeaders,
    })
      .then(async (response) => {
        if (!response.ok) throw new Error('Violation fetch failed')
        return response.json()
      })
      .then((data) => setViolationsFull(Array.isArray(data) ? data : []))
      .catch(() => setViolationsFull([]))
      .finally(() => setViolationsLoading(false))

    const seriesPromise = fetch(`${API_BASE_URL}/api/detections/stats?${statsQuery}`, {
      headers: authHeaders,
    })
      .then(async (response) => {
        if (!response.ok) throw new Error('Detection stats fetch failed')
        return response.json()
      })
      .then((data) => setDetectionSeries(Array.isArray(data) ? data : []))
      .catch(() => setDetectionSeries([]))
      .finally(() => setDetectionLoading(false))

    await Promise.all([violationsPromise, seriesPromise])
  }, [authHeaders, authStatus, eventStatusFilter, selectedCameraId])

  const updateViolationStatus = useCallback(
    async (violationId, nextStatus) => {
      if (authStatus !== 'ready' || !violationId) return

      setUpdatingViolationId(violationId)

      try {
        const response = await fetch(`${API_BASE_URL}/api/violations/${violationId}/status`, {
          method: 'PUT',
          headers: {
            ...authHeaders,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            status: nextStatus,
            notes: nextStatus === 'Verified' ? 'Verified from dashboard' : 'Marked as false positive from dashboard',
          }),
        })

        if (!response.ok) {
          const message = await response.text()
          throw new Error(message || 'Failed to update violation status')
        }

        await Promise.all([loadOverview(), loadDetailedData()])
      } catch (error) {
        setReportStatus({
          type: 'error',
          message: error.message || 'Failed to update violation status',
        })
      } finally {
        setUpdatingViolationId('')
      }
    },
    [authHeaders, authStatus, loadDetailedData, loadOverview],
  )

  useEffect(() => {
    loadOverview()
  }, [loadOverview])

  useEffect(() => {
    loadDetailedData()
  }, [loadDetailedData])

  useEffect(() => {
    if (authStatus !== 'ready' || !selectedCamera) {
      setStreamStatus('idle')
      return undefined
    }

    const source = resolveCameraSource(selectedCamera)
    const isLocalWebcam = source.startsWith('local://webcam')
    const isNetworkStream =
      source.startsWith('rtsp://') ||
      source.startsWith('http://') ||
      source.startsWith('https://')

    // Local camera should be consumed from edge relay to avoid webcam contention.
    if (isLocalWebcam) {
      setStreamStatus(EDGE_MJPEG_URL ? 'relay' : 'unsupported')
      return undefined
    }

    if (isNetworkStream) {
      setStreamStatus('relay')
    } else {
      setStreamStatus('unsupported')
    }
    return undefined
  }, [authStatus, selectedCamera])

  const handleLogin = async (event) => {
    event.preventDefault()
    setIsLoggingIn(true)
    setLoginError('')

    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(loginForm),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => null)
        throw new Error(errorData?.detail || 'Login failed')
      }

      const data = await response.json()
      localStorage.setItem('apd_token', data.access_token)
      setToken(data.access_token)
      setUser(data.user)
      setAuthStatus('checking')
      setLoginForm({ username: '', password: '' })
    } catch (error) {
      setLoginError(error.message || 'Login failed')
    } finally {
      setIsLoggingIn(false)
    }
  }

  const handleLogout = () => {
    setToken('')
    setUser(null)
    setAuthStatus('anon')
    localStorage.removeItem('apd_token')
  }

  const openCameraForm = (camera = null) => {
    setCameraFormError('')
    if (camera) {
      setCameraFormMode('edit')
      setEditingCameraId(String(camera.id))
      setCameraForm(createCameraDraft(camera))
      setShowCameraForm(true)
      return
    }

    setCameraFormMode('create')
    setEditingCameraId('')
    setCameraForm(createCameraDraft())
    setShowCameraForm(true)
  }

  const closeCameraForm = () => {
    setShowCameraForm(false)
    setCameraFormMode('create')
    setEditingCameraId('')
    setCameraForm(createCameraDraft())
    setCameraFormError('')
  }

  const handleSaveCamera = async (event) => {
    event.preventDefault()
    setCameraFormError('')

    if (!canManageCameras) {
      setCameraFormError('Only Admin_IT can manage cameras.')
      return
    }

    setIsSavingCamera(true)

    try {
      const isEditMode = cameraFormMode === 'edit' && editingCameraId
      const response = await fetch(
        isEditMode ? `${API_BASE_URL}/api/cameras/${editingCameraId}` : `${API_BASE_URL}/api/cameras`,
        {
          method: isEditMode ? 'PUT' : 'POST',
          headers: {
            ...authHeaders,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(cameraForm),
        },
      )

      if (!response.ok) {
        const errorData = await response.json().catch(() => null)
        throw new Error(errorData?.detail || 'Failed to save camera')
      }

      const savedCamera = await response.json()
      const nextCameraList = isEditMode
        ? cameraList.map((camera) =>
            String(camera.id) === String(editingCameraId) ? { ...camera, ...savedCamera } : camera,
          )
        : [savedCamera, ...cameraList]

      setCameras(nextCameraList)
      setCameraLoadFailed(false)
      setSelectedCameraId(String(savedCamera.id))
      closeCameraForm()
      await loadOverview()
    } catch (error) {
      setCameraFormError(error.message || 'Failed to save camera')
    } finally {
      setIsSavingCamera(false)
    }
  }

  const handleDeleteCamera = async (cameraId) => {
    if (!canManageCameras) return

    const cameraName = cameraList.find((camera) => String(camera.id) === String(cameraId))?.name || 'camera'
    const confirmed = window.confirm(`Hapus ${cameraName}?`)
    if (!confirmed) return

    setIsDeletingCameraId(String(cameraId))

    try {
      const response = await fetch(`${API_BASE_URL}/api/cameras/${cameraId}`, {
        method: 'DELETE',
        headers: {
          ...authHeaders,
        },
      })

      if (!response.ok) {
        const errorText = await response.text().catch(() => '')
        throw new Error(errorText || 'Failed to delete camera')
      }

      const nextCameraList = cameraList.filter((camera) => String(camera.id) !== String(cameraId))
      setCameras(nextCameraList)
      setCameraLoadFailed(false)
      if (String(selectedCameraId) === String(cameraId)) {
        setSelectedCameraId(nextCameraList[0] ? String(nextCameraList[0].id) : '')
      }
      if (String(editingCameraId) === String(cameraId)) {
        closeCameraForm()
      }
      await loadOverview()
    } catch (error) {
      setCameraFormError(error.message || 'Failed to delete camera')
    } finally {
      setIsDeletingCameraId('')
    }
  }

  const handleReportExport = async (event) => {
    event.preventDefault()
    setIsExporting(true)
    setReportStatus(null)

    try {
      const params = toQuery({
        camera_id: reportFilters.camera_id,
        status_filter: reportFilters.status_filter,
        start_date: reportFilters.start_date ? toIsoDateTime(reportFilters.start_date) : '',
        end_date: reportFilters.end_date ? toIsoDateTime(reportFilters.end_date, true) : '',
      })

      const response = await fetch(`${API_BASE_URL}/api/violations/export/xlsx?${params}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => null)
        throw new Error(errorData?.detail || 'Report export failed')
      }

      const contentDisposition = response.headers.get('Content-Disposition')
      const fileName =
        parseFilename(contentDisposition) ||
        `violations_report_${new Date().toISOString().slice(0, 10)}.xlsx`

      const blob = await response.blob()
      const objectUrl = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = objectUrl
      link.download = fileName
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(objectUrl)

      setReportStatus({ type: 'success', message: 'Report downloaded.' })
    } catch (error) {
      setReportStatus({
        type: 'error',
        message: error.message || 'Report export failed',
      })
    } finally {
      setIsExporting(false)
    }
  }

  const pageMeta = PAGE_META[activeNav] || PAGE_META.dashboard
  const resolvedCameraSource = resolveCameraSource(selectedCamera)
  const liveSource = streamStatus === 'relay' ? EDGE_MJPEG_URL : resolvedCameraSource
  const liveIsRelay =
    streamStatus === 'relay' &&
    (liveSource.startsWith('http://') || liveSource.startsWith('https://'))

  const statCards = [
    {
      label: 'Registered Cameras',
      value: cameraList.length,
      detail: 'From camera inventory',
    },
    {
      label: 'Average Compliance',
      value: stats ? formatPercent(stats.average_compliance_rate) : 'No data',
      detail: 'For selected scope',
    },
    {
      label: 'Peak Workers',
      value: stats ? stats.peak_workers : 'No data',
      detail: 'Highest detected workers',
    },
    {
      label: 'Total Violations',
      value: stats ? stats.total_violations : 'No data',
      detail: 'Records in detection stats',
    },
  ]

  if (authStatus !== 'ready') {
    const isChecking = authStatus === 'checking'

    return (
      <div className="auth">
        <div className="auth-card" data-animate>
          <div className="auth-brand">
            <div className="brand-mark">APD</div>
            <div>
              <p className="eyebrow">Vision Monitoring</p>
              <h1>Safety Control Room</h1>
              <p className="muted">
                Masuk untuk memantau live feed, event pelanggaran, dan analytics.
              </p>
              <div className="auth-hint-grid">
                <div className="auth-hint-card">
                  <p className="muted small">Admin</p>
                  <p className="strong">admin / admin123</p>
                </div>
                <div className="auth-hint-card">
                  <p className="muted small">User biasa</p>
                  <p className="strong">pengawas / pengawas123</p>
                </div>
              </div>
            </div>
          </div>
          {isChecking ? (
            <div className="auth-check">
              <p className="strong">Checking session...</p>
              <p className="muted">Validating access token.</p>
            </div>
          ) : (
            <form className="auth-form" onSubmit={handleLogin}>
              <label>
                Username
                <input
                  type="text"
                  placeholder="admin"
                  value={loginForm.username}
                  onChange={(event) =>
                    setLoginForm((prev) => ({ ...prev, username: event.target.value }))
                  }
                  required
                />
              </label>
              <label>
                Password
                <input
                  type="password"
                  placeholder="********"
                  value={loginForm.password}
                  onChange={(event) =>
                    setLoginForm((prev) => ({ ...prev, password: event.target.value }))
                  }
                  required
                />
              </label>
              {loginError ? <div className="auth-error">{loginError}</div> : null}
              <button className="btn primary" type="submit" disabled={isLoggingIn}>
                {isLoggingIn ? 'Signing in...' : 'Sign in'}
              </button>
            </form>
          )}
          <div className="auth-footer">
            <span>Backend:</span>
            <span className={`status ${apiHealth === 'online' ? 'good' : 'muted'}`}>
              {apiHealth === 'online' ? 'Online' : 'Offline'}
            </span>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">APD</div>
          <div>
            <p className="eyebrow">Vision Monitoring</p>
            <p className="brand-name">Safety Dashboard</p>
          </div>
        </div>

        <nav className="nav">
          {visibleNavItems.map((item) => {
            const Icon = item.icon
            return (
              <button
                key={item.id}
                type="button"
                className={activeNav === item.id ? 'nav-item active' : 'nav-item'}
                onClick={() => setActiveNav(item.id)}
              >
                <Icon size={20} className="nav-icon" />
                <span className="nav-label">{item.label}</span>
              </button>
            )
          })}
        </nav>

        <div className="sidebar-footer">
          <div>
            <p className="muted">Signed in as</p>
            <p className="strong">{user?.full_name || user?.username}</p>
            <p className="muted">{user?.role || 'Operator'}</p>
          </div>
          <button className="btn ghost" type="button" onClick={handleLogout}>
            Sign out
          </button>
        </div>
      </aside>

      <main className="main">
        <header className="topbar" data-animate>
          <div>
            <p className="eyebrow">{pageMeta.eyebrow}</p>
            <h1>{pageMeta.title}</h1>
            <p className="muted">{pageMeta.description}</p>
          </div>

          <div className="topbar-actions">
            <label className="field camera-switcher compact">
              Camera
              <select
                value={selectedCamera ? String(selectedCamera.id) : ''}
                onChange={(event) => setSelectedCameraId(event.target.value)}
              >
                {cameraList.map((camera) => (
                  <option key={camera.id} value={camera.id}>
                    {camera.name}
                  </option>
                ))}
              </select>
            </label>

            <div className="pill">API: {apiHealth === 'online' ? 'Online' : 'Offline'}</div>
            <button className="btn ghost" type="button" onClick={loadOverview}>
              <RefreshCw size={14} />
              Refresh
            </button>
            {canManageCameras ? (
              <button className="btn primary" type="button" onClick={() => setReportOpen(true)}>
                Export Report
              </button>
            ) : null}
          </div>
        </header>

        {activeNav === 'dashboard' ? (
          <>
            <section className="stat-grid">
              {statCards.map((card, index) => (
                <div
                  key={card.label}
                  className="stat-card"
                  data-animate
                  style={{ '--delay': `${index * 0.08}s` }}
                >
                  <p className="muted">{card.label}</p>
                  <h3>{card.value}</h3>
                  <p className="stat-detail">{card.detail}</p>
                </div>
              ))}
            </section>

            <section className="main-grid">
              <div className="panel live-panel" data-animate>
                <div className="panel-header">
                  <div>
                    <h2>Live Feed</h2>
                    <p className="muted">
                      {selectedCamera?.name || 'No camera'} · {selectedCamera?.location || '-'}
                    </p>
                  </div>
                  <span className={streamStatus === 'active' || streamStatus === 'relay' ? 'status good' : 'status warn'}>
                    {streamStatus === 'active' && 'Streaming'}
                    {streamStatus === 'relay' && 'Relay Stream'}
                    {streamStatus === 'loading' && 'Connecting'}
                    {streamStatus === 'unsupported' && 'Unsupported'}
                    {streamStatus === 'error' && 'Blocked'}
                    {streamStatus === 'idle' && 'Waiting'}
                  </span>
                </div>

                <div className="live-view">
                  {liveIsRelay ? (
                    <img
                      src={liveSource}
                      alt="Relay stream"
                      className="live-relay"
                      onError={() => setStreamStatus('error')}
                    />
                  ) : null}

                  {streamStatus !== 'active' && !liveIsRelay ? (
                    <div className="live-placeholder">
                      <p className="strong">Live feed tidak tersedia untuk sumber ini.</p>
                      <p className="muted small">
                        Camera source: {liveSource || '-'}
                      </p>
                      <p className="muted small">
                        Browser hanya bisa tampilkan local webcam atau HTTP relay stream. RTSP dari edge client perlu relay service terlebih dahulu.
                      </p>
                    </div>
                  ) : null}

                  <div className="live-overlay">
                    <span className="live-dot" />
                    <span>Selected camera</span>
                  </div>
                </div>
              </div>

              <div className="panel" data-animate style={{ '--delay': '0.06s' }}>
                <div className="panel-header">
                  <div>
                    <h2>Recent Events</h2>
                    <p className="muted">Pelanggaran terbaru kamera terpilih.</p>
                  </div>
                  <button className="btn ghost" type="button" onClick={() => setActiveNav('events')}>
                    Open Events
                  </button>
                </div>

                <div className="violation-list">
                  {violations.length ? (
                    violations.slice(0, 5).map((violation) => {
                      const cameraName = cameraMap.get(String(violation.camera_id))?.name || 'Unknown'
                      const snapshotUrl = buildSnapshotUrl(violation.snapshot_path)
                      return (
                        <div key={violation.id} className="violation-item">
                          <div className="violation-thumb">
                            {snapshotUrl ? (
                              <img src={snapshotUrl} alt="Violation snapshot" />
                            ) : (
                              <div className="thumb-fallback">No Image</div>
                            )}
                          </div>
                          <div>
                            <p className="strong">{cameraName}</p>
                            <p className="muted small">{formatTimestamp(violation.timestamp)}</p>
                          </div>
                          <div>
                            <p className="strong">{formatMissingApd(violation.missing_apd)}</p>
                            <p className="muted small">
                              Confidence: {formatPercent(violation.confidence_score * 100)}
                            </p>
                          </div>
                          <span className={getViolationTone(violation.status)}>{violation.status}</span>
                        </div>
                      )
                    })
                  ) : (
                    <div className="empty-state">No violations recorded.</div>
                  )}
                </div>
              </div>
            </section>
          </>
        ) : null}

        {activeNav === 'live' ? (
          <section className="page-grid">
            <div className="panel" data-animate>
              <div className="panel-header">
                <div>
                  <h2>Live Monitoring</h2>
                  <p className="muted">Gunakan daftar kamera terdaftar untuk berpindah feed.</p>
                </div>
                <span className={getStatusTone(selectedCamera?.status || 'Inactive')}>
                  {selectedCamera?.status || 'Inactive'}
                </span>
              </div>

              <div className="live-view">
                {liveIsRelay ? (
                  <img
                    src={liveSource}
                    alt="Relay stream"
                    className="live-relay"
                    onError={() => setStreamStatus('error')}
                  />
                ) : null}

                {streamStatus !== 'active' && !liveIsRelay ? (
                  <div className="live-placeholder">
                    <p className="strong">Feed belum bisa ditampilkan.</p>
                    <p className="muted small">Sumber: {liveSource || '-'}</p>
                    <p className="muted small">
                      Jika edge client pakai RTSP, siapkan converter RTSP ke HTTP/MJPEG/WebRTC agar browser dashboard bisa menampilkan feed.
                    </p>
                  </div>
                ) : null}
              </div>
            </div>
          </section>
        ) : null}

        {activeNav === 'events' && canManageCameras ? (
          <section className="page-grid">
            <div className="panel" data-animate>
              <div className="panel-header">
                <div>
                  <h2>Event List</h2>
                  <p className="muted">Daftar event pelanggaran berdasarkan filter aktif.</p>
                </div>
              </div>

              <div className="filters">
                <label className="field">
                  Status
                  <select
                    value={eventStatusFilter}
                    onChange={(event) => setEventStatusFilter(event.target.value)}
                  >
                    <option value="">All status</option>
                    {VIOLATION_STATUS_OPTIONS.map((statusItem) => (
                      <option key={statusItem} value={statusItem}>
                        {statusItem}
                      </option>
                    ))}
                  </select>
                </label>
              </div>

              <div className="table">
                <div className="table-row head violations">
                  <span>Time</span>
                  <span>Camera</span>
                  <span>Missing APD</span>
                  <span>Confidence</span>
                  <span>Status</span>
                </div>

                {violationsLoading ? (
                  <div className="empty-state">Loading events...</div>
                ) : filteredViolations.length ? (
                  filteredViolations.map((violation) => {
                    const cameraName = cameraMap.get(String(violation.camera_id))?.name || 'Unknown'
                    const isUpdating = updatingViolationId === String(violation.id)
                    return (
                      <div key={violation.id} className="table-row violations">
                        <div>
                          <p className="strong">{formatTimestamp(violation.timestamp)}</p>
                          <p className="muted small">ID: {String(violation.id).slice(0, 8)}</p>
                        </div>
                        <span>{cameraName}</span>
                        <span>{formatMissingApd(violation.missing_apd)}</span>
                        <span>{formatPercent(violation.confidence_score * 100)}</span>
                        <div className="violation-status-cell">
                          <span className={getViolationTone(violation.status)}>{violation.status}</span>
                          {violation.status === 'Unverified' ? (
                            <div className="violation-actions">
                              <button
                                type="button"
                                className="btn ghost tiny"
                                disabled={isUpdating}
                                onClick={() => updateViolationStatus(violation.id, 'Verified')}
                              >
                                {isUpdating ? 'Saving...' : 'Verify'}
                              </button>
                              <button
                                type="button"
                                className="btn ghost tiny muted-action"
                                disabled={isUpdating}
                                onClick={() => updateViolationStatus(violation.id, 'False_Positive')}
                              >
                                False Positive
                              </button>
                            </div>
                          ) : null}
                        </div>
                      </div>
                    )
                  })
                ) : (
                  <div className="empty-state">No events found.</div>
                )}
              </div>
            </div>
          </section>
        ) : null}

        {activeNav === 'analytics_addons' && canManageCameras ? (
          <section className="analytics-addons-layout" data-animate>
            <div className="filter-breadcrumb-bar">
              <button className="breadcrumb-btn active" type="button">
                <Camera size={16} className="b-icon" />
                {selectedCamera?.name || 'No camera'}
                <span className="chevron">&gt;</span>
              </button>
              <button className="breadcrumb-btn" type="button">
                <Cloud size={16} className="b-icon" />
                Detection Stats
              </button>
            </div>

            <section className="stat-grid">
              <div className="stat-card">
                <p className="muted">Compliance Rate</p>
                <h3>{formatPercent(selectedCameraCompliance?.rate)}</h3>
                <p className="stat-detail">From detection stats records</p>
              </div>
              <div className="stat-card">
                <p className="muted">Detected Workers</p>
                <h3>{selectedCameraCompliance?.totalWorkers ?? 'No data'}</h3>
                <p className="stat-detail">Accumulated workers count</p>
              </div>
              <div className="stat-card">
                <p className="muted">Violation Events</p>
                <h3>{filteredViolations.length}</h3>
                <p className="stat-detail">Filtered by selected camera</p>
              </div>
              <div className="stat-card">
                <p className="muted">Unverified Events</p>
                <h3>{filteredViolations.filter((item) => item.status === 'Unverified').length}</h3>
                <p className="stat-detail">Need review by operator</p>
              </div>
            </section>

            {/* Visualisasi Data: Bar Chart & Pie/Donut Chart */}
            <div className="analytics-charts-grid" data-animate style={{ '--delay': '0.04s' }}>
              {/* Bar Chart: Tren Pelanggaran Harian */}
              <div className="chart-panel">
                <div className="panel-header">
                  <div>
                    <h2>Tren Pelanggaran Harian</h2>
                    <p className="muted">Jumlah kejadian pelanggaran terdeteksi 7 hari terakhir.</p>
                  </div>
                </div>
                <div className="bar-chart-wrapper">
                  {(() => {
                    const maxCount = Math.max(...dailyTrend.map(d => d.count), 5)
                    return (
                      <svg width="100%" height="220" viewBox="0 0 540 220" preserveAspectRatio="xMidYMid meet">
                        <defs>
                          <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="var(--accent-strong)" stopOpacity="1" />
                            <stop offset="100%" stopColor="var(--accent)" stopOpacity="0.25" />
                          </linearGradient>
                        </defs>
                        
                        {/* Horizontal Grid lines */}
                        {[0, 0.25, 0.5, 0.75, 1].map((ratio, index) => {
                          const yPos = 170 - ratio * 140
                          const gridVal = Math.round(ratio * maxCount)
                          return (
                            <g key={index}>
                              <line x1="40" y1={yPos} x2="520" y2={yPos} className="grid-line" />
                              <text x="15" y={yPos + 4} className="chart-text" textAnchor="middle">{gridVal}</text>
                            </g>
                          )
                        })}
                        
                        {/* Bars */}
                        {dailyTrend.map((d, index) => {
                          const barWidth = 40
                          const xPos = index * 66 + 55
                          const barHeight = (d.count / maxCount) * 140
                          const yPos = 170 - barHeight
                          return (
                            <g key={d.key}>
                              <rect
                                x={xPos}
                                y={yPos}
                                width={barWidth}
                                height={barHeight}
                                fill="url(#barGradient)"
                                rx="6"
                                ry="6"
                                className="bar-rect"
                              >
                                <title>{`${d.label}: ${d.count} Pelanggaran`}</title>
                              </rect>
                              {d.count > 0 && (
                                <text
                                  x={xPos + barWidth / 2}
                                  y={yPos - 6}
                                  className="chart-value-text"
                                  textAnchor="middle"
                                >
                                  {d.count}
                                </text>
                              )}
                              <text
                                x={xPos + barWidth / 2}
                                y="192"
                                className="chart-text"
                                textAnchor="middle"
                              >
                                {d.label}
                              </text>
                            </g>
                          )
                        })}
                        
                        {/* X-axis Line */}
                        <line x1="40" y1="170" x2="520" y2="170" className="axis-line" />
                      </svg>
                    )
                  })()}
                </div>
              </div>

              {/* Pie/Donut Chart: Distribusi Pelanggaran */}
              <div className="chart-panel">
                <div className="panel-header">
                  <div>
                    <h2>Distribusi APD</h2>
                    <p className="muted">Proporsi jenis APD yang sering dilanggar pekerja.</p>
                  </div>
                </div>
                <div className="pie-chart-wrapper">
                  {(() => {
                    const { helm, rompi, boot, total } = violationDistribution
                    const radius = 55
                    const circumference = 2 * Math.PI * radius
                    
                    const helmPct = total ? (helm / total) : 0
                    const rompiPct = total ? (rompi / total) : 0
                    const bootPct = total ? (boot / total) : 0
                    
                    const helmOffset = 0
                    const rompiOffset = helmPct * circumference
                    const bootOffset = (helmPct + rompiPct) * circumference
                    
                    const formatPercentageText = (count) => {
                      if (!total) return '0%'
                      return `${((count / total) * 100).toFixed(0)}%`
                    }
                    
                    return (
                      <div className="pie-chart-container">
                        <div className="pie-svg-container">
                          <svg width="140" height="140" viewBox="0 0 140 140">
                            {/* Background Circle */}
                            <circle cx="70" cy="70" r={radius} fill="transparent" stroke="rgba(31, 63, 70, 0.4)" strokeWidth="12" />
                            {total > 0 ? (
                              <>
                                {/* Helm Segment */}
                                <circle
                                  cx="70"
                                  cy="70"
                                  r={radius}
                                  fill="transparent"
                                  stroke="var(--accent)"
                                  strokeWidth="12"
                                  strokeDasharray={`${helmPct * circumference} ${circumference}`}
                                  strokeDashoffset={-helmOffset}
                                  transform="rotate(-90 70 70)"
                                />
                                {/* Rompi Segment */}
                                <circle
                                  cx="70"
                                  cy="70"
                                  r={radius}
                                  fill="transparent"
                                  stroke="var(--accent-warm)"
                                  strokeWidth="12"
                                  strokeDasharray={`${rompiPct * circumference} ${circumference}`}
                                  strokeDashoffset={-rompiOffset}
                                  transform="rotate(-90 70 70)"
                                />
                                {/* Boot Segment */}
                                <circle
                                  cx="70"
                                  cy="70"
                                  r={radius}
                                  fill="transparent"
                                  stroke="var(--danger)"
                                  strokeWidth="12"
                                  strokeDasharray={`${bootPct * circumference} ${circumference}`}
                                  strokeDashoffset={-bootOffset}
                                  transform="rotate(-90 70 70)"
                                />
                              </>
                            ) : null}
                          </svg>
                          <div style={{ position: 'absolute', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                            <span style={{ fontSize: '1.6rem', fontWeight: 'bold', fontFamily: 'var(--font-display)', color: 'var(--text)' }}>
                              {total}
                            </span>
                            <span style={{ fontSize: '0.62rem', color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                              Kasus
                            </span>
                          </div>
                        </div>
                        <div className="chart-legend">
                          <div className="legend-item">
                            <div className="legend-label-group">
                              <span className="legend-dot helm" />
                              <span>Helm</span>
                            </div>
                            <span className="legend-value">
                              {helm} <span className="legend-percent">({formatPercentageText(helm)})</span>
                            </span>
                          </div>
                          <div className="legend-item">
                            <div className="legend-label-group">
                              <span className="legend-dot rompi" />
                              <span>Rompi</span>
                            </div>
                            <span className="legend-value">
                              {rompi} <span className="legend-percent">({formatPercentageText(rompi)})</span>
                            </span>
                          </div>
                          <div className="legend-item">
                            <div className="legend-label-group">
                              <span className="legend-dot boot" />
                              <span>Sepatu</span>
                            </div>
                            <span className="legend-value">
                              {boot} <span className="legend-percent">({formatPercentageText(boot)})</span>
                            </span>
                          </div>
                        </div>
                      </div>
                    )
                  })()}
                </div>
              </div>
            </div>

            <div className="new-data-table">
              <div className="new-table-row head-row">
                <span>Time</span>
                <span>Total Workers</span>
                <span>Compliant</span>
                <span>Violating</span>
                <span>Compliance</span>
              </div>
              <div className="new-table-body">
                {detectionLoading ? (
                  <div className="empty-state">Loading detection analytics...</div>
                ) : detectionSeries.length ? (
                  detectionSeries.slice(0, 30).map((item) => {
                    const complianceRate = item.total_workers
                      ? (item.compliant_workers / item.total_workers) * 100
                      : 0
                    return (
                      <div key={item.id} className="new-table-row data-row">
                        <div className="time-col">
                          <span className="time-val">{formatTimestamp(item.timestamp)}</span>
                          <span className="date-val">Camera: {String(item.camera_id).slice(0, 8)}</span>
                        </div>
                        <span>{item.total_workers}</span>
                        <span>{item.compliant_workers}</span>
                        <span>{item.violating_workers}</span>
                        <span>{formatPercent(complianceRate)}</span>
                      </div>
                    )
                  })
                ) : (
                  <div className="empty-state">No detection stats found for this camera.</div>
                )}
              </div>
            </div>

            <div className="panel">
              <div className="panel-header">
                <div>
                  <h2>Related Events</h2>
                  <p className="muted">Event list yang sinkron dengan kamera analytics saat ini.</p>
                </div>
              </div>
              <div className="violation-list">
                {filteredViolations.slice(0, 8).map((violation) => {
                  const snapshotUrl = buildSnapshotUrl(violation.snapshot_path)
                  return (
                    <div key={violation.id} className="violation-item">
                      <div
                        className="violation-thumb"
                        role="button"
                        tabIndex={0}
                        onClick={() => setInspectionModal(violation)}
                        onKeyDown={(event) => {
                          if (event.key === 'Enter' || event.key === ' ') {
                            setInspectionModal(violation)
                          }
                        }}
                      >
                        {snapshotUrl ? (
                          <img src={snapshotUrl} alt="Violation snapshot" />
                        ) : (
                          <div className="thumb-fallback">No Image</div>
                        )}
                      </div>
                      <div>
                        <p className="strong">{formatTimestamp(violation.timestamp)}</p>
                        <p className="muted small">{formatMissingApd(violation.missing_apd)}</p>
                      </div>
                      <div>
                        <p className="strong">Confidence</p>
                        <p className="muted small">{formatPercent(violation.confidence_score * 100)}</p>
                      </div>
                      <span className={getViolationTone(violation.status)}>{violation.status}</span>
                    </div>
                  )
                })}
                {!filteredViolations.length ? (
                  <div className="empty-state">No related events.</div>
                ) : null}
              </div>
            </div>
          </section>
        ) : null}

        {activeNav === 'cameras' && canManageCameras ? (
          <section className="page-grid">
            <div className="panel" data-animate>
              <div className="panel-header">
                <div>
                  <h2>Camera Inventory</h2>
                  <p className="muted">Daftar kamera dari backend API.</p>
                </div>
                <div className="panel-actions">
                  <button className="btn ghost" type="button" onClick={loadOverview}>
                    Refresh
                  </button>
                  <button
                    className="btn primary"
                    type="button"
                    onClick={() => openCameraForm()}
                  >
                    Add Camera
                  </button>
                </div>
              </div>

              <div className="table">
                <div className="table-row head cameras">
                  <span>Camera</span>
                  <span>Location</span>
                  <span>Status</span>
                  <span>Source</span>
                  <span>Actions</span>
                </div>
                {cameraList.length ? (
                  cameraList.map((camera) => (
                    <div key={camera.id} className="table-row cameras">
                      <div>
                        <p className="strong">{camera.name}</p>
                        <p className="muted small">ID: {String(camera.id).slice(0, 8)}</p>
                      </div>
                      <span>{camera.location}</span>
                      <span className={getStatusTone(camera.status)}>{camera.status}</span>
                      <span className="source-pill">{camera.rtsp_url || '-'}</span>
                      <div className="camera-actions">
                        <button className="btn ghost tiny" type="button" onClick={() => openCameraForm(camera)}>
                          Edit
                        </button>
                        <button
                          className="btn ghost tiny muted-action"
                          type="button"
                          onClick={() => handleDeleteCamera(camera.id)}
                          disabled={isDeletingCameraId === String(camera.id)}
                        >
                          {isDeletingCameraId === String(camera.id) ? 'Deleting...' : 'Delete'}
                        </button>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="table-row empty">
                    <span>No camera data yet.</span>
                  </div>
                )}
              </div>
            </div>
          </section>
        ) : null}

        {activeNav === 'settings' ? (
          <section className="page-grid">
            <div className="panel" data-animate>
              <div className="panel-header">
                <div>
                  <h2>User Profile</h2>
                  <p className="muted">Informasi akun yang sedang aktif.</p>
                </div>
              </div>
              <div className="info-grid">
                <div className="info-card">
                  <p className="muted small">Full Name</p>
                  <p className="strong">{user?.full_name || '-'}</p>
                </div>
                <div className="info-card">
                  <p className="muted small">Username</p>
                  <p className="strong">{user?.username}</p>
                </div>
                <div className="info-card">
                  <p className="muted small">Role</p>
                  <p className="strong">{user?.role || 'Operator'}</p>
                </div>
                <div className="info-card">
                  <p className="muted small">Email</p>
                  <p className="strong">{user?.email || '-'}</p>
                </div>
              </div>
            </div>

            <div className="panel" data-animate style={{ '--delay': '0.08s' }}>
              <div className="panel-header">
                <div>
                  <h2>System Endpoints</h2>
                  <p className="muted">Status koneksi utama platform.</p>
                </div>
              </div>
              <div className="info-grid">
                <div className="info-card">
                  <p className="muted small">Backend API</p>
                  <p className="strong">{API_BASE_URL}</p>
                </div>
                <div className="info-card">
                  <p className="muted small">API Health</p>
                  <p className="strong">{apiHealth === 'online' ? 'Connected' : 'Offline'}</p>
                </div>
                <div className="info-card">
                  <p className="muted small">Current Camera</p>
                  <p className="strong">{selectedCamera?.name || '-'}</p>
                </div>
              </div>
            </div>
          </section>
        ) : null}

        {showCameraForm ? (
          <div className="modal-backdrop">
            <div className="modal-card">
              <div className="modal-header">
                <div>
                  <p className="eyebrow">{cameraFormMode === 'edit' ? 'Edit Camera' : 'Add Camera'}</p>
                  <h2 className="modal-title">
                    {cameraFormMode === 'edit' ? 'Update Camera Details' : 'Register New Camera'}
                  </h2>
                </div>
                <button className="btn ghost" type="button" onClick={closeCameraForm}>
                  Close
                </button>
              </div>

              <form className="modal-body" onSubmit={handleSaveCamera}>
                <div className="form-grid">
                  <label className="field">
                    Camera Name
                    <input
                      type="text"
                      value={cameraForm.name}
                      onChange={(event) => setCameraForm((prev) => ({ ...prev, name: event.target.value }))}
                      placeholder="Lokasi Produksi A"
                      required
                    />
                  </label>
                  <label className="field">
                    Location
                    <input
                      type="text"
                      value={cameraForm.location}
                      onChange={(event) => setCameraForm((prev) => ({ ...prev, location: event.target.value }))}
                      placeholder="Lantai 1 - Area Produksi"
                      required
                    />
                  </label>
                  <label className="field">
                    RTSP / Source
                    <input
                      type="text"
                      value={cameraForm.rtsp_url}
                      onChange={(event) => setCameraForm((prev) => ({ ...prev, rtsp_url: event.target.value }))}
                      placeholder="local://webcam or https://stream-url"
                      required
                    />
                  </label>
                  <label className="field">
                    Status
                    <select
                      value={cameraForm.status}
                      onChange={(event) => setCameraForm((prev) => ({ ...prev, status: event.target.value }))}
                    >
                      {CAMERA_STATUS_OPTIONS.map((option) => (
                        <option key={option} value={option}>
                          {option}
                        </option>
                      ))}
                    </select>
                  </label>
                </div>

                {cameraFormError ? <div className="notice error">{cameraFormError}</div> : null}

                <div className="modal-footer">
                  <button className="btn ghost" type="button" onClick={closeCameraForm}>
                    Cancel
                  </button>
                  <button className="btn primary" type="submit" disabled={isSavingCamera}>
                    {isSavingCamera ? 'Saving...' : cameraFormMode === 'edit' ? 'Update Camera' : 'Save Camera'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        ) : null}

        {reportOpen ? (
          <div className="modal-backdrop">
            <div className="modal-card">
              <div className="modal-header">
                <div>
                  <p className="eyebrow">Export Report</p>
                  <h2 className="modal-title">Generate Violation Report</h2>
                </div>
                <button className="btn ghost" type="button" onClick={() => setReportOpen(false)}>
                  Close
                </button>
              </div>

              <form className="modal-body" onSubmit={handleReportExport}>
                <div className="form-grid">
                  <label className="field">
                    Camera
                    <select
                      value={reportFilters.camera_id}
                      onChange={(event) =>
                        setReportFilters((prev) => ({
                          ...prev,
                          camera_id: event.target.value,
                        }))
                      }
                    >
                      <option value="">All cameras</option>
                      {cameraList.map((camera) => (
                        <option key={camera.id} value={camera.id}>
                          {camera.name}
                        </option>
                      ))}
                    </select>
                  </label>

                  <label className="field">
                    Status
                    <select
                      value={reportFilters.status_filter}
                      onChange={(event) =>
                        setReportFilters((prev) => ({
                          ...prev,
                          status_filter: event.target.value,
                        }))
                      }
                    >
                      <option value="">All status</option>
                      {VIOLATION_STATUS_OPTIONS.map((option) => (
                        <option key={option} value={option}>
                          {option}
                        </option>
                      ))}
                    </select>
                  </label>

                  <label className="field">
                    Start Date
                    <input
                      type="date"
                      value={reportFilters.start_date}
                      onChange={(event) =>
                        setReportFilters((prev) => ({ ...prev, start_date: event.target.value }))
                      }
                    />
                  </label>

                  <label className="field">
                    End Date
                    <input
                      type="date"
                      value={reportFilters.end_date}
                      onChange={(event) =>
                        setReportFilters((prev) => ({ ...prev, end_date: event.target.value }))
                      }
                    />
                  </label>
                </div>

                {reportStatus ? <div className={`notice ${reportStatus.type}`}>{reportStatus.message}</div> : null}

                <div className="modal-footer">
                  <button className="btn ghost" type="button" onClick={() => setReportOpen(false)}>
                    Cancel
                  </button>
                  <button className="btn primary" type="submit" disabled={isExporting}>
                    {isExporting ? 'Exporting...' : 'Download Report'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        ) : null}

        {inspectionModal ? (
          <div className="modal-backdrop">
            <div className="inspection-modal-card" data-animate>
              <div className="inspection-header">
                <h3>{formatTimestamp(inspectionModal.timestamp)}</h3>
                <button type="button" className="btn-close" onClick={() => setInspectionModal(null)}>
                  <X size={18} />
                </button>
              </div>
              <div className="inspection-body">
                <div className="main-image">
                  {buildSnapshotUrl(inspectionModal.snapshot_path) ? (
                    <img src={buildSnapshotUrl(inspectionModal.snapshot_path)} alt="Incident" />
                  ) : (
                    <div className="placeholder">
                      <ImageIcon size={48} className="muted" />
                    </div>
                  )}
                </div>
                <div className="inspection-footer">
                  <div className="footer-thumbs">
                    <div className="thumb-item active">
                      <ImageIcon size={16} />
                    </div>
                  </div>
                  <div className="footer-actions">
                    <button type="button">
                      <Camera size={18} />
                    </button>
                    <button type="button">
                      <Info size={18} />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        ) : null}
      </main>
    </div>
  )
}

export default App
