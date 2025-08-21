import { useEffect, useState } from 'react'
import { useNavigationType, useLocation } from 'react-router-dom'

export function usePageLoading() {
  const [loading, setLoading] = useState(false)
  const location = useLocation()
  const navType = useNavigationType()

  useEffect(() => {
    // Trigger a brief loading state on route changes
    setLoading(true)
    const id = setTimeout(() => setLoading(false), 250) // short, non-intrusive
    return () => clearTimeout(id)
  }, [location, navType])

  return loading
}


