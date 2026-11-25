import { useCallback, useEffect, useState } from 'react'

interface ApiState<T> {
  data: T | null
  error: string | null
  loading: boolean
}

/** Small data-fetching hook with manual refetch and graceful error state. */
export function useApi<T>(loader: () => Promise<T>, deps: unknown[] = []) {
  const [state, setState] = useState<ApiState<T>>({
    data: null,
    error: null,
    loading: true,
  })

  // eslint-disable-next-line react-hooks/exhaustive-deps
  const load = useCallback(loader, deps)

  const refetch = useCallback(async () => {
    setState((previous) => ({ ...previous, loading: true, error: null }))
    try {
      const data = await load()
      setState({ data, error: null, loading: false })
      return data
    } catch (error) {
      setState({
        data: null,
        error: error instanceof Error ? error.message : 'Unknown error',
        loading: false,
      })
      return null
    }
  }, [load])

  useEffect(() => {
    void refetch()
  }, [refetch])

  return { ...state, refetch }
}
