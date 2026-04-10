# Notifications Module - Documentation

## Overview

Modul ini menangani notifikasi web untuk dashboard users. Setiap pelanggaran (violation) yang terdeteksi atau terverifikasi akan generate notifikasi untuk user yang relevan. Users dapat melihat list notifikasi, menandai satu per satu sebagai dibaca, atau sekaligus "tandai semua telah dibaca".

## Features

### Notification Management
- ✅ Real-time notification generation saat ada violation
- ✅ List notifications dengan pagination
- ✅ Mark single notification sebagai read
- ✅ Mark all notifications sebagai read (bulk action)
- ✅ Notifications ordered by most recent first
- ✅ Unread count tracking

### Dashboard Integration
- ✅ Quick access untuk users yang login
- ✅ Efficient pagination untuk large notification sets
- ✅ Bulk operations untuk UX yang better

---

## Endpoints

### Notifications Routes (`/api/notifications`)

#### 1. **GET /api/notifications**
Mengambil list notifikasi milik user yang login

**Akses:** Semua role (authenticated users only)

**Headers:**
```
Authorization: Bearer {access_token}
```

**Query Parameters (all optional):**
| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `limit` | Integer | Max records (1-500) | 50 |
| `offset` | Integer | Pagination offset | 0 |

**Example Request:**
```
GET /api/notifications?limit=20&offset=0
```

**Response (200):**
```json
[
  {
    "id": "aa0e8400-e29b-41d4-a716-446655440300",
    "violation_id": "990e8400-e29b-41d4-a716-446655440200",
    "message": "🚨 PELANGGARAN APD TERDETEKSI - Kamera: Lokasi Produksi A - APD Hilang: HELMET, VEST - Confidence: 92.0%",
    "is_read": false,
    "sent_at": "2026-04-10T14:30:00"
  },
  {
    "id": "bb0e8400-e29b-41d4-a716-446655440301",
    "violation_id": "aa0e8400-e29b-41d4-a716-446655440201",
    "message": "✅ PELANGGARAN TERVERIFIKASI - Kamera: Lokasi Produksi A - Diverifikasi oleh: admin",
    "is_read": true,
    "sent_at": "2026-04-10T14:15:00"
  }
]
```

**Response (200 - Empty):**
```json
[]
```

---

#### 2. **PUT /api/notifications/{id}/read**
Mengubah is_read menjadi TRUE pada satu notifikasi

**Akses:** Semua role (authenticated users only)

**Headers:**
```
Authorization: Bearer {access_token}
```

**URL Parameter:**
```
id = aa0e8400-e29b-41d4-a716-446655440300 (UUID notifikasi)
```

**Request Body:**
```json
{}
```

(Body kosong, hanya perlu URL parameter)

**Response (200):**
```json
{
  "id": "aa0e8400-e29b-41d4-a716-446655440300",
  "violation_id": "990e8400-e29b-41d4-a716-446655440200",
  "message": "🚨 PELANGGARAN APD TERDETEKSI - Kamera: Lokasi Produksi A - APD Hilang: HELMET, VEST - Confidence: 92.0%",
  "is_read": true,
  "sent_at": "2026-04-10T14:30:00"
}
```

**Error (404) - Notification tidak ditemukan:**
```json
{
  "detail": "Notification not found"
}
```

---

#### 3. **PUT /api/notifications/read-all**
Tandai semua notifikasi user sebagai telah dibaca

**Akses:** Semua role (authenticated users only)

**Features:**
- ✅ Bulk operation untuk UX yang lebih baik
- ✅ Hanya mark notifikasi yang is_read=FALSE
- ✅ Return count notifikasi yang di-update
- ✅ User favorit banget fitur ini!

**Headers:**
```
Authorization: Bearer {access_token}
```

**Request Body:**
```json
{}
```

(Body kosong)

**Response (200):**
```json
{
  "message": "All notifications marked as read",
  "count": 5
}
```

Penjelasan:
- `count`: Berapa banyak notifikasi yang di-update dari unread menjadi read
- Jika `count: 0`, bearti semua sudah dibaca atau tidak ada notifikasi

**Example Responses:**
```json
{
  "message": "All notifications marked as read",
  "count": 0
}
```
(Semua sudah dibaca)

---

## Data Models

### Notification Table

| Field | Type | Required | Deskripsi |
|-------|------|----------|-----------|
| `id` | UUID | Auto | Unique identifier |
| `violation_id` | UUID | ✅ | Foreign key to Violation |
| `user_id` | UUID | ✅ | Foreign key to User |
| `message` | String | ✅ | Notification message |
| `is_read` | Boolean | ✅ | Read status, default FALSE |
| `sent_at` | DateTime | Auto | Timestamp saat notifikasi dikirim |

---

## Notification Message Format

### Format Pelanggaran Baru
```
🚨 PELANGGARAN APD TERDETEKSI
📹 Kamera: {camera_name}
🕐 Waktu: {timestamp}
⚠️ APD Hilang: {missing_apd_list}
📊 Confidence Score: {score}%
```

### Format Verifikasi
```
✅ PELANGGARAN TERVERIFIKASI
📹 Kamera: {camera_name}
👤 Diverifikasi oleh: {verifier_name}
```

atau

```
⛔ BUKAN PELANGGARAN
📹 Kamera: {camera_name}
👤 Diverifikasi oleh: {verifier_name}
```

---

## Frontend Integration Example

### React Component - Notifications List
```jsx
import { useState, useEffect } from 'react';

function NotificationsList() {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  
  const fetchNotifications = async () => {
    setLoading(true);
    const response = await fetch('/api/notifications?limit=50', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    });
    const data = await response.json();
    setNotifications(data);
    setUnreadCount(data.filter(n => !n.is_read).length);
    setLoading(false);
  };
  
  useEffect(() => {
    fetchNotifications();
    // Poll every 10 seconds for new notifications
    const interval = setInterval(fetchNotifications, 10000);
    return () => clearInterval(interval);
  }, []);
  
  const markAsRead = async (notificationId) => {
    await fetch(`/api/notifications/${notificationId}/read`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    });
    fetchNotifications();
  };
  
  const markAllAsRead = async () => {
    await fetch('/api/notifications/read-all', {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    });
    fetchNotifications();
  };
  
  return (
    <div className="notifications-panel">
      <div className="notifications-header">
        <h2>Notifikasi ({unreadCount})</h2>
        {unreadCount > 0 && (
          <button onClick={markAllAsRead} className="btn-mark-all">
            Tandai Semua Telah Dibaca
          </button>
        )}
      </div>
      
      {notifications.map(notif => (
        <div 
          key={notif.id} 
          className={`notification-item ${notif.is_read ? 'read' : 'unread'}`}
        >
          <div className="notif-content">
            <p>{notif.message}</p>
            <small>{new Date(notif.sent_at).toLocaleString()}</small>
          </div>
          
          {!notif.is_read && (
            <button 
              onClick={() => markAsRead(notif.id)}
              className="btn-mark-read"
            >
              ✓ Tandai Dibaca
            </button>
          )}
        </div>
      ))}
      
      {notifications.length === 0 && (
        <p className="empty-state">Tidak ada notifikasi</p>
      )}
    </div>
  );
}

export default NotificationsList;
```

### React Component - Unread Badge
```jsx
function NotificationBadge() {
  const [unreadCount, setUnreadCount] = useState(0);
  
  useEffect(() => {
    const fetchUnreadCount = async () => {
      const response = await fetch('/api/notifications?limit=1000', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });
      const data = await response.json();
      setUnreadCount(data.filter(n => !n.is_read).length);
    };
    
    fetchUnreadCount();
    const interval = setInterval(fetchUnreadCount, 5000);
    return () => clearInterval(interval);
  }, []);
  
  return (
    <div className="notification-badge">
      🔔
      {unreadCount > 0 && (
        <span className="badge-count">{unreadCount}</span>
      )}
    </div>
  );
}
```

---

## API Usage Examples

### cURL Examples

**Get Notifications:**
```bash
curl -X GET http://localhost:8000/api/notifications?limit=20 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Mark Single Notification as Read:**
```bash
curl -X PUT http://localhost:8000/api/notifications/aa0e8400-e29b-41d4-a716-446655440300/read \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Mark All Notifications as Read:**
```bash
curl -X PUT http://localhost:8000/api/notifications/read-all \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Performance & Best Practices

1. **Pagination**
   - Default limit 50, max 500
   - Always use offset/limit untuk large result sets
   - Frontend bisa implement lazy-loading/infinite scroll

2. **Polling Strategy**
   - Frontend poll setiap 10-30 seconds untuk new notifications
   - Consider WebSocket implementation di future untuk real-time
   - Efficient untuk MVP dahulu

3. **Unread Count**
   - Frontend calculate dari fetched data: `data.filter(n => !n.is_read).length`
   - atau calculate per-endpoint call
   - Show badge di notification icon

4. **Database Indexes**
   - `notification.user_id` sudah ada index
   - Query optimized untuk filtering by user

---

## Troubleshooting

### Notifications Tidak Muncul
1. Check apakah violation sudah di-create
2. Verify notification di-trigger saat violation creation/verification
3. Check database: `SELECT * FROM notification WHERE user_id = 'xxx'`

### Mark All Not Working
1. Ensure user authenticated dengan valid token
2. Check user_id di database
3. Verify `is_read` status di database sebelum/sesudah operation

### Pagination Issues
1. Ensure limit + offset valid
2. Check total count dari violations
3. Implement client-side pagination logic

---

## File Structure

```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       └── notifications.py        # 3 notification endpoints
│   ├── models/
│   │   └── notification.py             # Notification model (existing)
│   └── schemas/
│       └── notifications.py            # NEW - Notification schemas
├── main.py                             # Updated with notifications router
└── NOTIFICATIONS_GUIDE.md              # This file
```

---

## Next Steps (Future Enhancements)

- [ ] WebSocket real-time notifications
- [ ] Notification preferences/filters
- [ ] Notification deletion
- [ ] Notification categories (violations, verifications, system)
- [ ] Push notifications ke mobile app
- [ ] Email notifications untuk critical violations
- [ ] Notification archive/history
- [ ] Bulk delete operations

---

## Summary

**Modul E - Notifications** telah complete dengan:
- ✅ List notifications dengan pagination
- ✅ Mark single notification as read
- ✅ Mark all notifications as read (bulk action)
- ✅ CORS support untuk frontend access
- ✅ Full integration dengan violation system
- ✅ Ready untuk dashboard implementation

Total endpoints: **3 notification endpoints**

Backend status: **COMPLETE - Semua 5 modules (A-E) sudah implemented!**
