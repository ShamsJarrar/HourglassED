import api from "./api";
import type { EventResponse, EventUpdate } from "../types/api";

export interface GetEventsParams {
  start_time?: string;
  end_time?: string;
  event_type?: number;
  owned_only?: boolean;
}

export async function getEvents(params: GetEventsParams = {}): Promise<EventResponse[]> {
  const res = await api.get<EventResponse[]>("/event/", { params });
  return res.data;
}

export interface EventClassResponse {
  class_id: number;
  class_name: string;
  is_builtin: boolean;
  created_by?: number | null;
}

export async function getEventClasses(): Promise<EventClassResponse[]> {
  const res = await api.get<EventClassResponse[]>("/event/classes");
  return res.data;
}

export async function updateEvent(eventId: number, body: EventUpdate): Promise<EventResponse> {
  const res = await api.put<EventResponse>(`/event/${eventId}`, body);
  return res.data;
}

export async function deleteEventById(eventId: number): Promise<void> {
  await api.delete(`/event/${eventId}`);
}

export async function removeUserFromEvent(eventId: number, invitedUserId: number): Promise<void> {
  await api.delete(`/event/${eventId}/remove/${invitedUserId}`);
}

export async function withdrawFromEvent(eventId: number): Promise<void> {
  await api.delete(`/event/${eventId}/withdraw`);
}