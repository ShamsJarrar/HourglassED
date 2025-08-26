import api from "./api";
import type { 
  FriendResponse, 
  FriendsListResponseItem,
  SentFriendRequest,
  ReceivedFriendRequest,
  SendFriendRequestRequest
} from "../types/api";

export async function getFriendById(friendId: number): Promise<FriendResponse> {
  const res = await api.get<FriendResponse>(`/friends/friends/${friendId}`);
  return res.data;
}



export async function getFriendsList(): Promise<FriendsListResponseItem[]> {
  const res = await api.get<FriendsListResponseItem[]>(`/friends/friends`);
  return res.data;
}

// Friend request functions
export async function sendFriendRequest(data: SendFriendRequestRequest): Promise<void> {
  await api.post('/friends/friend-request', data);
}

export async function getSentFriendRequests(): Promise<SentFriendRequest[]> {
  const res = await api.get<SentFriendRequest[]>('/friends/friend-requests/sent');
  return res.data;
}

export async function getReceivedFriendRequests(): Promise<ReceivedFriendRequest[]> {
  const res = await api.get<ReceivedFriendRequest[]>('/friends/friend-requests/received');
  return res.data;
}

export async function acceptFriendRequest(requestId: number): Promise<void> {
  await api.post(`/friends/friend-request/${requestId}/accept`);
}

export async function rejectFriendRequest(requestId: number): Promise<void> {
  await api.post(`/friends/friend-request/${requestId}/reject`);
}

export async function unsendFriendRequest(requestId: number): Promise<void> {
  await api.delete(`/friends/friend-request/${requestId}/unsend`);
}

export async function unfriendUser(friendId: number): Promise<void> {
  await api.delete(`/friends/unfriend/${friendId}`);
}
