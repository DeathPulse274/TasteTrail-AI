import express from 'express';
import path from 'path';
import { createServer as createViteServer } from 'vite';
import dotenv from 'dotenv';

dotenv.config();

const BACKEND_URL = process.env.BACKEND_URL ?? 'http://127.0.0.1:8000';
const PORT = Number(process.env.PORT ?? 3000);

function filterHeaders(headers: Record<string, string | undefined>) {
    const filtered: Record<string, string> = {};
    for (const [key, value] of Object.entries(headers)) {
        if (!value) continue;
        if ([
            'host',
            'connection',
            'content-length',
            'accept-encoding',
            'expect',
        ].includes(key.toLowerCase())) {
            continue;
        }
        filtered[key] = value;
    }
    return filtered;
}

async function proxyToBackend(req: express.Request, res: express.Response) {
    const forwardedPath = req.originalUrl.replace(/^\/api/, '') || '/';
    const targetUrl = `${BACKEND_URL}${forwardedPath}`;
    const init: RequestInit = {
        method: req.method,
        headers: {
            ...filterHeaders(req.headers as Record<string, string | undefined>),
            'content-type': req.headers['content-type'] || 'application/json',
        },
    };
    if (req.method !== 'GET' && req.method !== 'HEAD') {
        init.body = JSON.stringify(req.body);
    }

    const backendResponse = await fetch(targetUrl, init);
    const responseText = await backendResponse.text();

    res.status(backendResponse.status);
    backendResponse.headers.forEach((value, key) => {
        if (key.toLowerCase() === 'content-encoding') return;
        res.setHeader(key, value);
    });
    res.send(responseText);
}

async function startServer() {
    const app = express();
    app.use(express.json());

    app.use('/api', async (req, res, next) => {
        try {
            await proxyToBackend(req, res);
        } catch (error) {
            console.error('API proxy error:', error);
            next(error);
        }
    });

    if (process.env.NODE_ENV !== 'production') {
        const vite = await createViteServer({
            server: {
                middlewareMode: true,
                hmr: process.env.DISABLE_HMR === 'true' ? false : true,
            },
            appType: 'spa',
        });
        app.use(vite.middlewares);
    } else {
        const distPath = path.join(process.cwd(), 'dist');
        app.use(express.static(distPath));
        app.get('*', (req, res) => {
            res.sendFile(path.join(distPath, 'index.html'));
        });
    }

    app.listen(PORT, '0.0.0.0', () => {
        console.log(`Frontend server running on http://localhost:${PORT}`);
        console.log(`Proxying API requests to ${BACKEND_URL}`);
    });
}

startServer();
