export interface UserResponse {
	user_id: number;
	email: string;
	name: string;
}

export interface TokenWithUserResponse {
	access_token: string;
	token_type: string;
	user: UserResponse;
}



// Events
export interface EventCreate {
  event_type: string;
  header?: string | null;
  title: string;
  start_time: string; // ISO datetime string
  end_time: string;   // ISO datetime string
  color?: string | null;
  notes?: string | null;
  timezone: string;
  series_id?: number | null;
  is_exception?: boolean;
}

// Note: EventResponse from backend returns numeric class id
export interface EventResponse {
  event_id: number;
  user_id: number;
  event_type: number;
  header?: string | null;
  title: string;
  start_time: string;
  end_time: string;
  color?: string | null;
  notes?: string | null;
  series_id?: number | null;
  is_exception: boolean;
  timezone: string;
}

export interface EventUpdate {
  event_type?: string; // text class name per backend expectations
  header?: string | null;
  title?: string;
  start_time?: string;
  end_time?: string;
  color?: string | null;
  notes?: string | null;
  series_id?: number | null;
  is_exception?: boolean;
  timezone?: string;
}

// Invitations
export type InvitationStatus =
  | "pending"
  | "accepted"
  | "rejected"
  | "withdrawn"
  | "removed"
  | "expired";

export interface EventInvitationWithEvent {
  invitation_id: number;
  status: InvitationStatus;
  created_at: string;
  // Backend may include either invited_user_id or invited_user.email depending on schema
  invited_user_id?: number;
  invited_user?: { email: string } | null;
  event: {
    event_id: number;
    event_type: number;
    user: { email: string };
    header?: string | null;
    title: string;
    start_time: string;
    end_time: string;
    color?: string | null;
    notes?: string | null;
    series_id?: number | null;
    is_exception: boolean;
    timezone: string;
  };
}

// Friends
export interface FriendResponse {
  friend_name: string;
  friend_email: string;
}

// Friends list (owner inviting): backend may include the user id
export interface FriendListItem {
  friend_id?: number;
  friend_name: string;
  friend_email: string;
}

export interface FriendsListResponseItem {
  friend_id: number;
  friend_name: string;
  friend_email: string;
}

// Friend Requests
export interface FriendRequest {
  request_id: number;
  sender_email: string;
  receiver_email: string;
  status: 'pending' | 'accepted' | 'rejected';
  created_at: string;
}

export interface SentFriendRequest {
  request_id: number;
  receiver_email: string;
  status: 'pending' | 'accepted' | 'rejected';
  created_at: string;
}

export interface ReceivedFriendRequest {
  request_id: number;
  sender_email: string;
  status: 'pending' | 'accepted' | 'rejected';
  created_at: string;
}

export interface SendFriendRequestRequest {
  receiver_email: string;
}

// Notifications
export interface Notification {
  notification_id: number;
  message: string;
  is_read: boolean;
  created_at: string;
  type?: string;
}

// Recurrence Series
export interface RecurrenceSeriesCreate {
  recurrence_pattern: string;
  recurrence_end?: string | null; // ISO datetime string or null
}

export interface RecurrenceSeriesResponse {
  series_id: number;
  user_id: number;
  recurrence_pattern: string;
  recurrence_end?: string | null;
  created_at: string;
}

export interface RecurrenceSeriesUpdate {
  recurrence_pattern?: string;
  recurrence_end?: string | null;
}