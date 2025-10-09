import { useEffect, useState } from 'react'
import { startAgent, resumeAgent } from '../lib/agent'
import type { AgentResponse } from '../types/api'
import { getEventClassById, type EventClassResponse } from '../lib/events'

interface Props {
  open: boolean
  onClose: () => void
  onCommitted?: () => void
}

export default function AgentModal({ open, onClose, onCommitted }: Props) {
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [loadingLabel, setLoadingLabel] = useState<'Thinking…' | 'Working…' | null>(null)
  const [initialPrompt, setInitialPrompt] = useState('')
  const [threadId, setThreadId] = useState<string | null>(null)
  const [answer, setAnswer] = useState<string>('')
  const [proposals, setProposals] = useState<any[] | null>(null)
  const [feedback, setFeedback] = useState('')
  const [awaitingFeedback, setAwaitingFeedback] = useState(false)
  const [classNameById, setClassNameById] = useState<Map<number, string>>(new Map())

  const reset = () => {
    setInput('')
    setLoading(false)
    setThreadId(null)
    setAnswer('')
    setProposals(null)
    setFeedback('')
    setAwaitingFeedback(false)
  }

  const handleStart = async () => {
    if (!input.trim()) return
    try {
      setLoading(true)
      setLoadingLabel('Thinking…')
      setInitialPrompt(input)
      const res: AgentResponse = await startAgent({
        user_input: input,
        client_now_iso: new Date().toISOString(),
        client_timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
      })
      setThreadId(res.thread_id)
      setAnswer(res.answer)
      setProposals(res.proposed_events ?? null)
      setAwaitingFeedback(res.run_state === 'user_feedback')
      setInput('')
    } catch (e) {
      console.error(e)
      alert('Failed to run agent')
    } finally {
      setLoading(false)
      setLoadingLabel(null)
    }
  }
  // Load class names for any numeric proposed event_type ids so we can show strings
  useEffect(() => {
    if (!proposals || !proposals.length) return
    const ids = new Set<number>()
    for (const p of proposals as any[]) {
      const isSeries = p && typeof p === 'object' && 'recurrence' in p && 'event' in p
      const ev = isSeries ? (p.event || {}) : p
      const t = ev?.event_type
      if (typeof t === 'number' && !classNameById.has(t)) ids.add(t)
    }
    if (!ids.size) return
    ;(async () => {
      const updates = new Map(classNameById)
      for (const id of ids) {
        try {
          const cls: EventClassResponse = await getEventClassById(id)
          updates.set(id, cls.class_name)
        } catch {
          // ignore missing class; leave numeric fallback
        }
      }
      setClassNameById(updates)
    })()
  }, [proposals])

  const displayType = (eventType: unknown) => {
    if (typeof eventType === 'string') return eventType
    if (typeof eventType === 'number') return classNameById.get(eventType) ?? String(eventType)
    return '—'
  }

  const handleApproveOrFeedback = async (status: 'approved' | 'feedback') => {
    if (!threadId) return
    try {
      setLoading(true)
      setLoadingLabel(status === 'approved' ? 'Working…' : 'Thinking…')
      if (status === 'feedback') setFeedback('')
      const res = await resumeAgent({ thread_id: threadId, status, user_feedback: status === 'feedback' ? feedback : undefined })
      setAnswer(res.answer)
      setProposals(res.proposed_events ?? null)
      setAwaitingFeedback(res.run_state === 'user_feedback')
      if (status === 'approved' && res.run_state === 'finished') {
        onCommitted?.()
      }
    } catch (e) {
      console.error(e)
      alert('Failed to resume agent')
    } finally {
      setLoading(false)
      setLoadingLabel(null)
    }
  }

  const handleSkip = async () => {
    if (!threadId) return
    try {
      setLoading(true)
      await resumeAgent({ thread_id: threadId, status: 'skip' })
      // Return to initial prompt state (don't close modal)
      const lastInput = input
      reset()
      setInput(lastInput)
    } catch (e) {
      console.error(e)
      alert('Failed to skip')
    } finally {
      setLoading(false)
    }
  }

  const formatTime = (iso?: string) => {
    if (!iso) return ''
    try {
      const d = new Date(iso)
      return `${d.toLocaleDateString()} ${d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`
    } catch {
      return iso
    }
  }

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/30" onClick={() => { reset(); onClose() }}>
      <div className="w-[700px] max-w-[96vw] max-h-[86vh] rounded-xl bg-[#FFF8EB] border-2 border-[#633D00] shadow-2xl" onClick={(e) => e.stopPropagation()}>
        <div className="p-5 flex flex-col gap-4" style={{ maxHeight: '86vh' }}>
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-[#633D00]">Organize with Agent</h2>
            <button onClick={() => { reset(); onClose() }} className="text-[#633D00] border border-[#633D00] rounded-md px-2 py-0.5">Close</button>
          </div>

          {!threadId && (
            <div className="space-y-2">
              <label className="block text-sm text-[#633D00]">What do you want to organize?</label>
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                className="w-full min-h-28 rounded-md border border-[#633D00] px-3 py-2 bg-white text-[#633D00]"
                placeholder="Describe what events you want the agent to help you organize, mention specific times, dates or other constraints (ex. Organize multiple chemistry study sessions for this week, I need a total of 10 hours of study time)"
              />
            </div>
          )}

          {threadId && (
            <div className="grid grid-cols-1 gap-4 overflow-y-auto no-scrollbar">
              <div className="space-y-2">
                <div className="text-sm font-medium text-[#633D00]">Your request</div>
                <div className="rounded-md border border-[#633D00]/30 bg-white p-3 text-[#633D00] whitespace-pre-wrap">{initialPrompt || '(cleared)'}</div>
              </div>
              <div className="space-y-2">
                <div className="text-sm font-medium text-[#633D00]">Agent response</div>
                <div className="rounded-md border border-[#633D00]/30 bg-white p-3 text-[#633D00] whitespace-pre-wrap">{answer || '(No answer)'}</div>
              </div>

              {proposals && proposals.length > 0 && (
                <div className="space-y-2">
                  <div className="text-sm font-medium text-[#633D00]">Proposed events</div>
                  <div className="space-y-2 max-h-48 overflow-y-auto no-scrollbar pr-1">
                    {(proposals as any[]).map((p, idx) => {
                      const isSeries = p && typeof p === 'object' && 'recurrence' in p && 'event' in p
                      const ev = isSeries ? (p.event || {}) : p
                      const rec = isSeries ? (p.recurrence || {}) : null
                      return (
                        <div key={idx} className="rounded-md border border-[#633D00]/30 bg-white p-3 text-[#633D00]">
                          <div className="flex items-center justify-between text-sm">
                            <div className="font-medium truncate">{ev?.title || '(Untitled)'}</div>
                            {ev?.color && (
                              <span className="ml-2 inline-block h-3 w-3 rounded-sm border" style={{ backgroundColor: ev.color }} />
                            )}
                          </div>
                          <div className="mt-1 text-xs">
                            <div><span className="opacity-70">Type:</span> {displayType(ev?.event_type)}</div>
                            <div><span className="opacity-70">Start:</span> {formatTime(ev?.start_time)}</div>
                            <div><span className="opacity-70">End:</span> {formatTime(ev?.end_time)}</div>
                            {ev?.header && <div><span className="opacity-70">Header:</span> {ev.header}</div>}
                            {ev?.notes && <div><span className="opacity-70">Notes:</span> {ev.notes}</div>}
                            {isSeries && (
                              <div className="mt-1">
                                <div className="font-medium">Recurrence</div>
                                <div className="opacity-90">Pattern: {rec?.recurrence_pattern || '—'}</div>
                                {rec?.recurrence_end && <div className="opacity-90">Ends: {formatTime(rec?.recurrence_end)}</div>}
                              </div>
                            )}
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}

              {awaitingFeedback && (
                <div className="space-y-2">
                  <label className="block text-sm text-[#633D00]">Feedback to refine</label>
                  <textarea
                    value={feedback}
                    onChange={(e) => setFeedback(e.target.value)}
                    className="w-full min-h-24 rounded-md border border-[#633D00] px-3 py-2 bg-white text-[#633D00]"
                    placeholder="Add corrections or constraints"
                  />
                  {/* Buttons are in the footer */}
                </div>
              )}
            </div>
          )}
          {/* Footer Actions */}
          <div className="mt-2 flex justify-end gap-2">
            {!threadId && !loading && (
              <button
                onClick={handleStart}
                disabled={!input.trim()}
                className="rounded-md bg-[#633D00] text-[#FAF0DC] px-4 py-2 hover:bg-[#765827] disabled:opacity-60 disabled:cursor-not-allowed"
              >
                Start
              </button>
            )}

            {threadId && awaitingFeedback && !loading && (
              <>
                <button onClick={handleSkip} className="rounded-md bg-white text-[#633D00] border border-[#633D00] px-4 py-2 hover:bg-[#ead9be]">Skip</button>
                <button onClick={() => handleApproveOrFeedback('feedback')} className="rounded-md bg-[#FAF0DC] text-[#633D00] border border-[#633D00] px-4 py-2 hover:bg-[#ead9be]">Send feedback</button>
                <button onClick={() => handleApproveOrFeedback('approved')} className="rounded-md bg-[#633D00] text-[#FAF0DC] px-4 py-2 hover:bg-[#765827]">Approve</button>
              </>
            )}

            {loading && (
              <button disabled className="rounded-md bg-[#633D00] text-[#FAF0DC] px-4 py-2 opacity-80 cursor-wait">{loadingLabel ?? 'Working…'}</button>
            )}

            {threadId && !awaitingFeedback && !loading && (
              <button onClick={() => { onCommitted?.(); reset(); onClose() }} className="rounded-md bg-[#633D00] text-[#FAF0DC] px-4 py-2 hover:bg-[#765827]">Done</button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}


