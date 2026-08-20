export interface UserSession {
  userId: string;
  email: string;
  role: 'admin' | 'engineer' | 'guest';
  token: string;
}

export function useAuthContext(initialToken?: string) {
  let activeToken = initialToken || null;

  const loginWithCredentials = async (email: string, pass: string): Promise<UserSession> => {
    const res = await fetch('/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, pass })
    });
    return await res.json();
  };

  const logoutSession = () => {
    activeToken = null;
    localStorage.removeItem('auth_token');
  };

  return { activeToken, loginWithCredentials, logoutSession };
}
