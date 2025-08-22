import api from "./api";
import type { FriendResponse } from "../types/api";

export async function getFriendById(friendId: number): Promise<FriendResponse> {
  const res = await api.get<FriendResponse>(`/friends/friends/${friendId}`);
  return res.data;
}
