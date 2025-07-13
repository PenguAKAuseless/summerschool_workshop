from data.milvus.indexing import MilvusIndexer
import os
import re
import json

from llm.base import AgentClient
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider

from data.cache.memory_handler import MessageMemoryHandler
from config.system_prompts import get_enhanced_system_prompt

import chainlit as cl

from utils.basetools import *

class QnAHandlerAgent(AgentClient):
    def __init__(self, collection_name: str):
        # Only run indexer if collection doesn't exist
        from pymilvus import utility
        if not utility.has_collection(collection_name):
            # Initialize Milvus indexer (run only once to create collection and index data)
            indexer = MilvusIndexer(collection_name=collection_name, faq_file="src/data/mock_data/vnu_hcmut_faq.xlsx")
            indexer.run()

        provider = GoogleGLAProvider(api_key=os.getenv("GEMINI_API_KEY"))
        model = GeminiModel('gemini-2.0-flash', provider=provider)

        # Initialize your tools
        #---------------------------------------------
        faq_tool = create_faq_tool(collection_name=collection_name)
        
        # Calculator tools for computational capabilities
        from utils.basetools.calculator_tool import (
            calculate_expression, basic_math, trigonometry, 
            logarithm, calculator_memory
        )
        calculator_tools = [
            calculate_expression,
            basic_math,
            trigonometry,
            logarithm,
            calculator_memory
        ]
        #---------------------------------------------

        specific_role = """Bạn là trợ lý ảo thông minh và có khả năng tính toán của VNU-HCMUT, có nhiệm vụ trả lời câu hỏi của sinh viên dựa trên cơ sở dữ liệu FAQ về quy định và chính sách của trường.

NHIỆM VỤ CỤ THỂ:
- Trả lời các câu hỏi về quy định học vụ của trường
- Cung cấp thông tin về chính sách và thủ tục
- Hướng dẫn sinh viên về các dịch vụ của trường
- Sử dụng cơ sở dữ liệu FAQ để tìm câu trả lời chính xác
- TÍNH TOÁN THÔNG MINH: Khi phát hiện thông tin có công thức (điểm xét tuyển, GPA, học bổng), tự động thực hiện tính toán cho sinh viên

TÍNH NĂNG TÍNH TOÁN:
- Phát hiện công thức trong dữ liệu (điểm tổng hợp, GPA, điều kiện học bổng, v.v.)
- Thu thập thông tin đầu vào từ sinh viên (điểm số, tín chỉ, môn học)
- Tính toán tự động và đưa ra kết quả cụ thể
- Giải thích quá trình tính toán một cách rõ ràng

CÔNG CỤ SỬ DỤNG:
- faq_tool để tìm kiếm trong cơ sở dữ liệu FAQ của trường
- calculate_expression để thực hiện các phép tính toán
- basic_math cho các phép tính cơ bản
- trigonometry, logarithm cho các phép tính phức tạp (nếu cần)

QUY TRÌNH TÍNH TOÁN:
1. Khi phát hiện công thức trong dữ liệu:
   - Xác định loại tính toán cần thiết
   - Thu thập thông tin đầu vào từ sinh viên (hỏi một cách tự nhiên)
   - Thực hiện tính toán bằng công cụ phù hợp
   - Trình bày kết quả với giải thích chi tiết

VÍ DỤ TÌNH HUỐNG:
- Sinh viên hỏi: "Điểm này có đủ điều kiện vào BK không?" → Tìm công thức điểm xét tuyển → Hỏi điểm các môn → Tính toán điểm tổng hợp
- Sinh viên hỏi: "GPA kỳ này là bao nhiêu?" → Hỏi điểm và tín chỉ các môn → Tính GPA
- Sinh viên hỏi: "Có đủ điều kiện học bổng không?" → Tìm điều kiện học bổng → Tính GPA → So sánh với tiêu chuẩn

LƯU Ý:
- Chỉ trả lời dựa trên thông tin có trong cơ sở dữ liệu FAQ
- Không tự suy luận thông tin không có trong dữ liệu
- Khi cần thông tin để tính toán, hỏi sinh viên một cách tự nhiên
- Nếu không tìm thấy thông tin, hướng dẫn sinh viên liên hệ phòng ban phù hợp
- Luôn kiểm tra tính hợp lý của kết quả tính toán
- Giải thích rõ ràng quá trình tính toán để sinh viên hiểu"""

        enhanced_prompt = get_enhanced_system_prompt(specific_role)

        # Combine all tools (import them as functions, not as classes/instances)
        all_tools = [faq_tool] + calculator_tools

        self.agent = AgentClient(
            model=model,
            system_prompt=enhanced_prompt,
            tools=all_tools
        ).create_agent()

        # Initialize SearchHandler for fallback
        from .SearchHandler import SearchHandlerAgent
        self.search_handler = SearchHandlerAgent()

    def _has_computational_content(self, text: str) -> dict:
        """
        Analyze text to detect computational content and formulas.
        Returns detailed information about what type of computation is needed.
        """
        computation_patterns = {
            'gpa_calculation': {
                'keywords': ['gpa', 'điểm trung bình', 'dtb', 'trung bình học kỳ', 'trung bình tích lũy'],
                'formulas': ['(điểm × tín chỉ)', 'tổng tín chỉ', 'weighted average'],
                'needs_input': ['điểm các môn', 'số tín chỉ'],
                'description': 'Tính điểm trung bình học kỳ hoặc tích lũy'
            },
            'admission_score': {
                'keywords': ['điểm xét tuyển', 'tổng hợp', 'điểm đầu vào', 'điểm chuẩn'],
                'formulas': ['điểm thi × hệ số', 'điểm học bạ × hệ số', 'ưu tiên khu vực'],
                'needs_input': ['điểm thi đại học', 'điểm học bạ', 'khu vực'],
                'description': 'Tính điểm xét tuyển đại học'
            },
            'scholarship_eligibility': {
                'keywords': ['học bổng', 'khuyến khích', 'học lực', 'điều kiện'],
                'formulas': ['gpa >= ngưỡng', 'rèn luyện >= điểm'],
                'needs_input': ['gpa hiện tại', 'điểm rèn luyện'],
                'description': 'Kiểm tra điều kiện học bổng'
            },
            'credit_calculation': {
                'keywords': ['tín chỉ', 'đăng ký học', 'khối lượng', 'tính tín chỉ'],
                'formulas': ['tổng tín chỉ', 'tín chỉ tối đa', 'tín chỉ tối thiểu'],
                'needs_input': ['số môn học', 'tín chỉ từng môn'],
                'description': 'Tính toán tín chỉ học tập'
            },
            'tuition_calculation': {
                'keywords': ['học phí', 'chi phí', 'tiền học', 'đóng học phí'],
                'formulas': ['tín chỉ × đơn giá', 'phí dịch vụ'],
                'needs_input': ['số tín chỉ đăng ký', 'mức phí'],
                'description': 'Tính toán học phí'
            }
        }
        
        text_lower = text.lower()
        detected_computations = []
        
        for comp_type, patterns in computation_patterns.items():
            # Check for keywords
            keyword_matches = sum(1 for keyword in patterns['keywords'] if keyword in text_lower)
            
            # Check for formula patterns
            formula_matches = sum(1 for formula in patterns['formulas'] if any(word in text_lower for word in formula.split()))
            
            if keyword_matches > 0 or formula_matches > 0:
                confidence = min(1.0, (keyword_matches + formula_matches) / (len(patterns['keywords']) + len(patterns['formulas'])))
                detected_computations.append({
                    'type': comp_type,
                    'confidence': confidence,
                    'description': patterns['description'],
                    'needs_input': patterns['needs_input'],
                    'keyword_matches': keyword_matches,
                    'formula_matches': formula_matches
                })
        
        # Sort by confidence
        detected_computations.sort(key=lambda x: x['confidence'], reverse=True)
        
        return {
            'has_computation': len(detected_computations) > 0,
            'computations': detected_computations,
            'primary_computation': detected_computations[0] if detected_computations else None
        }

    def _generate_computation_prompt(self, computation_info: dict, query: str) -> str:
        """
        Generate a follow-up prompt to collect necessary information for computation.
        """
        if not computation_info['has_computation']:
            return ""
        
        primary = computation_info['primary_computation']
        comp_type = primary['type']
        
        prompts = {
            'gpa_calculation': """
Tôi tìm thấy thông tin về cách tính GPA trong cơ sở dữ liệu. Để tính chính xác cho bạn, tôi cần:

📊 **Thông tin cần thiết:**
• Điểm số từng môn học
• Số tín chỉ của từng môn

📝 **Cách nhập:** 
Vui lòng cho tôi biết theo định dạng:
- Môn 1: [điểm] điểm, [số tín chỉ] tín chỉ
- Môn 2: [điểm] điểm, [số tín chỉ] tín chỉ

Ví dụ: "Toán cao cấp: 8.5 điểm, 4 tín chỉ"
""",
            'admission_score': """
Tôi tìm thấy công thức tính điểm xét tuyển trong cơ sở dữ liệu. Để tính cho bạn:

📊 **Thông tin cần thiết:**
• Điểm thi đại học các môn
• Điểm học bạ THPT (nếu xét học bạ)
• Khu vực (K1, K2, K3) và đối tượng ưu tiên

📝 **Vui lòng cung cấp:**
- Điểm thi các môn: Toán, Lý, Hóa (hoặc tổ hợp khác)
- Khu vực của bạn
""",
            'scholarship_eligibility': """
Tôi tìm thấy điều kiện học bổng trong cơ sở dữ liệu. Để kiểm tra cho bạn:

📊 **Thông tin cần thiết:**
• GPA hiện tại (hoặc điểm các môn để tính GPA)
• Điểm rèn luyện
• Loại học bổng bạn quan tâm

📝 **Vui lòng cho biết:**
- GPA học kỳ gần nhất
- Điểm rèn luyện (nếu có)
""",
            'credit_calculation': """
Tôi tìm thấy quy định về tín chỉ. Để tính toán cho bạn:

📊 **Thông tin cần thiết:**
• Danh sách môn học dự định đăng ký
• Số tín chỉ từng môn

📝 **Vui lòng liệt kê:**
- Các môn học và số tín chỉ tương ứng
""",
            'tuition_calculation': """
Tôi tìm thấy thông tin về học phí. Để tính toán chi phí:

📊 **Thông tin cần thiết:**
• Số tín chỉ đăng ký trong kỳ
• Ngành học/chương trình đào tạo

📝 **Vui lòng cho biết:**
- Tổng số tín chỉ dự định đăng ký
- Ngành học của bạn
"""
        }
        
        return prompts.get(comp_type, "Tôi cần thêm thông tin để thực hiện tính toán cho bạn.")

    def _evaluate_search_quality(self, results: list, query: str) -> bool:
        """
        Evaluate the quality of Milvus search results to determine if SearchHandler should be called.
        Returns True if results are good quality, False if SearchHandler should be used.
        """
        if not results:
            return False
        
        # Check similarity scores (assuming they're in the results)
        min_similarity_threshold = 0.7  # Adjust based on your needs
        good_results_count = 0
        
        for result in results:
            # Check if result has good similarity score
            # Note: Milvus typically returns distance (lower is better) or score (higher is better)
            if 'distance' in result:
                # For distance, lower values mean better similarity
                if result['distance'] < (1.0 - min_similarity_threshold):
                    good_results_count += 1
            elif 'score' in result:
                # For score, higher values mean better similarity  
                if result['score'] > min_similarity_threshold:
                    good_results_count += 1
                    
        # If we have at least 1 good result, consider it acceptable
        if good_results_count > 0:
            return True
                
        # If no good similarity scores, check content relevance
        query_keywords = set(query.lower().split())
        for result in results:
            result_text = ""
            
            # Combine question and answer text for evaluation
            if 'question' in result:
                result_text += result['question'].lower() + " "
            if 'answer' in result:
                result_text += result['answer'].lower() + " "
                
            if result_text:
                result_words = set(result_text.split())
                # Check if at least 40% of query keywords are in the result
                matching_keywords = len(query_keywords.intersection(result_words))
                if matching_keywords >= len(query_keywords) * 0.4:
                    return True
                    
        return False

    def _generate_suggestions(self, query: str) -> str:
        """
        Generate contextual suggestions based on the query content.
        """
        query_lower = query.lower()
        suggestions = []
        
        # Academic-related queries
        if any(keyword in query_lower for keyword in ['học phí', 'tiền', 'chi phí', 'học bổng']):
            suggestions.extend([
                "• Thông tin học phí các khóa học hiện tại",
                "• Chính sách học bổng và hỗ trợ tài chính",
                "• Hướng dẫn đóng học phí và các khoản phí"
            ])
            
        if any(keyword in query_lower for keyword in ['điểm', 'thi', 'kiểm tra', 'tốt nghiệp']):
            suggestions.extend([
                "• Quy chế thi và kiểm tra",
                "• Điều kiện tốt nghiệp",
                "• Cách tính điểm trung bình"
            ])
            
        if any(keyword in query_lower for keyword in ['đăng ký', 'môn học', 'lịch học']):
            suggestions.extend([
                "• Hướng dẫn đăng ký môn học",
                "• Lịch học và thời khóa biểu",
                "• Quy định về việc hủy/thêm môn học"
            ])
            
        if any(keyword in query_lower for keyword in ['thủ tục', 'giấy tờ', 'xác nhận']):
            suggestions.extend([
                "• Các loại giấy tờ xác nhận sinh viên",
                "• Thủ tục xin nghỉ học tạm thời",
                "• Quy trình làm bằng cấp"
            ])
            
        if any(keyword in query_lower for keyword in ['ký túc xá', 'ktx', 'chỗ ở']):
            suggestions.extend([
                "• Thông tin về ký túc xá",
                "• Quy định nội trú",
                "• Đăng ký chỗ ở"
            ])
            
        if any(keyword in query_lower for keyword in ['tuyển sinh', 'nhập học', 'xét tuyển']):
            suggestions.extend([
                "• Thông tin tuyển sinh mới nhất",
                "• Điều kiện xét tuyển",
                "• Hồ sơ nhập học"
            ])
            
        # Default suggestions if no specific category matches
        if not suggestions:
            suggestions = [
                "• Quy định học vụ và đào tạo",
                "• Thông tin về các dịch vụ sinh viên", 
                "• Liên hệ phòng ban chuyên môn để được hỗ trợ"
            ]
            
        return "\n".join(suggestions)

    def _is_university_related(self, query: str) -> bool:
        """Check if query is related to HCMUT"""
        query_lower = query.lower()
        
        # University-related keywords
        university_keywords = [
            'hcmut', 'bách khoa', 'bach khoa', 'vnu-hcmut', 'đhqg', 'dhqg',
            'trường đại học', 'truong dai hoc', 'sinh viên', 'sinh vien',
            'học phí', 'hoc phi', 'tuyển sinh', 'tuyen sinh', 'đào tạo', 'dao tao',
            'môn học', 'mon hoc', 'khoa', 'bộ môn', 'bo mon', 'giảng viên', 'giang vien',
            'thủ tục', 'thu tuc', 'học vụ', 'hoc vu', 'ký túc xá', 'ky tuc xa',
            'thư viện', 'thu vien', 'cơ sở vật chất', 'co so vat chat',
            'chương trình', 'chuong trinh', 'ngành học', 'nganh hoc',
            'điểm', 'diem', 'thi', 'kiểm tra', 'kiem tra', 'tốt nghiệp', 'tot nghiep',
            'đăng ký', 'dang ky', 'lịch học', 'lich hoc', 'thời khóa biểu', 'thoi khoa bieu',
            'gpa', 'học bổng', 'hoc bong'
        ]
        
        # Check if any university keyword is present
        for keyword in university_keywords:
            if keyword in query_lower:
                return True
                
        return False

    async def run(self, query: str):
        """Run the enhanced QnA handler agent with computational capabilities."""
        try:
            # First validate if query is related to HCMUT
            if not self._is_university_related(query):
                return """Xin lỗi, tôi chỉ có thể hỗ trợ các vấn đề liên quan đến Trường Đại học Bách Khoa - ĐHQG-HCM. 

Tôi có thể giúp bạn về:
• Quy định học vụ và đào tạo
• Thủ tục hành chính sinh viên  
• Thông tin tuyển sinh và chương trình học
• Dịch vụ sinh viên (học bổng, ký túc xá, thư viện)
• Cơ sở vật chất và tiện ích của trường
• Các hoạt động và sự kiện của trường
• **Tính toán GPA, điểm xét tuyển, học bổng**

Bạn có câu hỏi gì về trường Bách Khoa không?"""

            # First, try to get results from Milvus via the agent
            response = await self.agent.run(query)
            
            # Extract search results from the response to evaluate quality
            # We need to perform a direct search to evaluate the results
            faq_tool_instance = create_faq_tool(collection_name="summerschool_workshop")
            search_input = FAQInput(query=query, limit=5, search_answers=False)
            search_results = faq_tool_instance(search_input)
            
            # Check if the response contains computational content
            combined_text = query + " " + str(response)
            computation_info = self._has_computational_content(combined_text)
            
            # If computational content is detected, enhance the response
            if computation_info['has_computation']:
                primary_comp = computation_info['primary_computation']
                
                # Add computational guidance to the response
                enhanced_response = f"""🔍 **Thông tin từ cơ sở dữ liệu FAQ:**
{response}

🧮 **Phát hiện yêu cầu tính toán:** {primary_comp['description']}

{self._generate_computation_prompt(computation_info, query)}

💡 **Sau khi bạn cung cấp thông tin, tôi sẽ tính toán cụ thể và đưa ra kết quả chính xác cho bạn.**"""
                
                return enhanced_response
            
            # Evaluate if the Milvus results are good enough
            elif not self._evaluate_search_quality(search_results.results, query):
                # If Milvus results are not good, use SearchHandler
                print(f"Milvus results insufficient for query: {query}. Using SearchHandler.")
                
                # Call SearchHandler for better results
                search_response = await self.search_handler.run(query)
                
                # Check if search results contain computational content
                search_computation_info = self._has_computational_content(search_response)
                
                if search_computation_info['has_computation']:
                    primary_comp = search_computation_info['primary_computation']
                    enhanced_response = f"""🔍 **Tìm kiếm trong cơ sở dữ liệu FAQ**
Tôi không tìm thấy thông tin rõ ràng trong cơ sở dữ liệu FAQ của trường về câu hỏi này.

🌐 **Kết quả tìm kiếm mở rộng:**
{search_response}

🧮 **Phát hiện yêu cầu tính toán:** {primary_comp['description']}

{self._generate_computation_prompt(search_computation_info, query)}

💡 **Sau khi bạn cung cấp thông tin, tôi sẽ tính toán cụ thể và đưa ra kết quả chính xác cho bạn.**"""
                    
                    return enhanced_response
                
                # Generate contextual suggestions based on query content
                suggestions = self._generate_suggestions(query)
                
                # Combine Milvus results (if any) with search results
                combined_response = f"""
🔍 **Tìm kiếm trong cơ sở dữ liệu FAQ**
Tôi không tìm thấy thông tin rõ ràng trong cơ sở dữ liệu FAQ của trường về câu hỏi này.

🌐 **Kết quả tìm kiếm mở rộng:**
{search_response}

💡 **Gợi ý thông tin có thể hữu ích:**
{suggestions}

📞 **Hỗ trợ trực tiếp:**
Nếu cần hỗ trợ cụ thể hơn, vui lòng liên hệ:
- Phòng Đào tạo: để biết thông tin về học vụ, chương trình đào tạo
- Phòng Công tác sinh viên: để biết về thủ tục hành chính, học bổng
- Hotline trường: để được hỗ trợ nhanh chóng
"""
                return combined_response
            else:
                # Milvus results are good, return the original response
                return response
                
        except Exception as e:
            print(f"Error in QnAHandler: {e}")
            # Fallback to SearchHandler if there's an error
            try:
                search_response = await self.search_handler.run(query)
                return f"Đã xảy ra lỗi khi truy cập cơ sở dữ liệu FAQ. Tuy nhiên, đây là thông tin tìm kiếm được:\n\n{search_response}"
            except Exception as search_error:
                return f"Xin lỗi, đã xảy ra lỗi khi xử lý câu hỏi của bạn. Vui lòng thử lại sau. Lỗi: {search_error}"