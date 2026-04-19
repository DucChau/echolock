"""Sample application to demonstrate echolock tracing."""


def parse_input(raw: str) -> dict:
    """Simulate parsing raw input into a structured dict."""
    return {"raw": raw, "tokens": raw.split()}


def validate(data: dict) -> dict:
    """Validate parsed data."""
    if "tokens" not in data:
        raise ValueError("Missing tokens")
    data["valid"] = True
    return data


def enrich(data: dict) -> dict:
    """Enrich data with additional metadata."""
    data["token_count"] = len(data.get("tokens", []))
    data["has_numbers"] = any(t.isdigit() for t in data.get("tokens", []))
    return data


def transform(data: dict) -> dict:
    """Apply a transformation pass."""
    data["tokens"] = [t.lower() for t in data.get("tokens", [])]
    data["transformed"] = True
    return data


def score(data: dict) -> dict:
    """Compute a synthetic score."""
    data["score"] = data.get("token_count", 0) * 10
    if data.get("has_numbers"):
        data["score"] += 5
    return data


def emit(data: dict) -> dict:
    """Emit the processed result."""
    data["emitted"] = True
    return data


def run_pipeline() -> dict:
    """Run the full processing pipeline — this is the function to trace."""
    raw = "hello world 42 foo bar"
    data = parse_input(raw)
    data = validate(data)
    data = enrich(data)
    data = transform(data)
    data = score(data)
    data = emit(data)
    return data


if __name__ == "__main__":
    result = run_pipeline()
    print("Pipeline result:", result)
