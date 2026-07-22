from io import BytesIO

import pytest
import torch
from PIL import Image

from worker.model import (
    CLASS_NAMES,
    IMAGE_SIZE,
    InvalidImageError,
    SimpleCNN,
    load_model,
    predict_pneumonia,
    preprocess_image,
)


def make_png_bytes(mode: str = "RGB") -> bytes:
    image = Image.new(mode, (80, 160), color=128)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_load_model_uses_expected_architecture() -> None:
    model = load_model(device=torch.device("cpu"))
    output = model(torch.zeros(1, 1, IMAGE_SIZE, IMAGE_SIZE))

    assert isinstance(model, SimpleCNN)
    assert model.training is False
    assert output.shape == (1, len(CLASS_NAMES))


def test_preprocess_converts_image_to_grayscale_tensor() -> None:
    image_tensor = preprocess_image(make_png_bytes())

    assert image_tensor.shape == (1, 1, IMAGE_SIZE, IMAGE_SIZE)
    assert image_tensor.dtype == torch.float32
    assert 0.0 <= image_tensor.min().item() <= image_tensor.max().item() <= 1.0


def test_predict_returns_two_probabilities() -> None:
    result = predict_pneumonia(make_png_bytes(), device=torch.device("cpu"))

    assert result.label in CLASS_NAMES
    assert result.class_index in (0, 1)
    assert result.confidence == result.probabilities[result.label]
    assert set(result.probabilities) == set(CLASS_NAMES)
    assert sum(result.probabilities.values()) == pytest.approx(1.0)
    assert result.to_dict()["is_pneumonia"] == (result.label == "PNEUMONIA")


def test_invalid_image_is_rejected() -> None:
    with pytest.raises(InvalidImageError):
        predict_pneumonia(b"not-an-image")
