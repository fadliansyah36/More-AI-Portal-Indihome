import { once } from "node:events";
import {
  type ClientRequest,
  createServer,
  type IncomingMessage,
  type RequestOptions,
  request,
} from "node:http";
import { connect, type Socket } from "node:net";
import { validatePublicUrl } from "./network.ts";

/**
 * MoreAI egress boundary override for the pinned OpenFuse worker.
 * Browser traffic is forced through this loopback listener, which forwards
 * HTTPS CONNECT only to the isolated MoreAI egress proxy. The browser worker
 * itself has no external network interface.
 */
export async function startEgressProxy(
  _sendHttpRequest: (
    options: RequestOptions,
    onResponse: (response: IncomingMessage) => void,
  ) => ClientRequest = request,
) {
  const sockets = new Set<Socket>();
  const server = createServer((_incoming, response) => {
    response.writeHead(403, { connection: "close", "content-type": "text/plain" });
    response.end("Only HTTPS CONNECT is permitted.");
  });

  server.on("connect", async (incoming, client, head) => {
    client.on("error", () => client.destroy());
    try {
      const authority = incoming.url ?? "";
      if (!/^(?:\[[0-9a-f:]+\]|[a-z0-9.-]+):443$/i.test(authority))
        throw new Error("Invalid HTTPS tunnel authority");
      // Retain OpenFuse's own URL/IP validation before delegating to the
      // second, network-boundary validator in the MoreAI egress proxy.
      await validatePublicUrl(`https://${authority}`);
      if (client.destroyed) return;

      const upstreamProxy = new URL(process.env.MOREAI_BROWSER_UPSTREAM_PROXY_URL ?? "");
      const token = process.env.MOREAI_BROWSER_PROXY_TOKEN ?? "";
      if (
        upstreamProxy.protocol !== "http:"
        || upstreamProxy.hostname !== "browser-egress-proxy"
        || Number(upstreamProxy.port || 80) !== 3128
        || upstreamProxy.username || upstreamProxy.password
        || upstreamProxy.pathname !== "/" || upstreamProxy.search || upstreamProxy.hash
        || token.length < 32
      ) throw new Error("MoreAI private egress proxy configuration is invalid");

      const upstream = connect({
        host: upstreamProxy.hostname,
        port: Number(upstreamProxy.port || 80),
      });
      sockets.add(upstream);
      upstream.setTimeout(60_000, () => upstream.destroy());
      upstream.on("close", () => {
        sockets.delete(upstream);
        client.destroy();
      });
      upstream.on("error", () => client.destroy());
      client.on("close", () => upstream.destroy());

      let responseHeader = Buffer.alloc(0);
      let handshakeComplete = false;
      const onProxyData = (chunk: Buffer) => {
        if (handshakeComplete) {
          client.write(chunk);
          return;
        }
        responseHeader = Buffer.concat([responseHeader, chunk]);
        if (responseHeader.length > 16_384) {
          upstream.destroy();
          client.destroy();
          return;
        }
        const boundary = responseHeader.indexOf("\r\n\r\n");
        if (boundary < 0) return;
        const headerText = responseHeader.subarray(0, boundary).toString("latin1");
        const statusLine = headerText.split("\r\n", 1)[0] ?? "";
        if (!/^HTTP\/1\.[01] 200(?:\s|$)/.test(statusLine)) {
          client.end("HTTP/1.1 403 Forbidden\r\nConnection: close\r\n\r\n");
          upstream.destroy();
          return;
        }
        handshakeComplete = true;
        upstream.off("data", onProxyData);
        client.write("HTTP/1.1 200 Connection Established\r\nProxy-Agent: MoreAI-Egress\r\n\r\n");
        const remainder = responseHeader.subarray(boundary + 4);
        if (remainder.length) client.write(remainder);
        upstream.pipe(client);
        client.pipe(upstream);
      };
      upstream.on("data", onProxyData);
      upstream.once("connect", () => {
        const authorization = Buffer.from(`moreai:${token}`).toString("base64");
        upstream.write(
          `CONNECT ${authority} HTTP/1.1\r\nHost: ${authority}\r\nProxy-Authorization: Basic ${authorization}\r\nConnection: keep-alive\r\n\r\n`,
        );
      });
    } catch {
      client.end("HTTP/1.1 403 Forbidden\r\nConnection: close\r\n\r\n");
    }
  });

  server.on("connection", (socket) => {
    sockets.add(socket);
    socket.on("close", () => sockets.delete(socket));
  });
  server.listen(0, "127.0.0.1");
  await once(server, "listening");
  const address = server.address();
  if (!address || typeof address === "string") throw new Error("Proxy unavailable");
  return {
    url: `http://127.0.0.1:${address.port}`,
    close: async () => {
      for (const socket of sockets) socket.destroy();
      await new Promise<void>((resolve) => server.close(() => resolve()));
    },
  };
}
