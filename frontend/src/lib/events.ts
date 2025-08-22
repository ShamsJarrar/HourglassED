import api from "./api";
import type { EventResponse } from "../types/api";

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


