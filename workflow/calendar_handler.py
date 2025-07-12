"""
Calendar Handler - Xử lý tạo lịch học/lịch cá nhân
Tích hợp với file processing và tạo Google Calendar import code
"""

import sys
import os
import csv
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
import tempfile

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.basetools.file_reading_tool import read_file_tool
# from src.utils.basetools.document_chunking_tool import chunk_document
from src.data.cache.memory_handler import MessageMemoryHandler
from config.system_config import config

@dataclass
class TimeSlot:
    day_of_week: str  # "Monday", "Tuesday", etc.
    start_time: str   # "08:00"
    end_time: str     # "10:00"
    duration_minutes: int

@dataclass
class CalendarEvent:
    title: str
    description: str
    start_datetime: datetime
    end_datetime: datetime
    location: str
    category: str  # "study", "exercise", "meeting", "personal"
    recurrence: Optional[str]  # "weekly", "daily", None

@dataclass
class CalendarSummary:
    total_events: int
    study_hours_per_week: int
    free_time_slots: List[TimeSlot]
    conflicts: List[str]
    recommendations: List[str]

@dataclass
class CalendarResponse:
    calendar_summary: CalendarSummary
    events: List[CalendarEvent]
    csv_file_path: str
    google_calendar_code: str
    user_approved: bool = False

class CalendarHandler:
    """
    Xử lý việc tạo lịch học tập và cá nhân
    """
    
    def __init__(self):
        self.memory_handler = MessageMemoryHandler()
        self.temp_storage = {}  # Temporary storage for conversation data
        
        # Template lịch học chuẩn từ config
        calendar_template = config.get_calendar_template()
        self.standard_schedule_templates = {
            "university_semester": {
                "periods_per_day": 6,
                "period_duration": calendar_template["period_duration"],  # minutes
                "break_duration": 15,   # minutes
                "start_time": calendar_template["start_time"],
                "working_days": calendar_template["work_days"]
            },
            "high_school": {
                "periods_per_day": 8,
                "period_duration": 45,
                "break_duration": 10,
                "start_time": "07:00", 
                "working_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
            }
        }
    
    def handle_calendar_request(self, user_input: str, session_id: str) -> Dict[str, Any]:
        """
        Xử lý yêu cầu tạo lịch từ user
        """
        # 1. Phân tích intent và thu thập thông tin cần thiết
        required_info = self._analyze_calendar_requirements(user_input)
        
        # 2. Kiểm tra thông tin còn thiếu
        missing_info = self._check_missing_information(required_info, session_id)
        
        if missing_info:
            return {
                "type": "request_more_info",
                "message": self._create_info_request_message(missing_info),
                "missing_fields": missing_info
            }
        
        # 3. Xử lý file thời khóa biểu nếu có
        schedule_data = self._process_schedule_files(session_id)
        
        # 4. Tạo lịch dựa trên thông tin đã thu thập
        calendar_response = self._generate_calendar(required_info, schedule_data, session_id)
        
        # 5. Tạo file CSV và code Google Calendar
        csv_path = self._create_csv_file(calendar_response.events)
        google_code = self._generate_google_calendar_code(calendar_response.events)
        
        calendar_response.csv_file_path = csv_path
        calendar_response.google_calendar_code = google_code
        
        return {
            "type": "calendar_preview",
            "calendar_response": calendar_response,
            "preview_message": self._create_calendar_preview_message(calendar_response)
        }
    
    def _analyze_calendar_requirements(self, user_input: str) -> Dict[str, Any]:
        """
        Phân tích yêu cầu của user để xác định thông tin cần thiết
        """
        user_input_lower = user_input.lower()
        
        requirements = {
            "calendar_type": "personal",  # "study", "exercise", "personal", "mixed"
            "duration_weeks": 4,  # Default 4 weeks
            "priorities": [],
            "constraints": [],
            "schedule_type": "university_semester"  # Default
        }
        
        # Xác định loại lịch
        if any(word in user_input_lower for word in ["học", "môn học", "khóa học", "study"]):
            requirements["calendar_type"] = "study"
        elif any(word in user_input_lower for word in ["tập", "thể dục", "gym", "exercise"]):
            requirements["calendar_type"] = "exercise"
        elif any(word in user_input_lower for word in ["cá nhân", "sinh hoạt", "personal"]):
            requirements["calendar_type"] = "personal"
        else:
            requirements["calendar_type"] = "mixed"
        
        # Xác định thời gian
        if "tuần" in user_input_lower:
            # Tìm số tuần
            words = user_input.split()
            for i, word in enumerate(words):
                if "tuần" in word and i > 0:
                    try:
                        requirements["duration_weeks"] = int(words[i-1])
                    except ValueError:
                        pass
        
        # Xác định priorities từ từ khóa
        priority_keywords = {
            "toán": "Mathematics",
            "lý": "Physics", 
            "hóa": "Chemistry",
            "anh": "English",
            "văn": "Literature",
            "thể dục": "Physical Education",
            "tin học": "Computer Science"
        }
        
        for keyword, subject in priority_keywords.items():
            if keyword in user_input_lower:
                requirements["priorities"].append(subject)
        
        return requirements
    
    def _check_missing_information(self, requirements: Dict[str, Any], session_id: str) -> List[str]:
        """
        Kiểm tra thông tin còn thiếu cần hỏi thêm user
        """
        missing = []
        
        # Lấy thông tin đã có từ conversation
        stored_info = self.temp_storage.get(session_id, {})
        
        # Các thông tin cần thiết
        required_fields = {
            "schedule_file": "File thời khóa biểu hiện tại",
            "preferred_study_times": "Thời gian học ưa thích", 
            "break_preferences": "Thời gian nghỉ mong muốn",
            "special_requirements": "Yêu cầu đặc biệt"
        }
        
        for field, description in required_fields.items():
            if field not in stored_info and field not in requirements:
                missing.append(field)
        
        return missing
    
    def _create_info_request_message(self, missing_info: List[str]) -> str:
        """
        Tạo message yêu cầu thông tin từ user
        """
        messages = []
        
        messages.append("📅 **ĐỂ TẠO LỊCH TỐI ƯU, TÔI CẦN THÊM THÔNG TIN:**")
        messages.append("")
        
        if "schedule_file" in missing_info:
            messages.append("📎 **1. File thời khóa biểu hiện tại**")
            messages.append("   - Vui lòng upload file thời khóa biểu (Excel, PDF, txt)")
            messages.append("   - Hoặc gõ trực tiếp lịch học hiện tại của bạn")
            messages.append("")
        
        if "preferred_study_times" in missing_info:
            messages.append("⏰ **2. Thời gian học ưa thích**")
            messages.append("   - Bạn thích học vào khung giờ nào? (VD: sáng 7-11h, chiều 14-17h)")
            messages.append("   - Có môn nào bạn muốn ưu tiên không?")
            messages.append("")
        
        if "break_preferences" in missing_info:
            messages.append("☕ **3. Thời gian nghỉ**")
            messages.append("   - Bạn muốn nghỉ bao lâu giữa các buổi học? (15p, 30p, 1h)")
            messages.append("   - Có hoạt động gì trong giờ nghỉ không?")
            messages.append("")
        
        if "special_requirements" in missing_info:
            messages.append("⚡ **4. Yêu cầu đặc biệt**")
            messages.append("   - Có ràng buộc về thời gian không? (VD: không học tối muộn)")
            messages.append("   - Có hoạt động cố định nào cần tránh không?")
            messages.append("")
        
        messages.append("💡 **Hãy cung cấp từng thông tin, tôi sẽ ghi nhận và xử lý!**")
        
        return "\n".join(messages)
    
    def store_user_info(self, session_id: str, info_type: str, info_content: str) -> str:
        """
        Lưu thông tin user cung cấp vào temporary storage
        """
        if session_id not in self.temp_storage:
            self.temp_storage[session_id] = {}
        
        self.temp_storage[session_id][info_type] = info_content
        
        return f"✅ Đã ghi nhận thông tin về {info_type}. Cảm ơn bạn!"
    
    def _process_schedule_files(self, session_id: str) -> Dict[str, Any]:
        """
        Xử lý file thời khóa biểu mà user upload
        """
        stored_info = self.temp_storage.get(session_id, {})
        schedule_data = {"events": [], "constraints": []}
        
        if "schedule_file" in stored_info:
            try:
                # Giả sử user đã upload file và path được lưu
                file_path = stored_info["schedule_file"]
                
                # Đọc file (simplified without FileReadInput)
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                
                # Chunk và phân tích content (simplified without chunk_document)
                content_chunks = [file_content[:2000]]  # Simple chunking
                schedule_data = self._parse_schedule_from_content(content_chunks)
                
            except Exception as e:
                print(f"Error processing schedule file: {e}")
                schedule_data = {"events": [], "constraints": [], "error": str(e)}
        
        return schedule_data
    
    def _parse_schedule_from_content(self, content_chunks: List[str]) -> Dict[str, Any]:
        """
        Parse lịch học từ content chunks
        """
        events = []
        constraints = []
        
        # Đơn giản hóa parsing logic
        for chunk in content_chunks:
            chunk_lower = chunk.lower()
            
            # Tìm thời gian và môn học
            if any(day in chunk_lower for day in ["thứ", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]):
                # Extract event info
                lines = chunk.split('\n')
                for line in lines:
                    if any(time_indicator in line for time_indicator in [":", "h", "giờ"]):
                        # Tạo event từ line này
                        event_info = self._extract_event_from_line(line)
                        if event_info:
                            events.append(event_info)
        
        return {"events": events, "constraints": constraints}
    
    def _extract_event_from_line(self, line: str) -> Optional[Dict[str, Any]]:
        """
        Extract thông tin event từ một dòng text
        """
        # Đơn giản hóa - return placeholder
        # TODO: Implement proper parsing logic
        return {
            "title": "Môn học",
            "time": "08:00-10:00",
            "day": "Monday",
            "location": "Phòng học"
        }
    
    def _generate_calendar(self, requirements: Dict[str, Any], schedule_data: Dict[str, Any], session_id: str) -> CalendarResponse:
        """
        Tạo lịch dựa trên requirements và schedule data
        """
        events = []
        
        # Lấy template
        template = self.standard_schedule_templates[requirements["schedule_type"]]
        
        # Tạo events cho số tuần được yêu cầu
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        for week in range(requirements["duration_weeks"]):
            week_start = start_date + timedelta(weeks=week)
            
            for day_offset, day_name in enumerate(template["working_days"]):
                current_date = week_start + timedelta(days=day_offset)
                
                # Tạo events cho ngày này
                daily_events = self._generate_daily_events(
                    current_date, 
                    requirements, 
                    template,
                    schedule_data
                )
                events.extend(daily_events)
        
        # Tạo summary
        calendar_summary = self._create_calendar_summary(events, requirements)
        
        return CalendarResponse(
            calendar_summary=calendar_summary,
            events=events,
            csv_file_path="",  # Sẽ được set sau
            google_calendar_code=""  # Sẽ được set sau
        )
    
    def _generate_daily_events(self, date: datetime, requirements: Dict[str, Any], template: Dict[str, Any], schedule_data: Dict[str, Any]) -> List[CalendarEvent]:
        """
        Tạo events cho một ngày cụ thể
        """
        events = []
        
        # Parse start time
        start_hour, start_minute = map(int, template["start_time"].split(":"))
        current_time = date.replace(hour=start_hour, minute=start_minute)
        
        # Tạo các periods trong ngày
        for period in range(template["periods_per_day"]):
            # Tính thời gian của period
            period_start = current_time + timedelta(minutes=period * (template["period_duration"] + template["break_duration"]))
            period_end = period_start + timedelta(minutes=template["period_duration"])
            
            # Tạo event (simplified)
            if requirements["calendar_type"] == "study":
                event_title = f"Học tập - Tiết {period + 1}"
                event_category = "study"
            elif requirements["calendar_type"] == "exercise":
                event_title = f"Luyện tập - Buổi {period + 1}"
                event_category = "exercise"
            else:
                event_title = f"Hoạt động {period + 1}"
                event_category = "personal"
            
            event = CalendarEvent(
                title=event_title,
                description=f"Hoạt động được lên lịch tự động",
                start_datetime=period_start,
                end_datetime=period_end,
                location="",
                category=event_category,
                recurrence=None
            )
            
            events.append(event)
        
        return events
    
    def _create_calendar_summary(self, events: List[CalendarEvent], requirements: Dict[str, Any]) -> CalendarSummary:
        """
        Tạo summary cho calendar
        """
        total_events = len(events)
        
        # Tính study hours per week
        study_events = [e for e in events if e.category == "study"]
        total_study_minutes = sum((e.end_datetime - e.start_datetime).total_seconds() / 60 for e in study_events)
        study_hours_per_week = int(total_study_minutes / 60 / requirements["duration_weeks"])
        
        # Tìm free time slots (simplified)
        free_slots = [
            TimeSlot("Saturday", "19:00", "22:00", 180),
            TimeSlot("Sunday", "08:00", "18:00", 600)
        ]
        
        # Tìm conflicts (simplified)
        conflicts = []
        
        # Tạo recommendations
        recommendations = [
            "Nên nghỉ 15 phút giữa các buổi học",
            "Ưu tiên học các môn khó vào buổi sáng",
            "Dành thời gian ôn tập vào cuối tuần"
        ]
        
        return CalendarSummary(
            total_events=total_events,
            study_hours_per_week=study_hours_per_week,
            free_time_slots=free_slots,
            conflicts=conflicts,
            recommendations=recommendations
        )
    
    def _create_csv_file(self, events: List[CalendarEvent]) -> str:
        """
        Tạo file CSV từ events
        """
        try:
            # Tạo temporary file
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8')
            
            # Write CSV header
            fieldnames = ['Subject', 'Start Date', 'Start Time', 'End Date', 'End Time', 'Description', 'Location', 'Category']
            writer = csv.DictWriter(temp_file, fieldnames=fieldnames)
            writer.writeheader()
            
            # Write events
            for event in events:
                writer.writerow({
                    'Subject': event.title,
                    'Start Date': event.start_datetime.strftime('%m/%d/%Y'),
                    'Start Time': event.start_datetime.strftime('%H:%M'),
                    'End Date': event.end_datetime.strftime('%m/%d/%Y'),
                    'End Time': event.end_datetime.strftime('%H:%M'),
                    'Description': event.description,
                    'Location': event.location,
                    'Category': event.category
                })
            
            temp_file.close()
            return temp_file.name
            
        except Exception as e:
            print(f"Error creating CSV file: {e}")
            return ""
    
    def _generate_google_calendar_code(self, events: List[CalendarEvent]) -> str:
        """
        Tạo code Python để import vào Google Calendar
        """
        code_template = '''"""
Google Calendar Import Script
Tự động tạo từ hệ thống Calendar Handler
"""

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle
import os
from datetime import datetime

# Scopes needed for Google Calendar
SCOPES = ['https://www.googleapis.com/auth/calendar']

def authenticate_google_calendar():
    """Authenticate with Google Calendar API"""
    creds = None
    
    # Token file stores the user's access and refresh tokens
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    return build('calendar', 'v3', credentials=creds)

def create_calendar_events():
    """Create calendar events"""
    service = authenticate_google_calendar()
    
    events_data = [
'''
        
        # Add events data
        for event in events:
            event_dict = {
                'summary': event.title,
                'description': event.description,
                'location': event.location,
                'start': {
                    'dateTime': event.start_datetime.isoformat(),
                    'timeZone': 'Asia/Ho_Chi_Minh'
                },
                'end': {
                    'dateTime': event.end_datetime.isoformat(),
                    'timeZone': 'Asia/Ho_Chi_Minh'
                }
            }
            code_template += f"        {event_dict},\n"
        
        code_template += '''    ]
    
    # Create events
    for event_data in events_data:
        try:
            event = service.events().insert(calendarId='primary', body=event_data).execute()
            print(f"Event created: {event['summary']}")
        except Exception as e:
            print(f"Error creating event {event_data['summary']}: {e}")

if __name__ == "__main__":
    print("Đang tạo events trong Google Calendar...")
    create_calendar_events()
    print("Hoàn thành!")
'''
        
        return code_template
    
    def _create_calendar_preview_message(self, calendar_response: CalendarResponse) -> str:
        """
        Tạo preview message cho calendar
        """
        summary = calendar_response.calendar_summary
        
        preview_parts = []
        
        preview_parts.append("📅 **TÓM TẮT LỊCH TRÌNH ĐÃ TẠO**")
        preview_parts.append("")
        preview_parts.append(f"📊 **Thống kê:**")
        preview_parts.append(f"   • Tổng số sự kiện: {summary.total_events}")
        preview_parts.append(f"   • Giờ học/tuần: {summary.study_hours_per_week} tiếng")
        preview_parts.append("")
        
        if summary.free_time_slots:
            preview_parts.append("🕐 **Thời gian rảnh:**")
            for slot in summary.free_time_slots:
                preview_parts.append(f"   • {slot.day_of_week}: {slot.start_time} - {slot.end_time}")
            preview_parts.append("")
        
        if summary.conflicts:
            preview_parts.append("⚠️ **Xung đột lịch:**")
            for conflict in summary.conflicts:
                preview_parts.append(f"   • {conflict}")
            preview_parts.append("")
        
        if summary.recommendations:
            preview_parts.append("💡 **Gợi ý:**")
            for rec in summary.recommendations:
                preview_parts.append(f"   • {rec}")
            preview_parts.append("")
        
        preview_parts.append("📎 **File đã tạo:**")
        preview_parts.append(f"   • File CSV: {calendar_response.csv_file_path}")
        preview_parts.append("   • Code Google Calendar: Đã tạo")
        preview_parts.append("")
        
        preview_parts.append("❓ **Bạn có hài lòng với lịch này không?**")
        preview_parts.append("   • Trả lời 'OK' nếu đồng ý")
        preview_parts.append("   • Trả lời 'SỬA' để chỉnh sửa")
        preview_parts.append("   • Trả lời 'GOOGLE' để nhận code import Google Calendar")
        
        return "\n".join(preview_parts)
    
    def approve_calendar(self, session_id: str) -> Dict[str, Any]:
        """
        User approve calendar và cung cấp final files
        """
        return {
            "message": "✅ Lịch trình đã được phê duyệt! File CSV và code đã sẵn sàng.",
            "files_ready": True
        }
    
    def get_google_calendar_instructions(self) -> str:
        """
        Trả về hướng dẫn setup Google Calendar
        """
        instructions = '''
🔧 **HƯỚNG DẪN SETUP GOOGLE CALENDAR API**

**Bước 1: Tạo Google Cloud Project**
1. Truy cập: https://console.cloud.google.com/
2. Tạo project mới hoặc chọn project hiện có
3. Enable Google Calendar API

**Bước 2: Tạo Credentials**
1. Vào "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth 2.0 Client IDs"
3. Chọn "Desktop Application"
4. Download file JSON và đổi tên thành "credentials.json"

**Bước 3: Cài đặt thư viện**
```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

**Bước 4: Chạy code**
1. Đặt file "credentials.json" cùng thư mục với code
2. Chạy script Python đã tạo
3. Authorize lần đầu qua browser

**Lưu ý:** 
- Token sẽ được lưu để sử dụng lần sau
- Code sẽ tự động tạo tất cả events trong calendar
        '''
        
        return instructions
