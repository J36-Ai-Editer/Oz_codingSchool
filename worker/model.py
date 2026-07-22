from __future__ import annotations

from dataclasses import asdict, dataclass
from io import BytesIO
from pathlib import Path
from typing import BinaryIO

import torch
from PIL import Image, UnidentifiedImageError
from torch import Tensor, nn
from torchvision import transforms


IMAGE_SIZE = 128
CLASS_NAMES = ("NORMAL", "PNEUMONIA")
MODEL_PATH = Path(__file__).resolve().parent / "models" / "model_state_dict.pth"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class InvalidImageError(ValueError):
    """입력 파일을 이미지로 처리할 수 없을 때 발생하는 예외."""


class SimpleCNN(nn.Module):
    """제공된 state_dict와 동일한 2-class 흉부 X-ray 분류 모델."""

    def __init__(self) -> None:
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(1, 16, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2),
            nn.Conv2d(16, 32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2),
        )
        self.fc = nn.Sequential(
            nn.Flatten(),
            nn.Linear(32 * 32 * 32, len(CLASS_NAMES)),
        )

    def forward(self, images: Tensor) -> Tensor:
        return self.fc(self.conv(images))


@dataclass(frozen=True, slots=True)
class PredictionResult:
    class_index: int
    label: str
    confidence: float
    probabilities: dict[str, float]

    @property
    def is_pneumonia(self) -> bool:
        return self.label == "PNEUMONIA"

    def to_dict(self) -> dict[str, object]:
        result = asdict(self)
        result["is_pneumonia"] = self.is_pneumonia
        return result


PREPROCESS = transforms.Compose(
    [
        transforms.Grayscale(num_output_channels=1),
        transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
        transforms.ToTensor(),
    ]
)


def load_model(
    model_path: str | Path = MODEL_PATH,
    *,
    device: torch.device = DEVICE,
) -> SimpleCNN:
    """state_dict를 안전 모드로 불러와 평가 모드의 모델을 반환한다."""

    resolved_path = Path(model_path)
    if not resolved_path.is_file():
        raise FileNotFoundError(f"모델 파일을 찾을 수 없습니다: {resolved_path}")

    state_dict = torch.load(resolved_path, map_location="cpu", weights_only=True)
    if not isinstance(state_dict, dict):
        raise TypeError("state_dict 형식의 모델 파일이 필요합니다.")

    model = SimpleCNN()
    model.load_state_dict(state_dict, strict=True)
    model.to(device)
    model.eval()
    return model


def _open_image(image: str | Path | bytes | bytearray | BinaryIO | Image.Image) -> Image.Image:
    if isinstance(image, Image.Image):
        return image.copy()

    try:
        if isinstance(image, (str, Path)):
            with Image.open(image) as opened:
                return opened.copy()
        if isinstance(image, (bytes, bytearray)):
            with Image.open(BytesIO(image)) as opened:
                return opened.copy()
        if hasattr(image, "read"):
            with Image.open(image) as opened:
                return opened.copy()
    except (OSError, UnidentifiedImageError) as exc:
        raise InvalidImageError("올바른 흉부 X-ray 이미지가 아닙니다.") from exc

    raise TypeError("이미지 경로, bytes, 파일 객체 또는 PIL 이미지를 입력해주세요.")


def preprocess_image(
    image: str | Path | bytes | bytearray | BinaryIO | Image.Image,
) -> Tensor:
    """입력 이미지를 모델 입력 형식인 [1, 1, 128, 128] 텐서로 변환한다."""

    opened_image = _open_image(image)
    return PREPROCESS(opened_image).unsqueeze(0)


def predict_pneumonia(
    image: str | Path | bytes | bytearray | BinaryIO | Image.Image,
    *,
    model: SimpleCNN | None = None,
    device: torch.device = DEVICE,
) -> PredictionResult:
    """흉부 X-ray 이미지의 정상/폐렴 확률과 최종 분류를 반환한다."""

    active_model = model if model is not None else MODEL
    image_tensor = preprocess_image(image).to(device)

    with torch.inference_mode():
        logits = active_model(image_tensor)
        probabilities = torch.softmax(logits, dim=1)[0].cpu()

    class_index = int(torch.argmax(probabilities).item())
    probability_map = {
        class_name: float(probabilities[index].item())
        for index, class_name in enumerate(CLASS_NAMES)
    }
    return PredictionResult(
        class_index=class_index,
        label=CLASS_NAMES[class_index],
        confidence=probability_map[CLASS_NAMES[class_index]],
        probabilities=probability_map,
    )


# worker 프로세스 시작 시 한 번만 로딩해 요청마다 모델을 다시 읽지 않는다.
MODEL = load_model()
