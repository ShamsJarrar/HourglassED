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
  linked_event_id?: number | null;
  recurring_event_id?: number | null;
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
  linked_event_id?: number | null;
  recurring_event_id?: number | null;
}

export interface EventUpdate {
  event_type?: string; // text class name per backend expectations
  header?: string | null;
  title?: string;
  start_time?: string;
  end_time?: string;
  color?: string | null;
  notes?: string | null;
  linked_event_id?: number | null;
  recurring_event_id?: number | null;
}