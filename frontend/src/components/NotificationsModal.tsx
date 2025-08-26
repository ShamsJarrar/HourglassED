import { useEffect, useState} from 'react'
import { getNotifications, markNotificationAsRead } from '../lib/notifications'
import type { Notification } from '../types/api'
import { useToast } from './Toast'

interface Props {
  open: boolean
  onClose: () => void
  onRefresh?: () => void
  onNotificationRead?: () => void
}

export default function NotificationsModal({ open, onClose, onRefresh, onNotificationRead }: Props) {
  const { show } = useToast()
  const [notifications, setNotifications] = useState<Notification[] | null>(null)
  const [markAsReadLoading, setMarkAsReadLoading] = useState<Record<number, boolean>>({})

  useEffect(() => {
    if (!open) return
    
    loadNotifications()
  }, [open])

  const loadNotifications = async () => {
    setNotifications(null)
    try {
      const notificationsList = await getNotifications()
      // Sort by most recent first
      const sortedNotifications = notificationsList.sort((a, b) => 
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      )
      setNotifications(sortedNotifications)
    } catch (e) {
      console.error('Failed to load notifications', e)
      show('Failed to load notifications', 'error')
      setNotifications([])
    }
  }

  const handleClose = () => {
    onClose()
    if (onRefresh) {
      onRefresh()
    }
  }

  const formatTimeAgo = (dateString: string) => {
    const now = new Date()
    const date = new Date(dateString)
    const diffInMs = now.getTime() - date.getTime()
    const diffInMinutes = Math.floor(diffInMs / (1000 * 60))
    const diffInHours = Math.floor(diffInMs / (1000 * 60 * 60))
    const diffInDays = Math.floor(diffInMs / (1000 * 60 * 60 * 24))

    if (diffInMinutes < 1) return 'Just now'
    if (diffInMinutes < 60) return `${diffInMinutes} min ago`
    if (diffInHours < 24) return `${diffInHours} hour${diffInHours > 1 ? 's' : ''} ago`
    if (diffInDays < 7) return `${diffInDays} day${diffInDays > 1 ? 's' : ''} ago`
    return date.toLocaleDateString()
  }

  const handleMarkAsRead = async (notificationId: number) => {
    setMarkAsReadLoading(prev => ({ ...prev, [notificationId]: true }))
    try {
      await markNotificationAsRead(notificationId)
      
      // Update the local state to mark as read
      setNotifications(prev => 
        prev?.map(notification => 
          notification.notification_id === notificationId 
            ? { ...notification, is_read: true }
            : notification
        ) ?? []
      )
      
      show('Notification marked as read', 'info')
      
      // Notify parent component that a notification was read
      if (onNotificationRead) {
        onNotificationRead()
      }
    } catch (e) {
      console.error('Failed to mark notification as read', e)
      show('Failed to mark notification as read', 'error')
    } finally {
      setMarkAsReadLoading(prev => ({ ...prev, [notificationId]: false }))
    }
  }

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/30" onClick={handleClose}>
      <div className="w-[520px] max-w-[92vw] max-h-[86vh] rounded-xl bg-[#FFF8EB] border-2 border-[#633D00] shadow-2xl" onClick={(e) => e.stopPropagation()}>
        <div className="p-5 flex flex-col" style={{ maxHeight: '86vh' }}>
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-xl font-semibold text-[#633D00]">Notifications</h2>
            <button onClick={handleClose} className="text-[#633D00] border border-[#633D00] rounded-md px-2 py-0.5">Close</button>
          </div>

          <div className="flex-1 overflow-y-auto no-scrollbar">
            {notifications === null ? (
              <div className="text-center py-8">
                <div className="text-[#633D00]/70">Loading notifications...</div>
              </div>
            ) : notifications.length === 0 ? (
              <div className="text-center py-8">
                <div className="text-[#633D00]/70">No notifications</div>
              </div>
            ) : (
              <div className="space-y-3">
                {notifications.map((notification) => (
                  <div 
                    key={notification.notification_id} 
                    className={`rounded-md border p-4 relative ${
                      notification.is_read 
                        ? 'border-[#633D00]/20 bg-[#FFF8EB]/50' 
                        : 'border-[#633D00]/30 bg-white'
                    }`}
                  >
                    {/* Time ago indicator in top right */}
                    <div className="absolute top-2 right-2 text-xs text-[#633D00]/60">
                      {formatTimeAgo(notification.created_at)}
                    </div>
                    
                    {/* Read status indicator */}
                    {!notification.is_read && (
                      <div className="absolute top-2 left-2 w-3 h-3 bg-blue-500 rounded-full"></div>
                    )}
                    
                    <div className={`mt-2 mb-2 ${!notification.is_read ? 'pl-6' : ''}`}>
                      <p className={`text-[#633D00] ${notification.is_read ? 'opacity-70' : ''}`}>
                        {notification.message}
                      </p>
                      {notification.type && (
                        <p className="text-[#633D00]/60 text-sm mt-1">
                          Type: {notification.type}
                        </p>
                      )}
                    </div>

                    {!notification.is_read && (
                      <div className="flex justify-end">
                        <button
                          onClick={() => handleMarkAsRead(notification.notification_id)}
                          disabled={markAsReadLoading[notification.notification_id]}
                          className="px-3 py-1.5 bg-[#633D00] text-white text-sm rounded-md hover:bg-[#633D00]/90 disabled:opacity-60 disabled:cursor-not-allowed"
                        >
                          {markAsReadLoading[notification.notification_id] ? 'Marking...' : 'Mark as Read'}
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
