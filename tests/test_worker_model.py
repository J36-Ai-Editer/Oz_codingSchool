import math
import time

import pytest
from PIL import Image

from worker.model import (
    CLASS_NAMES,
    MODEL,
    InvalidImageError,
    predict_pneumonia,
    preprocess_image,
)


def make_test_image() -> Image.Image:
    return Image.new("L", (256, 256), color=128)


def test_preprocess_image_shape() -> None:
    tensor = preprocess_image(make_test_image())
    assert tensor.shape == (1, 1, 128, 128)


def test_predict_pneumonia_result() -> None:
    result = predict_pneumonia(make_test_image())

    assert result.label in CLASS_NAMES
    assert result.class_index in (0, 1)
    assert 0.0 <= result.confidence <= 1.0
    assert set(result.probabilities) == set(CLASS_NAMES)
    assert math.isclose(sum(result.probabilities.values()), 1.0, rel_tol=1e-5)
    assert result.is_pneumonia == (result.label == "PNEUMONIA")


def test_invalid_image_raises_error() -> None:
    with pytest.raises(InvalidImageError):
        predict_pneumonia(b"not-an-image")


def test_model_is_reused_between_predictions() -> None:
    model_id = id(MODEL)
    predict_pneumonia(make_test_image())
    predict_pneumonia(make_test_image())
    assert id(MODEL) == model_id


def test_inference_p95_is_under_three_seconds() -> None:
    image = make_test_image()
    for _ in range(3):
        predict_pneumonia(image)

    elapsed_times = []
    for _ in range(20):
        started_at = time.perf_counter()
        predict_pneumonia(image)
        elapsed_times.append(time.perf_counter() - started_at)

    sorted_times = sorted(elapsed_times)
    p95_index = max(0, math.ceil(len(sorted_times) * 0.95) - 1)
    average = sum(sorted_times) / len(sorted_times)
    p95 = sorted_times[p95_index]
    maximum = max(sorted_times)

    print(
        f"AI inference performance: average={average:.4f}s, "
        f"p95={p95:.4f}s, max={maximum:.4f}s"
    )
    assert p95 < 3.0
