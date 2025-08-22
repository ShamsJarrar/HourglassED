import api from "./api";
import type { EventInvitationWithEvent, InvitationStatus } from "../types/api";

export interface GetSentInvitationsParams {
  event_id?: number;
  status?: InvitationStatus;
}

export async function getSentInvitations(
  params: GetSentInvitationsParams = {}
): Promise<EventInvitationWithEvent[]> {
  const res = await api.get<EventInvitationWithEvent[]>("/invitations/sent", {
    params,
  });
  return res.data;
}

export interface ParticipantResponse {
  user_name: string;
  user_email: string;
}

export async function getParticipants(eventId: number): Promise<ParticipantResponse[]> {
  const res = await api.get<ParticipantResponse[]>(`/invitations/participants/${eventId}`);
  return res.data;
}

export interface CreateInvitationBody {
  event_id: number;
  invited_user_id: number;
}

export async function createInvitation(body: CreateInvitationBody) {
  const res = await api.post(`/invitations/`, body);
  return res.data;
}
