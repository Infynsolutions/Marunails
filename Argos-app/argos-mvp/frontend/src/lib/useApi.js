import { useMemo } from 'react';
import { useAuth } from './auth';
import { makeApi } from './api';

/**
 * Returns the api object scoped to the current user's tenant.
 * Returns null while auth is loading or tenant is not yet resolved.
 */
export function useApi() {
  const { tenantId } = useAuth();
  return useMemo(() => (tenantId ? makeApi(tenantId) : null), [tenantId]);
}
