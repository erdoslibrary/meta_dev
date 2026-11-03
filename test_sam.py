"""Modal GPU에서 SAM 3.1 가중치 접근과 이미지 추론을 시험한다.

실행: modal run test_sam.py [--photo 사진.jpg]
토큰: facebook/sam3.1 접근 승인을 받은 Hugging Face 토큰을 환경 변수 HF_TOKEN에 둔다.
"""
import os
from pathlib import Path

import modal

SAM3_COMMIT = "f1647e8d0c1d280991f4d1b7d974c2704537fe66"
PROMPTS = ["door", "chair", "table"]

image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("git")
    .pip_install(
        "torch==2.10.0",
        "torchvision",
        index_url="https://download.pytorch.org/whl/cu128",
    )
    .pip_install("setuptools<81", "einops", "pycocotools", "psutil")
    .run_commands(
        "git clone https://github.com/facebookresearch/sam3.git /sam3",
        f"git -C /sam3 checkout {SAM3_COMMIT}",
        "pip install -e /sam3",
    )
    .env({"HF_HOME": "/weights"})
)
app = modal.App("sam3-weights-test", image=image)
weights = modal.Volume.from_name("sam3-weights", create_if_missing=True)
hf_token = {"HF_TOKEN": os.environ["HF_TOKEN"]} if os.environ.get("HF_TOKEN") else {}


@app.function(
    gpu="T4",
    volumes={"/weights": weights},
    secrets=[modal.Secret.from_dict(hf_token)],
    timeout=1200,
)
def try_sam(photo: bytes | None = None) -> None:
    import io
    import time

    import torch
    from huggingface_hub import hf_hub_download
    from huggingface_hub.errors import GatedRepoError, RepositoryNotFoundError
    from PIL import Image
    from sam3.model.sam3_image_processor import Sam3Processor
    from sam3.model_builder import build_sam3_image_model

    print("GPU:", torch.cuda.get_device_name(0))

    try:
        started = time.time()
        checkpoint = hf_hub_download("facebook/sam3.1", "sam3.1_multiplex.pt")
        print(f"가중치 접근 성공: {time.time() - started:.0f}초")
    except (GatedRepoError, RepositoryNotFoundError) as error:
        print("가중치 접근 실패:", type(error).__name__)
        print("환경 구성은 정상입니다. facebook/sam3.1 승인과 HF_TOKEN을 확인하세요.")
        return

    model = build_sam3_image_model(checkpoint_path=checkpoint, load_from_HF=False)
    state = torch.load(checkpoint, map_location="cpu", weights_only=True)
    state = state.get("model", state)
    loaded = {key.replace("detector.", "") for key in state if "detector" in key}
    expected = set(model.state_dict())
    print(f"이미지 모델 키: 기대 {len(expected)}, 일치 {len(expected & loaded)}")

    source = io.BytesIO(photo) if photo else "/sam3/assets/images/test_image.jpg"
    picture = Image.open(source).convert("RGB")
    processor = Sam3Processor(model)
    state = processor.set_image(picture)
    print("이미지 크기:", picture.size)

    for prompt in PROMPTS:
        started = time.time()
        output = processor.set_text_prompt(state=state, prompt=prompt)
        boxes, scores = output["boxes"], output["scores"]
        print(
            f"{prompt}: {len(boxes)}개, {time.time() - started:.2f}초, "
            f"점수 {[round(s, 2) for s in scores.tolist()[:3]]}, "
            f"박스 {[[round(v) for v in b] for b in boxes.tolist()[:3]]}, "
            f"마스크 {tuple(output['masks'].shape)}"
        )
    print(f"최대 VRAM: {torch.cuda.max_memory_allocated() / 2**30:.1f}GiB")


@app.local_entrypoint()
def main(photo: str = ""):
    try_sam.remote(Path(photo).read_bytes() if photo else None)
