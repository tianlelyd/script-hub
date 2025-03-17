addEventListener("fetch", (event) => {
  event.respondWith(handleRequest(event.request));
});

async function handleRequest(request) {
  // 获取 CF 提供的客户端IP
  const clientIP = request.headers.get("CF-Connecting-IP");

  // 构建响应数据
  const data = {
    ip: clientIP,
    // 可选：获取更多 CF 提供的信息
    country: request.headers.get("CF-IPCountry"),
    // 添加所有请求头信息（可选，用于调试）
    headers: Object.fromEntries([...request.headers]),
  };

  // 返回 JSON 响应
  return new Response(JSON.stringify(data, null, 2), {
    headers: {
      "Content-Type": "application/json",
      "Access-Control-Allow-Origin": "*", // 允许跨域访问
      "Cache-Control": "no-store", // 禁用缓存
    },
  });
}
