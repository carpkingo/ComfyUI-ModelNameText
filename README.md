# ComfyUI-ModelNameText

把 ComfyUI 正在使用的**大模型(Checkpoint) / LoRA / VAE 名称**输出成文本(STRING),
用于直接接入「保存文本 / 写入文件名」等字符串字段。

## 节点

| 节点 | 作用 | 输出 |
|------|------|------|
| Model Name → Text (Checkpoint) | 把选中大模型的名称输出 | STRING |
| Model Name → Text (Diffusion / UNET) | 把选中 diffusion_models 里 UNET 模型的名称输出 | STRING |
| **UNET Loader + Name (联动)** | 加载 UNET 的同时输出模型名(替换 UNETLoader 用) | MODEL, STRING |
| **Checkpoint Loader + Name (联动)** | 加载 Checkpoint 的同时输出模型名(替换 CheckpointLoaderSimple 用) | MODEL, CLIP, VAE, STRING |
| LoRA Name → Text | 把选中 LoRA 名称输出 | STRING |
| VAE Name → Text | 把选中 VAE 名称输出 | STRING |

每个下拉节点都有 `include_extension` 开关:
- 关(默认):输出 `myModel`,不含扩展名;
- 开:输出 `myModel.safetensors`,保留扩展名。

## 联动用法(推荐)

不想每次手动选模型的话,直接把 **UNET Loader + Name (联动)** 替换原来的 UNETLoader:
模型只选一次,`name` 输出会自动带上所选模型名,连到保存文字字段即可,换模型时自动跟随。
同名 Checkpoint 节点同理。

```
UNET Loader + Name (联动) ── MODEL ──► ... (采样/解码等)
        │
        └────────── name ──► 保存文字/文件名
```

## 为什么默认是下拉框而不是自动读取

ComfyUI 底层(`comfy/sd.py` 的 `load_checkpoint_guess_config`、`load_diffusion_model`)返回的
`model/clip/vae` 对象**并不携带文件名**,所以任何节点都无法从 MODEL 接口自动拿回
模型名。本节点用下拉框列出 `models/checkpoints`(或 `loras`/`vae`/`diffusion_models`)里的文件名,
选项列表和对应的 `CheckpointLoaderSimple` / `UNETLoader` 完全一致——你加载时选哪个,这里就选哪个,
输出即该模型名。

## 安装

1. 把整个 `ComfyUI-ModelNameText` 文件夹复制到:
   `D:\ComfyUI-aki-v1.6\ComfyUI\custom_nodes\`
2. 重启 ComfyUI(或在前端点"刷新节点定义")。
3. 在节点面板搜索 **Model Name → Text**。

## 使用示例

```
CheckpointLoaderSimple ── MODEL ──► ... (采样/解码等)
        │
        └ (下拉选同一个模型)
Model Name → Text ── text ──► "Save Text to File" / 自定义保存节点的文件名/文字字段
```

## 文件

- `nodes.py` —— 节点逻辑
- `__init__.py` —— 注册节点到 ComfyUI
