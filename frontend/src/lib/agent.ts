import api from "./api";
import type { AgentInitialRequest, AgentResumeRequest, AgentResponse } from "../types/api";

export async function startAgent(body: AgentInitialRequest): Promise<AgentResponse> {
  const res = await api.post<AgentResponse>("/agent/start", body);
  return res.data;
}

export async function resumeAgent(body: AgentResumeRequest): Promise<AgentResponse> {
  const res = await api.post<AgentResponse>("/agent/resume", body);
  return res.data;
}


