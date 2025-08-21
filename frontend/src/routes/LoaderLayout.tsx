import { Outlet } from 'react-router-dom'
import PageLoader from '../components/PageLoader'
import { usePageLoading } from '../hooks/usePageLoading'

export default function LoaderLayout() {
  const loading = usePageLoading()
  return (
    <>
      <Outlet />
      {loading && <PageLoader />}
    </>
  )
}


