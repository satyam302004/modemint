from flask import Blueprint, jsonify, request

from ..services.openai_service import ask_openai_chatbot, build_local_chat_response

from ..config import DEFAULT_OPENAI_MODEL

chat_bp = Blueprint("chat", __name__)

@chat_bp.route("/chat", methods=["POST"])
def chat() -> Any:
    payload = request.get_json(silent=True) or {}
    message = str(payload.get("message", "")).strip()
    if not message:
        return jsonify({"error": "Message is required"}), 400

    try:
        response_text = ask_openai_chatbot(message)
    except Exception as error:
        response_text = build_local_chat_response(message)
        return jsonify(
            {
                "response": response_text,
                "model": "local-fallback",
                "warning": str(error),
            }
        )

    from backend.config import DEFAULT_OPENAI_MODEL
    return jsonify(
        {
            "response": response_text or "I could not generate a response right now.",
            "model": DEFAULT_OPENAI_MODEL,
        }
    )