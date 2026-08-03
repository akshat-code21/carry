import concurrent.futures
from unittest.mock import MagicMock, patch

from src.services.finbert_service import FinBertService


def test_finbert_service_concurrent_loading_once():
    """Verify that multiple concurrent calls to _ensure_loaded load ONNX session only once."""
    # Reset class shared state for clean test isolation
    FinBertService._shared_session = None
    FinBertService._shared_tokenizer = None
    FinBertService._shared_loaded = False

    load_count = 0

    def mock_inference_session(*args, **kwargs):
        nonlocal load_count
        load_count += 1
        return MagicMock()

    with (
        patch("onnxruntime.InferenceSession", side_effect=mock_inference_session),
        patch("transformers.AutoTokenizer.from_pretrained", return_value=MagicMock()),
        patch("pathlib.Path.exists", return_value=True),
    ):
        services = [FinBertService() for _ in range(5)]

        def load_service(srv: FinBertService):
            srv._ensure_loaded()

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(load_service, srv) for srv in services]
            concurrent.futures.wait(futures)

        # Ensure model session was created EXACTLY ONCE despite 5 parallel threads
        assert load_count == 1, f"Expected 1 model load, got {load_count}"
        for srv in services:
            assert srv._loaded is True
            assert srv._session is not None
