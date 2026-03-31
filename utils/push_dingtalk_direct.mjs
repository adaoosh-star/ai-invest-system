#!/usr/bin/env node
/**
 * 钉钉推送 - 直接调用钉钉连接器
 */

import { sendProactive } from '/home/admin/.openclaw/extensions/dingtalk-connector/src/services/messaging.ts';

const config = {
  clientId: "dinggmk7kpiddrrvi0l5",
  clientSecret: "9RR-37dNLUKRkzzS-1RN5CHsDSJnIKEtBCd3-O9MqB7SvYUduBwse8FhEtMnr2bN",
  gatewayToken: "7c945e183e33b18df341e2c3ad9ced59e0a7f156d7d20238"
};

const userId = "01023647151178899";
const content = `# 🦀 AI 价值投资系统 - 推送测试

**测试时间：** ${new Date().toISOString()}

这是一条测试消息，验证 Cron 任务能否推送到钉钉。
`;

async function push() {
  try {
    const result = await sendProactive(config, { userId }, content, {
      msgType: "markdown",
      title: "AI 价值投资系统"
    });
    console.log("推送结果:", JSON.stringify(result, null, 2));
  } catch (err) {
    console.error("推送失败:", err.message);
    console.error(err.stack);
  }
}

push();
