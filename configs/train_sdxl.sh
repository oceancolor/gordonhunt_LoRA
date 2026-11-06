#!/usr/bin/env bash
# SDXL style LoRA — Phase A baseline. Run from Git Bash on Windows.
# Full rationale: docs/Gordon_Hunt_style_research_and_LoRA_plan.md (section 6/7)
#
# Prerequisites:
#   - Kohya sd-scripts installed, `accelerate` configured
#   - dataset/ prepared and `python tools/audit_dataset.py --root dataset` is clean
#   - put every image's .txt caption next to it; trigger word `glntwtr` first
#
# Configure via environment variables (recommended) or by editing the two
# defaults below. Nothing in this repo hardcodes a machine-specific path.
#   SD_SCRIPTS=/path/to/sd-scripts  BASE_MODEL=/path/to/base.safetensors  STEPS=1800 ./train_sdxl.sh

set -euo pipefail

# Resolve the checkout root automatically (pwd -W gives C:/... form on Git Bash)
ROOT="${ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && (pwd -W 2>/dev/null || pwd))}"
SD_SCRIPTS="${SD_SCRIPTS:-C:/path/to/sd-scripts}"                        # <-- edit
BASE_MODEL="${BASE_MODEL:-C:/path/to/models/sd_xl_base_1.0.safetensors}"  # <-- edit

# Turn the portable template into a local, absolute-path config (gitignored)
DATASET_TOML="$ROOT/configs/dataset_sdxl.local.toml"
sed "s|@PROJECT_ROOT@|$ROOT|g" "$ROOT/configs/dataset_sdxl.toml" > "$DATASET_TOML"

# Phase 1: SMOKE TEST. Set STEPS=40, confirm captions are actually loaded.
# Phase 2: full run. Set STEPS=1800.
STEPS="${STEPS:-40}"

cd "$SD_SCRIPTS"

accelerate launch --num_cpu_threads_per_process 8 sdxl_train_network.py \
  --pretrained_model_name_or_path="$BASE_MODEL" \
  --dataset_config="$DATASET_TOML" \
  --output_dir="$ROOT/output" \
  --output_name="glntwtr_sdxl_v1" \
  --logging_dir="$ROOT/output/logs" \
  --network_module=networks.lora \
  --network_dim=32 \
  --network_alpha=16 \
  --learning_rate=1e-4 \
  --text_encoder_lr=5e-5 \
  --optimizer_type="AdamW8bit" \
  --lr_scheduler="cosine_with_restarts" \
  --lr_warmup_steps=90 \
  --max_train_steps="$STEPS" \
  --train_batch_size=1 \
  --mixed_precision="bf16" \
  --gradient_checkpointing \
  --cache_latents --cache_latents_to_disk \
  --save_model_as=safetensors \
  --save_every_n_steps=200 \
  --sample_every_n_steps=200 \
  --sample_sampler="euler_a" \
  --sample_prompts="$ROOT/prompts/sample_prompts.txt" \
  --noise_offset=0.035 \
  --min_snr_gamma=5 \
  --seed=42

# Notes / deliberate omissions:
#  --cache_text_encoder_outputs  : INCOMPATIBLE with shuffle_caption + caption_dropout_rate.
#  --network_train_unet_only     : valid v2 ablation (SDXL dual text encoders).
#                                  If enabled, drop --text_encoder_lr.
#  --enable_random_flip (flip_aug): off in v1; a missed signature can be mirrored.
#  --min_snr_gamma / --noise_offset: A/B test both; noise_offset helps the
#                                  dark-ground / very-bright-glint luminance structure.
#
# 12 GB VRAM fallback: resolution 768 in dataset_sdxl.toml, fp8 base, batch 1.
# Always keep the SAME base checkpoint for training, sampling and evaluation.
