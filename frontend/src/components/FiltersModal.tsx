import { useEffect, useState } from 'react'
import { getEventClasses, type EventClassResponse } from '../lib/events'

interface Props {
  open: boolean
  onClose: () => void
  value: { owned_only?: boolean; event_types?: number[] | null }
  onChange: (next: { owned_only?: boolean; event_types?: number[] | null }) => void
}

export default function FiltersModal({ open, onClose, value, onChange }: Props) {
  const [classes, setClasses] = useState<EventClassResponse[]>([])
  const [ownedOnly, setOwnedOnly] = useState<boolean>(!!value.owned_only)
  const [selectedTypes, setSelectedTypes] = useState<number[]>(value.event_types ?? [])

  useEffect(() => {
    if (!open) return
    getEventClasses().then(setClasses).catch(() => setClasses([]))
    setOwnedOnly(!!value.owned_only)
    setSelectedTypes(value.event_types ?? [])
  }, [open])

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/30" onClick={onClose}>
      <div className="w-[420px] max-w-[92vw] rounded-xl bg-[#FFF8EB] border-2 border-[#633D00] shadow-2xl" onClick={(e) => e.stopPropagation()}>
        <div className="p-5">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-[#633D00]">Filters</h2>
            <button onClick={onClose} className="text-[#633D00] border border-[#633D00] rounded-md px-2 py-0.5">Close</button>
          </div>

          <div className="space-y-4 text-[#633D00]">
            <label className="flex items-center gap-2">
              <input type="checkbox" checked={ownedOnly} onChange={(e) => setOwnedOnly(e.target.checked)} />
              <span>Owned events only</span>
            </label>

            <div>
              <label className="block text-sm mb-2">Event Types</label>
              <div className="grid grid-cols-2 gap-2">
                {classes.map((c) => {
                  const checked = selectedTypes.includes(c.class_id)
                  return (
                    <label key={c.class_id} className="flex items-center gap-2 text-sm">
                      <input
                        type="checkbox"
                        checked={checked}
                        onChange={(e) => {
                          setSelectedTypes((prev) =>
                            e.target.checked ? [...prev, c.class_id] : prev.filter((id) => id !== c.class_id)
                          )
                        }}
                      />
                      <span>{c.class_name}</span>
                    </label>
                  )
                })}
              </div>
            </div>
          </div>

          <div className="mt-6 flex justify-end gap-2">
            <button
              onClick={() => {
                setOwnedOnly(false)
                setSelectedTypes([])
                onChange({ owned_only: false, event_types: [] })
                onClose()
              }}
              className="rounded-md border border-[#633D00] text-[#633D00] px-3 py-1.5 hover:bg-[#ead9be]"
            >
              Clear
            </button>
            <button
              onClick={() => {
                onChange({ owned_only: ownedOnly || undefined, event_types: selectedTypes })
                onClose()
              }}
              className="rounded-md bg-[#633D00] text-[#FAF0DC] px-4 py-2 hover:bg-[#765827]"
            >
              Apply
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}


