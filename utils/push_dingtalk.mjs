#!/usr/bin/env node
/**
 * 钉钉推送 - 使用钉钉连接器内部 API
 */

import { sendProactive } from './extensions/dingtalk-connector/src/services/messaging.ts';

const config = {
  clientId: "dinggmk7kpiddrrvi0l5",
  clientSecret: "9RR-37dNLUKRkzzS-1RN5CHsDSJnIKEtBCd3-O9MqB7SvYUduBwse8FhEtMnr2bN",
  gatewayToken: "7c945e183e33b18df341e2c3ad9ced59e0a7f156d7d20238"
};

const userId = "01023647151178899";
const content = "# 测试\n\n这是一条测试消息";

async function push() {
  try {
    const result = await sendProactive(config, { userId }, content, {
      msgType: "markdown",
      title: "AI 价值投资系统"
    });
    console.log("推送结果:", result);
  } catch (err) {
    console.error("推送失败:", err.message);
  }
}

push();
