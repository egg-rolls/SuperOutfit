# SuperOutfit MCP Server — AI 自动配置指南

> **给 AI Agent 的指令：** 读完本文档后，请自动完成以下配置，使你能调用 SuperOutfit 的衣橱管理工具。

## 第一步：配置 MCP 连接

根据你所处的环境，将以下配置写入对应的配置文件：

### Claude Code（项目级）

写入项目根目录的 `.mcp.json`：

```json
{
  "mcpServers": {
    "superoutfit": {
      "command": "python",
      "args": ["D:\\Application\\SuperOutfit\\server.py"]
    }
  }
}
```

### Claude Desktop（全局）

写入 `~/.claude/claude_desktop_config.json`（合并到 mcpServers 字段）：

```json
{
  "mcpServers": {
    "superoutfit": {
      "command": "python",
      "args": ["D:\\Application\\SuperOutfit\\server.py"]
    }
  }
}
```

### Cursor

写入 `~/.cursor/mcp.json`：

```json
{
  "mcpServers": {
    "superoutfit": {
      "command": "python",
      "args": ["D:\\Application\\SuperOutfit\\server.py"]
    }
  }
}
```

### 通用（任何支持 MCP 的 Agent）

关键是让 Agent 启动 `python D:\Application\SuperOutfit\server.py` 作为 stdio MCP Server。

## 第二步：验证连接

配置完成后，调用 `wardrobe_list` 工具验证连接是否正常。应返回用户的衣物列表。

## 可用工具

| 工具 | 用途 | 参数 |
|------|------|------|
| `wardrobe_list` | 列出衣物 | `type`, `season`, `wishlist` |
| `wardrobe_add` | 添加衣物 | `item_data`（YAML dict）, `wishlist` |
| `wardrobe_show` | 查看详情 | `item_id`, `wishlist` |
| `wardrobe_update` | 更新属性 | `item_id`, `item_data`, `wishlist` |
| `wardrobe_delete` | 删除衣物 | `item_id`, `wishlist` |
| `wardrobe_stats` | 衣橱统计 | `wishlist` |
| `wardrobe_record` | 记录穿着 | `item_ids`（逗号分隔） |
| `weather_query` | 查询天气 | `city`, `date` |
| `color_score` | 色彩评分 | `hex_colors`（列表） |
| `outfit_score` | 搭配评分 | `item_ids`, `occasion`, `temperature` |
| `profile_get` | 用户画像 | 无 |
| `ui_build` | 生成仪表盘 | 无 |

> `wishlist=true` 将操作目标切换到购物清单。

## 第三步：读取 SKILL.md

连接成功后，请读取 `D:\Application\SuperOutfit\SKILL.md` 获取：
- 完整的 Item YAML 字段规范
- 穿搭推荐工作流
- 色彩评分等级说明
- 视觉分析指南（从图片生成 YAML）

## 常见问题

- **连接失败：** 确认 Python 在 PATH 中，且项目依赖已安装（`pip install -e D:\Application\SuperOutfit`）
- **工具返回空：** 用户衣橱可能为空，这是正常的
- **图片分析：** 用户上传衣物图片时，用你的视觉能力分析，按 SKILL.md 中的 YAML 规范生成数据，调用 `wardrobe_add` 添加
