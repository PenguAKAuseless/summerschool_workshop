"""
Search Information Handler - Xử lý tìm kiếm thông tin chi tiết
Tập trung vào web search và document search với validation chặt chẽ
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.basetools.search_web_tool import search_web, SearchInput as WebSearchInput
from src.utils.basetools.search_relevant_document_tool import search_relevant_document
from src.data.cache.memory_handler import MessageMemoryHandler

from dataclasses import dataclass
from typing import Dict, Any, List

@dataclass
class SearchResult:
    title: str
    content: str
    source: str
    relevance_score: float

@dataclass
class SearchResponse:
    results: List[SearchResult]
    summary: str
    follow_up_questions: List[str]
    confidence: float
    is_school_related: bool

class SearchInformationHandler:
    """
    Xử lý các request tìm kiếm thông tin chi tiết
    """
    
    def __init__(self):
        self.memory_handler = MessageMemoryHandler()
        
        # Từ khóa liên quan đến trường học để validate
        self.school_keywords = [
            "trường", "học", "sinh viên", "giáo viên", "khóa học", "môn học",
            "học phí", "đăng ký", "thi", "điểm", "bằng cấp", "chứng chỉ",
            "thư viện", "ký túc xá", "học bổng", "tuyển sinh", "giáo dục",
            "university", "college", "student", "teacher", "course", "exam"
        ]
        
        # Từ khóa cần chặn (nội dung không phù hợp)
        self.blocked_keywords = [
            "bạo lực", "khiêu dâm", "ma túy", "đánh bạc", "chính trị",
            "tôn giáo cực đoan", "hack", "virus", "phần mềm lậu"
        ]
    
    def handle_search(self, query: str, session_id: str) -> SearchResponse:
        """
        Xử lý request tìm kiếm thông tin
        """
        # 1. Validate input
        if not self._is_valid_search_query(query):
            return SearchResponse(
                results=[],
                summary="Xin lỗi, tôi không thể tìm kiếm thông tin về chủ đề này. Vui lòng tìm kiếm thông tin liên quan đến giáo dục và trường học.",
                follow_up_questions=[],
                confidence=0.0,
                is_school_related=False
            )
        
        # 2. Tìm kiếm thông tin
        search_results = self._perform_comprehensive_search(query)
        
        # 3. Filter và validate kết quả
        filtered_results = self._filter_and_validate_results(search_results, query)
        
        # 4. Tạo summary và follow-up questions
        summary = self._generate_summary(filtered_results, query)
        follow_up_questions = self._generate_follow_up_questions(query, filtered_results)
        
        # 5. Tính confidence score
        confidence = self._calculate_confidence(filtered_results, query)
        
        # 6. Kiểm tra liên quan đến trường học
        is_school_related = self._is_school_related(query, filtered_results)
        
        return SearchResponse(
            results=filtered_results,
            summary=summary,
            follow_up_questions=follow_up_questions,
            confidence=confidence,
            is_school_related=is_school_related
        )
    
    def _is_valid_search_query(self, query: str) -> bool:
        """
        Kiểm tra query có hợp lệ không
        """
        query_lower = query.lower()
        
        # Kiểm tra blocked keywords
        for blocked in self.blocked_keywords:
            if blocked in query_lower:
                return False
        
        # Kiểm tra độ dài query
        if len(query.strip()) < 3:
            return False
        
        return True
    
    def _perform_comprehensive_search(self, query: str) -> List[SearchResult]:
        """
        Thực hiện tìm kiếm toàn diện từ nhiều nguồn
        """
        all_results = []
        
        try:
            # 1. Web search với query gốc
            web_input = WebSearchInput(query=query, max_results=5)
            web_results = search_web(web_input)
            
            for result in web_results.results:
                all_results.append(SearchResult(
                    title=result.get("title", ""),
                    content=result.get("content", ""),
                    source=result.get("link", ""),
                    relevance_score=0.7
                ))
        
        except Exception as e:
            print(f"Error in web search: {e}")
        
        try:
            # 2. Web search với context trường học
            school_query = f"trường học giáo dục {query}"
            school_web_input = WebSearchInput(query=school_query, max_results=3)
            school_web_results = search_web(school_web_input)
            
            for result in school_web_results.results:
                all_results.append(SearchResult(
                    title=f"[GIÁO DỤC] {result.get('title', '')}",
                    content=result.get("content", ""),
                    source=result.get("link", ""),
                    relevance_score=0.8
                ))
        
        except Exception as e:
            print(f"Error in school-focused web search: {e}")
        
        try:
            # 3. Document search (nếu có)
            # doc_results = search_relevant_document({"query": query})
            # Process document results...
            pass
        
        except Exception as e:
            print(f"Error in document search: {e}")
        
        return all_results
    
    def _filter_and_validate_results(self, results: List[SearchResult], query: str) -> List[SearchResult]:
        """
        Lọc và validate kết quả tìm kiếm
        """
        filtered_results = []
        
        for result in results:
            # Kiểm tra nội dung có phù hợp không
            if self._is_appropriate_content(result):
                # Tính toán relevance score chi tiết hơn
                relevance_score = self._calculate_relevance_score(result, query)
                result.relevance_score = relevance_score
                
                if relevance_score > 0.3:  # Threshold để lọc kết quả
                    filtered_results.append(result)
        
        # Sắp xếp theo relevance score
        filtered_results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Giới hạn số lượng kết quả
        return filtered_results[:7]
    
    def _is_appropriate_content(self, result: SearchResult) -> bool:
        """
        Kiểm tra nội dung có phù hợp không
        """
        content_lower = (result.title + " " + result.content).lower()
        
        # Kiểm tra blocked keywords
        for blocked in self.blocked_keywords:
            if blocked in content_lower:
                return False
        
        # Kiểm tra độ dài nội dung
        if len(result.title.strip()) < 3:
            return False
        
        return True
    
    def _calculate_relevance_score(self, result: SearchResult, query: str) -> float:
        """
        Tính toán relevance score chi tiết
        """
        query_words = query.lower().split()
        content_lower = (result.title + " " + result.content).lower()
        
        # Tính số từ khóa match
        matched_words = sum(1 for word in query_words if word in content_lower)
        word_match_score = matched_words / len(query_words)
        
        # Bonus cho school-related content
        school_bonus = 0.0
        school_word_count = sum(1 for keyword in self.school_keywords if keyword in content_lower)
        if school_word_count > 0:
            school_bonus = min(school_word_count * 0.1, 0.3)
        
        # Combine scores
        final_score = (word_match_score * 0.7) + school_bonus + (result.relevance_score * 0.3)
        
        return min(final_score, 1.0)
    
    def _generate_summary(self, results: List[SearchResult], query: str) -> str:
        """
        Tạo summary từ kết quả tìm kiếm
        """
        if not results:
            return "Không tìm thấy thông tin phù hợp về chủ đề này trong phạm vi giáo dục."
        
        # Tạo summary từ top results
        top_results = results[:3]
        summary_parts = []
        
        summary_parts.append(f"Dựa trên tìm kiếm về '{query}', đây là những thông tin chính:")
        
        for i, result in enumerate(top_results, 1):
            if result.title:
                summary_parts.append(f"{i}. {result.title}")
        
        summary_parts.append(f"\nTìm thấy {len(results)} kết quả liên quan. Bạn có muốn tôi tìm hiểu sâu hơn về khía cạnh nào không?")
        
        return "\n".join(summary_parts)
    
    def _generate_follow_up_questions(self, query: str, results: List[SearchResult]) -> List[str]:
        """
        Tạo các câu hỏi follow-up
        """
        follow_ups = []
        
        # Base follow-up questions
        follow_ups.append(f"Bạn muốn biết thêm chi tiết về khía cạnh nào của '{query}'?")
        follow_ups.append("Có thông tin cụ thể nào bạn đang tìm kiếm không?")
        
        # Dynamic follow-ups based on results
        if any("học phí" in result.title.lower() for result in results):
            follow_ups.append("Bạn có muốn biết về học phí và hỗ trợ tài chính không?")
        
        if any("đăng ký" in result.title.lower() for result in results):
            follow_ups.append("Bạn cần hướng dẫn về quy trình đăng ký không?")
        
        return follow_ups[:3]  # Giới hạn 3 câu hỏi
    
    def _calculate_confidence(self, results: List[SearchResult], query: str) -> float:
        """
        Tính confidence score cho response
        """
        if not results:
            return 0.1
        
        # Base confidence từ số lượng và chất lượng kết quả
        result_count_score = min(len(results) / 5.0, 1.0)
        
        # Average relevance score
        avg_relevance = sum(result.relevance_score for result in results) / len(results)
        
        # School-related bonus
        school_related_count = sum(1 for result in results 
                                 if any(keyword in result.title.lower() + result.content.lower() 
                                       for keyword in self.school_keywords))
        school_bonus = min(school_related_count / len(results), 0.3)
        
        confidence = (result_count_score * 0.4) + (avg_relevance * 0.4) + (school_bonus * 0.2)
        
        return min(confidence, 0.95)
    
    def _is_school_related(self, query: str, results: List[SearchResult]) -> bool:
        """
        Kiểm tra có liên quan đến trường học không
        """
        query_lower = query.lower()
        
        # Kiểm tra query
        query_school_match = any(keyword in query_lower for keyword in self.school_keywords)
        
        # Kiểm tra results
        if results:
            result_content = " ".join([result.title + " " + result.content for result in results]).lower()
            result_school_match = any(keyword in result_content for keyword in self.school_keywords)
        else:
            result_school_match = False
        
        return query_school_match or result_school_match
    
    def interactive_follow_up(self, follow_up_query: str, original_query: str, session_id: str) -> SearchResponse:
        """
        Xử lý câu hỏi follow-up từ user
        """
        combined_query = f"{original_query} {follow_up_query}"
        return self.handle_search(combined_query, session_id)
