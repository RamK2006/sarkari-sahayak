import { NextRequest } from 'next/server';

export const dynamic = 'force-dynamic';

const BACKEND = (process.env.BACKEND_URL ?? 'http://localhost:8000').replace(/\/$/, '');

/** Same-origin proxy to the API, so the browser never needs the backend address or CORS. */
async function proxy(req: NextRequest, { params }: { params: { path: string[] } }) {
  const target = `${BACKEND}/api/${params.path.map(encodeURIComponent).join('/')}${req.nextUrl.search}`;
  const headers = new Headers();
  const type = req.headers.get('content-type');
  if (type) headers.set('content-type', type);
  const forwarded = req.headers.get('x-forwarded-for');
  if (forwarded) headers.set('x-forwarded-for', forwarded);

  let upstream: Response;
  try {
    upstream = await fetch(target, {
      method: req.method,
      headers,
      body: req.method === 'GET' ? undefined : await req.arrayBuffer(),
      cache: 'no-store',
    });
  } catch {
    return Response.json({ detail: { code: 'service_unavailable' } }, { status: 503 });
  }
  return new Response(upstream.body, {
    status: upstream.status,
    headers: {
      'content-type': upstream.headers.get('content-type') ?? 'application/json',
      'cache-control': 'no-store',
    },
  });
}

export { proxy as GET, proxy as POST };
