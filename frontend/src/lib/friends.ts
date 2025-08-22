import api from "./api";
import type { FriendResponse } from "../types/api";

export async function getFriendById(friendId: number): Promise<FriendResponse> {
  const res = await api.get<FriendResponse>(`/friends/friends/${friendId}`);
  return res.data;
}

export interface FriendsListResponseItem {
  friend_id: number;
  friend_name: string;
  friend_email: string;
}

export async function getFriendsList(): Promise<FriendsListResponseItem[]> {
  const res = await api.get<FriendsListResponseItem[]>(`/friends/friends`);
  return res.data;
}
