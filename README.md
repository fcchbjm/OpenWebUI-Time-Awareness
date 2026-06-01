# Open-WebUI-Time-Awareness-Filter

为 Open WebUI 中的任意大模型注入**当前日期与时间**上下文。零配置、即装即用，专为 **Ollama 本地小模型**（如 qwen3:0.6b）优化——无需 Function Calling，无需修改 System Prompt。

---

## 核心功能

1. **自动注入当前时间**  
   在每条用户消息发送给模型之前，自动在消息开头 prepend 当前系统时间与星期。  
   就像给模型戴上一块「隐形手表」，让它始终知道「现在是几点、今天星期几」。

2. **小模型友好**  
   时间信息注入到 **user 消息** 而非 system 消息。实测 qwen3:0.6b、gemma、llama 等本地小模型，在注入后均可正确回答「今天几号」「星期几」等问题。

3. **零外部依赖**  
   不调用外部 API，不依赖 Function Calling，不依赖 Open WebUI 的 `{{CURRENT_DATE}}` 变量配置。  
   Admin 面板粘贴代码 → 启用 Global → 立即对所有模型生效。

4. **极低 Token 开销**  
   默认仅注入**最新一条**用户消息，每轮约增加 15~20 token，几乎可忽略。

5. **灵活可配置**  
   支持 IANA 时区、ISO8601 格式、中英文星期、自定义注入模板，Admin 面板 Valves 可视化配置。

6. **多模态消息支持**  
   纯图片、图文混合消息均可注入：无 text 块时在 content 数组头部插入时间文本，有 text 块时 prepend 到文本，**不破坏图片结构**。

7. **防重复注入**  
   多轮对话不会反复改写历史消息，内置前缀检测，避免上下文污染。

8. **状态栏反馈**  
   注入成功后，聊天界面状态栏显示当前注入的时间摘要，方便确认插件是否正常工作。

---

## 效果示例

**用户输入：**

```
今天星期几？
```

**实际发送给模型的内容：**

```
[时间上下文]
当前系统时间：2026-06-01 15:30:21（Asia/Shanghai）
星期：星期一

今天星期几？
```

**模型回复：**

```
今天是星期一。
```

---

## 使用方法

### 方式一：从 GitHub 复制导入（推荐）

1. 打开本仓库中的 [`function`](./function) 文件
2. 全选复制全部代码
3. 进入 Open WebUI → **管理面板 → Functions → +** 创建新函数
4. 类型选择 **Filter**，粘贴代码
5. 保存并**启用**该 Filter
6. 点击函数右侧 **⋮ → 地球图标（Globe）**，设为 **Global**（全局对所有模型生效）

### 方式二：Open WebUI 社区导入

> 发布到 [openwebui.com](https://openwebui.com) 后，可在此处补充社区链接，一键导入。

---

## 配置说明（Valves）

在 **管理面板 → Functions → 时间感知 Filter → 齿轮图标** 中可调整：

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `enabled` | `true` | 【总开关】启用/禁用本插件 |
| `timezone` | `Asia/Shanghai` | 【时区】IANA 时区名称，如 `Asia/Shanghai`、`UTC` |
| `include_weekday` | `true` | 【星期】是否包含星期信息 |
| `weekday_language` | `zh` | 【星期语言】`zh`=星期一，`en`=Monday |
| `use_iso8601` | `false` | 【ISO8601】标准格式 `2026-06-01T15:30:21+08:00` |
| `inject_last_message_only` | `true` | 【推荐】仅注入最新用户消息 |
| `template` | `当前系统时间：{time}（{timezone}）` | 【模板】自定义注入格式 |
| `show_injection_status` | `true` | 【状态提示】聊天栏显示注入摘要 |
| `priority` | `0` | 【优先级】与其他 Filter 联用时的执行顺序 |

### 模板占位符

| 占位符 | 示例 |
|--------|------|
| `{time}` | `2026-06-01 15:30:21` 或 ISO8601 |
| `{datetime}` | `2026-06-01 15:30:21` |
| `{iso_time}` | `2026-06-01T15:30:21+08:00` |
| `{timezone}` | `Asia/Shanghai` |
| `{weekday}` | `星期一` / `Monday` |

### 模板示例

**简洁英文（适合英文模型）：**

```
Current system time: {time} ({timezone}).
```

**XML 标签（适合结构化 prompt）：**

```
<system_time>{iso_time}</system_time>
<timezone>{timezone}</timezone>
<weekday>{weekday}</weekday>
```

---

## 与 Open WebUI 官方方案对比

Open WebUI 官方提供 `{{CURRENT_DATE}}`、`{{CURRENT_TIME}}` 等变量，详见 [Temporal Awareness 文档](https://docs.openwebui.com/features/chat-conversations/chat-features/temporal-awareness/)。

| 场景 | 推荐方案 |
|------|----------|
| Ollama 小模型，未配置 System Prompt | **本 Filter** |
| 模型忽略 system 消息中的时间变量 | **本 Filter** |
| 不想给每个 Model 单独写 Prompt | **本 Filter** |
| 已在 Model System Prompt 配置 `{{CURRENT_DATE}}` | 官方变量 |
| 复杂时间计算（「上周二我写了什么」） | Native Tool Calling |

> 官方变量需要**手动写入** System Prompt 才会生效；本 Filter **Global 启用后自动对所有模型生效**，无需逐个配置。

---

## 依赖说明

| 环境 | 说明 |
|------|------|
| Docker 版 Open WebUI | `pytz` 已内置，无需额外安装 |
| 手动安装 | 运行 `pip install pytz` |
| Open WebUI 版本 | >= 0.5.0 |

---

## 兼容模型

已验证可用（欢迎补充 Issue）：

- qwen3:0.6b / qwen3:1.7b
- gemma / llama / mistral 系列（Ollama）
- 任意 OpenAI 兼容 API 模型

---

## 相关项目

| 项目 | 特点 |
|------|------|
| [Super-Memory-for-openwebui](https://github.com/Fino-wind/Super-Memory-for-openwebui/) | 超级记忆助手，记忆时间戳 + 后台摘要 |
| [CookSleep/Time-Awareness-Filter-for-Open-WebUI](https://github.com/CookSleep/Time-Awareness-Filter-for-Open-WebUI) | 全功能时间 Filter，多用户时区 + API |
| [fractuscontext/openwebui-filters](https://github.com/fractuscontext/openwebui-filters) | 上下文裁剪 + 历史时间戳 |

本项目定位：**极简、零 API、专为小模型优化**。

---

## 常见问题

**Q：纯图片消息能注入时间吗？**  
A：可以。Filter 会在 content 数组最前面插入一条 text 块（如 `[时间上下文]\n当前系统时间：...`），模型会同时看到时间与图片。

**Q：注入的时间会显示在用户界面的消息里吗？**  
A：Open WebUI 可能展示注入后的完整消息内容，这是 Filter 的正常行为，模型需要看到时间上下文才能正确回答。

**Q：和 System Prompt 里写 `{{CURRENT_DATE}}` 冲突吗？**  
A：不冲突，但通常二选一即可。若已配置官方变量且效果满意，可关闭本 Filter。

**Q：时区不对怎么办？**  
A：在 Valves 中将 `timezone` 改为你的 IANA 时区，如 `Asia/Shanghai`。

**Q：如何确认 Filter 已生效？**  
A：开启 `show_injection_status` 后，发送消息时状态栏会显示 `🕐 时间感知：...`；或直接问模型「现在几点」。

---

## 许可证

MIT — 见 [LICENSE](./LICENSE)
