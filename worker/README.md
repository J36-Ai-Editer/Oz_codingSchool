# 폐렴 예측 Worker

## 사용 모델

- 파일: `models/model_state_dict.pth`
- 구조: `SimpleCNN`
- 입력: 흑백 이미지 `1 x 128 x 128`
- 클래스: `0 = NORMAL`, `1 = PNEUMONIA`

`AH_05_compact_xray.ipynb`에서는 `0 = NORMAL`, `1 = PNEUMONIA`를 사용합니다. 다만 노트북의
ConvNeXt/EfficientNet 학습 체크포인트는 제공되지 않았기 때문에, 현재 worker는 과제와 함께 제공된
SimpleCNN state_dict를 사용합니다.

## 예측 흐름

1. worker 시작 시 모델 파일을 한 번만 읽어 메모리에 올립니다.
2. 입력 이미지를 흑백으로 변환하고 `128 x 128` 크기로 조정합니다.
3. 모델의 두 logits에 softmax를 적용합니다.
4. `NORMAL`, `PNEUMONIA` 확률과 가장 높은 클래스의 신뢰도를 반환합니다.

```python
from worker.model import predict_pneumonia

result = predict_pneumonia("sample_xray.png")
print(result.to_dict())
```

응답 예시 구조:

```python
{
    "class_index": 1,
    "label": "PNEUMONIA",
    "confidence": 0.91,
    "probabilities": {"NORMAL": 0.09, "PNEUMONIA": 0.91},
    "is_pneumonia": True,
}
```

## 팀 확인 사항

- 모델 학습 당시 별도의 정규화를 적용했다면 `PREPROCESS`에 같은 정규화를 추가해야 합니다.
- 현재 클래스 순서는 노트북과 일반적인 데이터셋 정의를 근거로 명시했습니다.
- 출력은 학습 모델의 예측 결과이며 의료진의 최종 진단을 대체하지 않습니다.

## 테스트

```bash
pip install -r worker/requirements.txt pytest
python -m pytest worker/tests/test_model.py -q
```
