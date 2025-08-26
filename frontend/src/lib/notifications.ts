import api from "./api";
import type { Notification } from "../types/api";

export async function getNotifications(): Promise<Notification[]> {
  const res = await api.get<Notification[]>('/notifications/');
  return res.data;
}

export async function markNotificationAsRead(notificationId: number): Promise<void> {
  await api.post(`/notifications/mark-as-read/${notificationId}`);
}
