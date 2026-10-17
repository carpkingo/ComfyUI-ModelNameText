# -*- coding: utf-8 -*-
"""
ModelNameText nodes
===================
把 ComfyUI 正在使用的大模型(Checkpoint)、LoRA、VAE 的名称输出成 STRING 文本,
方便直接接入 "保存文本" / 写入 filename 等字符串字段。

原理说明:
ComfyUI 的 CheckpointLoaderSimple 等加载器返回的 model/clip/vae 对象在底层
(comfy/sd.py 的 load_checkpoint_guess_config) 并不会把文件名挂到模型对象上,
所以无法从 MODEL 接口自动取回名字。社区标准做法是:用下拉框列出模型目录里的
文件名(与加载器选择列表一致),把选中项作为文本输出。

用法:在界面上添加节点,下拉框里选择和 CheckpointLoaderSimple 相同的大模型,
把输出的 STRING 连到 "Save Text" / 自定义保存节点的文字字段即可。
"""
import os
import folder_paths


def _clean_name(filename):
    """去掉子目录前缀和扩展名,只保留模型纯名称。
    例: 'Krea2\\moodyXxx.safetensors' -> 'moodyXxx'
    """
    name = os.path.splitext(filename)[0]
    name = os.path.basename(name.replace("/", os.path.sep))
    return name


def _make_name_node(folder_key, category, label_on, label_off):
    """按模型目录生成一个 “文件名 → STRING” 节点类。

    folder_key: folder_paths 里的模型目录 key,如 checkpoints / loras / vae。
    """

    class ModelNameToTextNode:
        CATEGORY = category

        @classmethod
        def INPUT_TYPES(cls):
            names = folder_paths.get_filename_list(folder_key)
            if not names:
                names = ["(no files)"]
            return {
                "required": {
                    "filename": (names,),
                    "include_extension": (
                        "BOOLEAN",
                        {
                            "default": False,
                            "label_on": label_on,
                            "label_off": label_off,
                        },
                    ),
                }
            }

        RETURN_TYPES = ("STRING",)
        RETURN_NAMES = ("text",)
        FUNCTION = "get_name"
        OUTPUT_NODE = False
        IS_CHANGED = True  # 模型目录内容变化时刷新下拉选项

        def get_name(self, filename, include_extension):
            name = filename
            if not include_extension:
                name = os.path.splitext(name)[0]
            return (name,)

    return ModelNameToTextNode


# 三个节点:Checkpoint(大模型)、LoRA、VAE
CheckpointNameToText = _make_name_node(
    "checkpoints",
    "ModelNameText",
    "include .safetensors/.ckpt",
    "name only (no ext)",
)

LoRANameToText = _make_name_node(
    "loras",
    "ModelNameText",
    "include .safetensors",
    "name only (no ext)",
)

VAENameToText = _make_name_node(
    "vae",
    "ModelNameText",
    "include .pt/.safetensors",
    "name only (no ext)",
)

# UNET/Diffusion 模型:配合 UNETLoader 使用(diffusion_models 目录)
DiffusionModelNameToText = _make_name_node(
    "diffusion_models",
    "ModelNameText",
    "include .safetensors",
    "name only (no ext)",
)


# ============================================================
# 联动方案:加载器 + 名称输出 一体节点
# 只需要在加载器里选一次模型,名称与模型同时输出并自动跟随。
# 用法:用下面的节点替换默认的 UNETLoader / CheckpointLoaderSimple,
#       它的 "name" 输出直接连到保存文字字段即可。
# ============================================================
class UnetLoaderWithName:
    """UNET 加载器 + 输出所选模型名(联动)。"""

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "unet_name": (folder_paths.get_filename_list("diffusion_models"),),
                "weight_dtype": (
                    ["default", "fp8_e4m3fn", "fp8_e4m3fn_fast", "fp8_e5m2"],
                    {"advanced": True},
                ),
            }
        }

    RETURN_TYPES = ("MODEL", "STRING")
    RETURN_NAMES = ("MODEL", "name")
    FUNCTION = "load_unet"
    CATEGORY = "ModelNameText"

    def load_unet(self, unet_name, weight_dtype):
        import torch
        import comfy.sd

        model_options = {}
        if weight_dtype == "fp8_e4m3fn":
            model_options["dtype"] = torch.float8_e4m3fn
        elif weight_dtype == "fp8_e4m3fn_fast":
            model_options["dtype"] = torch.float8_e4m3fn
            model_options["fp8_optimizations"] = True
        elif weight_dtype == "fp8_e5m2":
            model_options["dtype"] = torch.float8_e5m2

        unet_path = folder_paths.get_full_path_or_raise("diffusion_models", unet_name)
        model = comfy.sd.load_diffusion_model(unet_path, model_options=model_options)
        name = _clean_name(unet_name)
        return (model, name)


class CheckpointLoaderSimpleWithName:
    """Checkpoint 加载器 + 输出所选模型名(联动)。"""

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "ckpt_name": (folder_paths.get_filename_list("checkpoints"),),
            }
        }

    RETURN_TYPES = ("MODEL", "CLIP", "VAE", "STRING")
    RETURN_NAMES = ("MODEL", "CLIP", "VAE", "name")
    FUNCTION = "load_checkpoint"
    CATEGORY = "ModelNameText"

    def load_checkpoint(self, ckpt_name):
        import comfy.sd

        ckpt_path = folder_paths.get_full_path_or_raise("checkpoints", ckpt_name)
        out = comfy.sd.load_checkpoint_guess_config(
            ckpt_path, output_vae=True, output_clip=True, output_clipvision=False
        )
        model, clip, vae, clipvision = out
        name = _clean_name(ckpt_name)
        return (model, clip, vae, name)


NODE_CLASS_MAPPINGS = {
    "CheckpointNameToText": CheckpointNameToText,
    "DiffusionModelNameToText": DiffusionModelNameToText,
    "LoRANameToText": LoRANameToText,
    "VAENameToText": VAENameToText,
    "UnetLoaderWithName": UnetLoaderWithName,
    "CheckpointLoaderSimpleWithName": CheckpointLoaderSimpleWithName,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "CheckpointNameToText": "Model Name → Text (Checkpoint)",
    "DiffusionModelNameToText": "Model Name → Text (Diffusion / UNET)",
    "LoRANameToText": "LoRA Name → Text",
    "VAENameToText": "VAE Name → Text",
    "UnetLoaderWithName": "UNET Loader + Name (联动)",
    "CheckpointLoaderSimpleWithName": "Checkpoint Loader + Name (联动)",
}
