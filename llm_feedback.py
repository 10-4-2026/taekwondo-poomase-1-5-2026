import requests
import json

PROVIDERS = {
    "OpenRouter": {
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "default_model": "openrouter/free"
    },
    "OpenAI": {
        "url": "https://api.openai.com/v1/chat/completions",
        "default_model": "gpt-4o"
    },
    "Google Gemini": {
        "url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "default_model": "gemini-1.5-flash"
    },
    "DeepSeek": {
        "url": "https://api.deepseek.com/chat/completions",
        "default_model": "deepseek-chat"
    },
    "Qwen": {
        "url": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
        "default_model": "qwen-plus"
    },
    "Nvidia": {
        "url": "https://integrate.api.nvidia.com/v1/chat/completions",
        "default_model": "meta/llama-3.1-70b-instruct"
    }
}

def get_llm_feedback(provider, api_key, model, metrics, overall_similarity):
    """
    Gửi dữ liệu phân tích tới LLM để nhận nhận xét và hướng dẫn.
    Hỗ trợ nhiều nhà cung cấp khác nhau.
    """
    if not api_key:
        return "Vui lòng cung cấp API KEY để nhận nhận xét từ AI."

    # Xác định cấu hình provider
    config = PROVIDERS.get(provider)
    if not config:
        return f"Nhà cung cấp {provider} chưa được hỗ trợ."

    url = config["url"]
    target_model = model if model else config["default_model"]

    # Chuẩn bị dữ liệu cho prompt
    joint_details = ""
    sorted_metrics = sorted(metrics.items(), key=lambda x: x[1]['JS_Distance'], reverse=True)
    
    for joint, data in sorted_metrics:
        js_dist = data['JS_Distance']
        if js_dist > 0.3:
            status = "Sai lệch lớn"
        elif js_dist > 0.15:
            status = "Sai lệch vừa"
        else:
            status = "Khá tốt"
        joint_details += f"- {joint}: {js_dist:.4f} ({status})\n"

    prompt = f"""Bạn là một chuyên gia võ thuật Taekwondo giàu kinh nghiệm. Bạn đang phân tích video thực hành Poomsae của một vận động viên so với video mẫu chuẩn.

Dưới đây là kết quả phân tích sự tương đồng giữa hai video:
- Độ tương đồng tổng thể: {overall_similarity:.2f}%
- Chi tiết sai lệch từng khớp (Chỉ số JS Distance - càng thấp càng tốt):
{joint_details}

Nhiệm vụ của bạn:
1. Đưa ra nhận xét tổng quan về bài thực hành (khích lệ vận động viên).
2. Chỉ ra 3-4 khớp quan trọng nhất cần cải thiện dựa trên dữ liệu sai lệch lớn.
3. Đưa ra các lời khuyên kỹ thuật cụ thể (ví dụ: "Cần mở rộng khớp vai hơn", "Lưu ý độ cao của gối", v.v.) để vận động viên có thể thực hiện giống với mẫu hơn.
4. Giọng văn chuyên nghiệp, mang tính xây dựng và dễ hiểu bằng tiếng Việt.

Hãy trình bày dưới dạng Markdown.
"""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # Một số provider có header đặc biệt
    if provider == "OpenRouter":
        headers["HTTP-Referer"] = "https://github.com/taekwondo-ai"
        headers["X-Title"] = "Taekwondo Poomsae Analysis"

    payload = {
        "model": target_model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
    }

    try:
        response = requests.post(url=url, headers=headers, data=json.dumps(payload))
        
        # Kiểm tra nếu response là JSON
        try:
            result = response.json()
        except:
            return f"Lỗi: Provider {provider} phản hồi không phải định dạng JSON. (Mã lỗi: {response.status_code})\nNội dung phản hồi: {response.text[:200]}"

        if response.status_code == 200:
            # Hầu hết các provider OpenAI-compatible đều dùng cấu trúc này
            if 'choices' in result and len(result['choices']) > 0:
                return result['choices'][0]['message']['content']
            else:
                return f"Lỗi: Phản hồi từ {provider} không có nội dung 'choices'. JSON: {json.dumps(result)}"
        else:
            # Xử lý các lỗi phổ biến từ JSON phản hồi
            error_msg = result.get('error', {}).get('message', response.text)
            return f"Lỗi từ {provider} ({response.status_code}): {error_msg}"
            
    except Exception as e:
        return f"Lỗi kết nối khi gọi LLM: {str(e)}"
