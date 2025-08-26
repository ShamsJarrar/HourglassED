import { useEffect, useState } from 'react'
import { 
  getFriendsList, 
  sendFriendRequest, 
  getSentFriendRequests, 
  getReceivedFriendRequests,
  acceptFriendRequest,
  rejectFriendRequest,
  unsendFriendRequest,
  unfriendUser
} from '../lib/friends'
import type { 
  FriendsListResponseItem,
  SentFriendRequest,
  ReceivedFriendRequest
} from '../types/api'
import { useToast } from './Toast'

interface Props {
  open: boolean
  onClose: () => void
  onRefresh?: () => void
}

type TabType = 'friends' | 'send' | 'received'

export default function FriendsModal({ open, onClose, onRefresh }: Props) {
  const { show } = useToast()
  const [activeTab, setActiveTab] = useState<TabType>('friends')
  
  // Friends tab state
  const [friends, setFriends] = useState<FriendsListResponseItem[] | null>(null)
  const [unfriendLoading, setUnfriendLoading] = useState<Record<number, boolean>>({})
  const [unfriendDropdownOpen, setUnfriendDropdownOpen] = useState<number | null>(null)
  
  // Send tab state
  const [emailInput, setEmailInput] = useState('')
  const [sentRequests, setSentRequests] = useState<SentFriendRequest[] | null>(null)
  const [unsendLoading, setUnsendLoading] = useState<Record<number, boolean>>({})
  const [unsendDropdownOpen, setUnsendDropdownOpen] = useState<number | null>(null)
  const [sendLoading, setSendLoading] = useState(false)
  
  // Received tab state
  const [receivedRequests, setReceivedRequests] = useState<ReceivedFriendRequest[] | null>(null)
  const [respondLoading, setRespondLoading] = useState<Record<number, boolean>>({})

  useEffect(() => {
    if (!open) return
    
    loadTabData()
  }, [open, activeTab])

  // Close dropdowns when clicking outside
  useEffect(() => {
    const handleClickOutside = () => {
      setUnfriendDropdownOpen(null)
      setUnsendDropdownOpen(null)
    }

    if (open) {
      document.addEventListener('click', handleClickOutside)
      return () => document.removeEventListener('click', handleClickOutside)
    }
  }, [open])

  const loadTabData = async () => {
    switch (activeTab) {
      case 'friends':
        await loadFriends()
        break
      case 'send':
        await loadSentRequests()
        break
      case 'received':
        await loadReceivedRequests()
        break
    }
  }

  const loadFriends = async () => {
    setFriends(null)
    try {
      const friendsList = await getFriendsList()
      setFriends(friendsList)
    } catch (e) {
      console.error('Failed to load friends', e)
      show('Failed to load friends', 'error')
      setFriends([])
    }
  }

  const loadSentRequests = async () => {
    setSentRequests(null)
    try {
      const requests = await getSentFriendRequests()
      setSentRequests(requests)
    } catch (e) {
      console.error('Failed to load sent requests', e)
      show('Failed to load sent requests', 'error')
      setSentRequests([])
    }
  }

  const loadReceivedRequests = async () => {
    setReceivedRequests(null)
    try {
      const requests = await getReceivedFriendRequests()
      setReceivedRequests(requests)
    } catch (e) {
      console.error('Failed to load received requests', e)
      show('Failed to load received requests', 'error')
      setReceivedRequests([])
    }
  }

  const handleClose = () => {
    onClose()
    setUnfriendDropdownOpen(null)
    setUnsendDropdownOpen(null)
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

  const validateEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return emailRegex.test(email)
  }

  const handleSendRequest = async () => {
    if (!emailInput.trim()) {
      show('Please enter an email address', 'error')
      return
    }
    
    if (!validateEmail(emailInput.trim())) {
      show('Please enter a valid email address', 'error')
      return
    }

    setSendLoading(true)
    try {
      await sendFriendRequest({ receiver_email: emailInput.trim() })
      setEmailInput('')
      show('Friend request sent!', 'info')
      await loadSentRequests() // Refresh the sent requests list
    } catch (e: any) {
      console.error('Failed to send friend request', e)
      const status = e?.response?.status
      if (status === 400) {
        show('Already friends/Already sent a request', 'error')
      } else if (status == 404) {
        show('User does not exist', 'error')
      } else {
        show('Failed to send friend request', 'error')
      }
    } finally {
      setSendLoading(false)
    }
  }

  const handleUnfriend = async (friendId: number) => {
    setUnfriendLoading(prev => ({ ...prev, [friendId]: true }))
    try {
      await unfriendUser(friendId)
      setFriends(prev => prev?.filter(friend => friend.friend_id !== friendId) ?? [])
      show('Friend removed', 'info')
    } catch (e) {
      console.error('Failed to remove friend', e)
      show('Failed to remove friend', 'error')
    } finally {
      setUnfriendLoading(prev => ({ ...prev, [friendId]: false }))
    }
  }

  const handleUnsendRequest = async (requestId: number) => {
    setUnsendLoading(prev => ({ ...prev, [requestId]: true }))
    try {
      await unsendFriendRequest(requestId)
      setSentRequests(prev => prev?.filter(req => req.request_id !== requestId) ?? [])
      show('Request unsent', 'info')
    } catch (e) {
      console.error('Failed to unsend request', e)
      show('Failed to unsend request', 'error')
    } finally {
      setUnsendLoading(prev => ({ ...prev, [requestId]: false }))
    }
  }

  const handleRespondToRequest = async (requestId: number, response: 'accept' | 'reject') => {
    setRespondLoading(prev => ({ ...prev, [requestId]: true }))
    try {
      if (response === 'accept') {
        await acceptFriendRequest(requestId)
        show('Friend request accepted!', 'info')
      } else {
        await rejectFriendRequest(requestId)
        show('Friend request rejected', 'info')
      }
      setReceivedRequests(prev => prev?.filter(req => req.request_id !== requestId) ?? [])
    } catch (e) {
      console.error(`Failed to ${response} friend request`, e)
      show(`Failed to ${response} friend request`, 'error')
    } finally {
      setRespondLoading(prev => ({ ...prev, [requestId]: false }))
    }
  }

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/30" onClick={handleClose}>
      <div className="w-[520px] max-w-[92vw] max-h-[86vh] rounded-xl bg-[#FFF8EB] border-2 border-[#633D00] shadow-2xl" onClick={(e) => e.stopPropagation()}>
        <div className="p-5 flex flex-col" style={{ maxHeight: '86vh' }}>
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-xl font-semibold text-[#633D00]">Friends</h2>
            <button onClick={handleClose} className="text-[#633D00] border border-[#633D00] rounded-md px-2 py-0.5">Close</button>
          </div>

          {/* Tabs */}
          <div className="flex border-b border-[#633D00]/30 mb-4">
            {[
              { id: 'friends', label: 'My Friends' },
              { id: 'send', label: 'Send' },
              { id: 'received', label: 'Received' }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as TabType)}
                className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === tab.id
                    ? 'border-[#633D00] text-[#633D00]'
                    : 'border-transparent text-[#633D00]/60 hover:text-[#633D00]'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <div className="flex-1 overflow-y-auto no-scrollbar">
            {/* My Friends Tab */}
            {activeTab === 'friends' && (
              <div>
                {friends === null ? (
                  <div className="text-center py-8">
                    <div className="text-[#633D00]/70">Loading friends...</div>
                  </div>
                ) : friends.length === 0 ? (
                  <div className="text-center py-8">
                    <div className="text-[#633D00]/70">No friends yet</div>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {friends.map((friend) => (
                      <div key={friend.friend_id} className="rounded-md border border-[#633D00]/30 bg-white p-4 relative">
                        <div className="flex items-center justify-between">
                          <div>
                            <h3 className="font-semibold text-[#633D00]">{friend.friend_name}</h3>
                            <p className="text-[#633D00]/70 text-sm">{friend.friend_email}</p>
                          </div>
                          <div className="relative">
                            <button 
                              className="text-[#633D00]/60 hover:text-[#633D00] p-1"
                              onClick={(e) => {
                                e.stopPropagation()
                                setUnfriendDropdownOpen(unfriendDropdownOpen === friend.friend_id ? null : friend.friend_id)
                              }}
                            >
                              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                                <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z" />
                              </svg>
                            </button>
                                                         {unfriendDropdownOpen === friend.friend_id && (
                               <div className="absolute right-0 top-full mt-1 bg-white border border-[#633D00]/30 rounded-md shadow-lg z-10" onClick={(e) => e.stopPropagation()}>
                                <button
                                  onClick={() => {
                                    handleUnfriend(friend.friend_id)
                                    setUnfriendDropdownOpen(null)
                                  }}
                                  disabled={unfriendLoading[friend.friend_id]}
                                  className="block w-full text-left px-3 py-2 text-sm text-red-600 hover:bg-red-50 disabled:opacity-60"
                                >
                                  {unfriendLoading[friend.friend_id] ? 'Removing...' : 'Unfriend'}
                                </button>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Send Tab */}
            {activeTab === 'send' && (
              <div className="space-y-4">
                {/* Send Request Form */}
                <div className="rounded-md border border-[#633D00]/30 bg-white p-4">
                  <h3 className="font-semibold text-[#633D00] mb-3">Send Friend Request</h3>
                  <div className="flex gap-2">
                                          <input
                        type="email"
                        value={emailInput}
                        onChange={(e) => setEmailInput(e.target.value)}
                        placeholder="Enter email address"
                        required
                        pattern="[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$"
                        className="flex-1 px-3 py-2 border border-[#633D00]/30 rounded-md focus:outline-none focus:border-[#633D00]"
                        onKeyPress={(e) => e.key === 'Enter' && handleSendRequest()}
                      />
                                            <button
                          onClick={handleSendRequest}
                          disabled={sendLoading || !emailInput.trim() || !validateEmail(emailInput.trim())}
                          className="px-4 py-2 bg-[#633D00] text-white rounded-md hover:bg-[#633D00]/90 disabled:opacity-60 disabled:cursor-not-allowed"
                        >
                      {sendLoading ? 'Sending...' : 'Send'}
                    </button>
                  </div>
                </div>

                {/* Sent Requests */}
                <div>
                  <h3 className="font-semibold text-[#633D00] mb-3">Sent Requests</h3>
                  {sentRequests === null ? (
                    <div className="text-center py-4">
                      <div className="text-[#633D00]/70">Loading...</div>
                    </div>
                  ) : sentRequests.length === 0 ? (
                    <div className="text-center py-4">
                      <div className="text-[#633D00]/70">No sent requests</div>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {sentRequests.map((request) => (
                        <div key={request.request_id} className="rounded-md border border-[#633D00]/30 bg-white p-4 relative">
                          <div className="flex items-center justify-between">
                                                          <div>
                                <p className="font-medium text-[#633D00]">{request.receiver_email}</p>
                                <p className="text-[#633D00]/70 text-sm">Status: {request.status}</p>
                                <p className="text-[#633D00]/60 text-xs">{formatTimeAgo(request.created_at)}</p>
                              </div>
                              {request.status === 'pending' && (
                               <div className="relative">
                                 <button 
                                   className="text-[#633D00]/60 hover:text-[#633D00] p-1"
                                   onClick={(e) => {
                                     e.stopPropagation()
                                     setUnsendDropdownOpen(unsendDropdownOpen === request.request_id ? null : request.request_id)
                                   }}
                                 >
                                   <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                                     <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z" />
                                   </svg>
                                 </button>
                                 {unsendDropdownOpen === request.request_id && (
                                   <div className="absolute right-0 top-full mt-1 bg-white border border-[#633D00]/30 rounded-md shadow-lg z-10" onClick={(e) => e.stopPropagation()}>
                                     <button
                                       onClick={() => {
                                         handleUnsendRequest(request.request_id)
                                         setUnsendDropdownOpen(null)
                                       }}
                                       disabled={unsendLoading[request.request_id]}
                                       className="block w-full text-left px-3 py-2 text-sm text-red-600 hover:bg-red-50 disabled:opacity-60"
                                     >
                                       {unsendLoading[request.request_id] ? 'Unsending...' : 'Unsend'}
                                     </button>
                                   </div>
                                 )}
                               </div>
                             )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Received Tab */}
            {activeTab === 'received' && (
              <div>
                {receivedRequests === null ? (
                  <div className="text-center py-8">
                    <div className="text-[#633D00]/70">Loading requests...</div>
                  </div>
                ) : receivedRequests.length === 0 ? (
                  <div className="text-center py-8">
                    <div className="text-[#633D00]/70">No received requests</div>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {receivedRequests.map((request) => (
                      <div key={request.request_id} className="rounded-md border border-[#633D00]/30 bg-white p-4 relative">
                        {/* Time ago indicator in top right */}
                        <div className="absolute top-2 right-2 text-xs text-[#633D00]/60">
                          {formatTimeAgo(request.created_at)}
                        </div>
                        
                        <div className="mb-3 pr-16">
                          <h3 className="font-semibold text-[#633D00]">{request.sender_email}</h3>
                          <p className="text-[#633D00]/70 text-sm">Status: {request.status}</p>
                        </div>

                        {request.status === 'pending' && (
                          <div className="flex gap-2">
                            <button
                              onClick={() => handleRespondToRequest(request.request_id, 'accept')}
                              disabled={respondLoading[request.request_id]}
                              className="flex-1 rounded-md bg-green-600 text-white px-4 py-2 hover:bg-green-700 disabled:opacity-60 disabled:cursor-not-allowed"
                            >
                              {respondLoading[request.request_id] ? 'Accepting...' : 'Accept'}
                            </button>
                            <button
                              onClick={() => handleRespondToRequest(request.request_id, 'reject')}
                              disabled={respondLoading[request.request_id]}
                              className="flex-1 rounded-md bg-red-600 text-white px-4 py-2 hover:bg-red-700 disabled:opacity-60 disabled:cursor-not-allowed"
                            >
                              {respondLoading[request.request_id] ? 'Rejecting...' : 'Reject'}
                            </button>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
