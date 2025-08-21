export type JwtPayload = {
  exp?: number
  [key: string]: unknown
}

function base64UrlDecode(input: string): string {
  const base64 = input.replace(/-/g, '+').replace(/_/g, '/').padEnd(Math.ceil(input.length / 4) * 4, '=')
  try {
    return atob(base64)
  } catch {
    return ''
  }
}

export function parseJwt(token: string): JwtPayload | null {
  const parts = token.split('.')
  if (parts.length !== 3) return null
  const payloadJson = base64UrlDecode(parts[1])
  try {
    return JSON.parse(payloadJson)
  } catch {
    return null
  }
}

export function isTokenExpired(token: string): boolean {
  const payload = parseJwt(token)
  if (!payload || typeof payload.exp !== 'number') return true
  const nowSeconds = Math.floor(Date.now() / 1000)
  return nowSeconds >= payload.exp
}


