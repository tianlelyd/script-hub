/**
 * Cloudflare Workers 边缘代理
 * 该脚本用于将请求代理到指定的目标域名
 * @author 未指定
 * @version 1.0.0
 */

/**
 * 监听所有fetch事件并处理请求
 * @param {FetchEvent} event - Fetch事件对象
 */
addEventListener("fetch", (event) => {
  event.respondWith(handleRequest(event.request));
});

/**
 * 处理传入的请求并转发到目标服务器
 * @param {Request} request - 客户端请求对象
 * @returns {Promise<Response>} 返回响应对象
 */
async function handleRequest(request) {
  // 解析 URL 和路径
  const url = new URL(request.url);
  const path = url.pathname.slice(1); // 移除开头的 '/'

  // 如果路径为空，返回 400 错误
  if (!path) {
    return new Response(
      JSON.stringify({
        error: "Missing proxy destination",
        code: 400,
      }),
      {
        status: 400,
        headers: {
          "content-type": "application/json",
          "Cache-Control": "no-cache",
        },
      }
    );
  }

  // 构建目标域名,请修改为你的域名
  const targetDomain = `${path}.***.top`;

  // 构建新的目标 URL
  const targetUrl = `https://${targetDomain}${url.search}`;

  // 获取请求信息
  const clientIP = request.headers.get("CF-Connecting-IP");
  const country = request.headers.get("CF-IPCountry");
  const colo = request.cf.colo;

  // 构建优化后的请求配置
  const requestInit = {
    method: request.method,
    headers: new Headers(request.headers),
    cf: {
      // 连接优化
      http3: true, // 启用 HTTP/3
      zero_rtt: true, // 启用 0-RTT
      tcp_turbo: true, // 启用 TCP turbo 模式
      resolveOverride: targetDomain,
      // WebSocket 优化
      webSocket: {
        enableCompression: true, // 启用 WebSocket 压缩
        keepAliveTimeout: 60, // 保持连接活跃
      },
    },
  };

  try {
    // 发送请求到后端
    let response = await fetch(targetUrl, requestInit);

    // 添加响应头
    response = new Response(response.body, response);
    response.headers.set("CF-Cache-Status", "DYNAMIC");
    response.headers.set("CF-Ray", request.headers.get("CF-Ray"));

    return response;
  } catch (err) {
    // 错误处理
    return new Response(
      JSON.stringify({
        error: "Backend connection failed",
        code: 502,
      }),
      {
        status: 502,
        headers: {
          "content-type": "application/json",
          "Cache-Control": "no-cache",
        },
      }
    );
  }
}
