import api from "./api";
import type { EventResponse, EventUpdate, EventCreate } from "../types/api";
import type { RecurrenceSeriesCreate, RecurrenceSeriesResponse, RecurrenceSeriesUpdate } from "../types/api";

export interface GetEventsParams {
  start_time?: string;
  end_time?: string;
  event_types?: number[];
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
  const res = await api.get<EventClassResponse[]>("/classes/");
  return res.data;
}

export async function getEventClassById(classId: number): Promise<EventClassResponse> {
  const res = await api.get<EventClassResponse>(`/classes/${classId}`);
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

export async function createEvent(body: EventCreate): Promise<EventResponse> {
  const res = await api.post<EventResponse>(`/event/`, body);
  return res.data;
}

// Recurrence Series API
export interface CreateSeriesBody {
  recurrence: RecurrenceSeriesCreate;
  event: EventCreate;
}

export async function createSeries(body: CreateSeriesBody): Promise<RecurrenceSeriesResponse> {
  const res = await api.post<RecurrenceSeriesResponse>(`/series/create`, body);
  return res.data;
}

export interface UpdateSeriesParams {
  pivot?: string; // ISO datetime; if omitted, backend uses current UTC
  months?: number; // how many months to generate (default 6)
}

export async function updateSeries(seriesId: number, body: RecurrenceSeriesUpdate, params: UpdateSeriesParams = {}): Promise<RecurrenceSeriesResponse> {
  const res = await api.patch<RecurrenceSeriesResponse>(`/series/${seriesId}`, body, { params });
  return res.data;
}

export async function getSeries(seriesId: number): Promise<RecurrenceSeriesResponse> {
  const res = await api.get<RecurrenceSeriesResponse>(`/series/${seriesId}`);
  return res.data;
}

export async function deleteSeries(seriesId: number): Promise<void> {
  await api.delete(`/series/${seriesId}`);
}