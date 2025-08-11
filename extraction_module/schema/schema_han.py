from pydantic import BaseModel, Field
from typing import List, Optional

# 개인정보
class PersonalInfo(BaseModel):
    name: Optional[str] = Field(description="이름", default=None)
    gender: Optional[str] = Field(description="성별(남자/여자)", default=None)
    nationality_type: Optional[str] = Field(description="외국인/내국인", default=None)
    nationality: Optional[str] = Field(description="국가명", default=None)
    birth: Optional[str] = Field(description="생년월일(yyyy 또는 yyyy-mm-dd 또는 yyyy-mm)", default=None)
    contacts: List[str] = Field(description="연락처(전화번호)", default_factory=list)
    email: Optional[str] = Field(description="이메일", default=None)
    address: Optional[str] = Field(description="주소", default=None)
    available_date: Optional[str] = Field(description="입사가능시기", default=None)
    sns_links: List[str] = Field(description="SNS 링크(깃헙/링크드인/블로그 등)", default_factory=list)
    desired_job: Optional[str] = Field(description="희망직무", default=None)
    desired_location: Optional[str] = Field(description="희망 근무지", default=None)
    desired_position: Optional[str] = Field(description="희망 직급", default=None)
    desired_salary: Optional[str] = Field(description="희망 급여", default=None)

# 요약정보
class SummaryInfo(BaseModel):
    brief_introduction: Optional[str] = Field(description="간략소개(문서에 명시된 경우만 추출)", default=None)
    core_competencies: List[str] = Field(description="핵심역량(문서에 명시되어 있는 스킬이나 역량)", default_factory=list)

# 학력사항
class Education(BaseModel):
    school_type: Optional[str] = Field(description="학교종류(예시 초등학교/중학교/고등학교/대학교/대학원)", default=None)
    school_name: Optional[str] = Field(description="학교명", default=None)
    admission_date: Optional[str] = Field(description="입학년월(yyyy 또는 yyyy-mm-dd 또는 yyyy-mm)", default=None)
    graduation_date: Optional[str] = Field(description="졸업년월(yyyy 또는 yyyy-mm-dd 또는 yyyy-mm)", default=None)
    gpa: Optional[str] = Field(description="학점(고등학교/대학교/대학원 해당 시)", default=None)
    major: Optional[str] = Field(description="전공(고등학교/대학교/대학원 해당 시)", default=None)
    sub_major: Optional[str] = Field(description="부전공(고등학교/대학교/대학원 해당 시, 있을 때만)", default=None)
    degree: Optional[str] = Field(description="학위(대학교/대학원 해당 시, 전학/학사/석사/박사)", default=None)
    graduation_work: Optional[str] = Field(description="졸업작품(대학원 해당 시, 논문 혹은 작품)", default=None)
    completion_status: Optional[str] = Field(description="학업상태(졸업/재학/휴학/수료) 졸업년이 있으면 졸업", default=None)

# 경력
class Career(BaseModel):
    company_name: Optional[str] = Field(description="회사명", default=None)
    start_date: Optional[str] = Field(description="입사년월(yyyy 또는 yyyy-mm-dd 또는 yyyy-mm)", default=None)
    end_date: Optional[str] = Field(description="퇴사년월(yyyy 또는 yyyy-mm-dd 또는 yyyy-mm)", default=None)
    is_currently_employed: Optional[bool] = Field(description="재직중 여부", default=None)
    responsibilities: Optional[str] = Field(description="담당업무(해당 회사에서의 경력요약, 경력기술서, 주요업무, 담당업무, 프로젝트 상세 내용 등 모든 경력 관련 전체 내용)", default=None)
    reason_for_leaving: Optional[str] = Field(description="이직/퇴사사유", default=None)
    annual_salary: Optional[int] = Field(description="연봉", default=None)
    work_location: Optional[str] = Field(description="근무지역", default=None)
    job_field: Optional[str] = Field(description="직무명(실제 수행 업무/담당 분야)", default=None)
    department: Optional[str] = Field(description="부서", default=None)
    position: Optional[str] = Field(description="직책(구체적 역할/지위)", default=None)
    rank: Optional[str] = Field(description="직급(서열/등급)", default=None)
    employment_type: Optional[str] = Field(description="고용형태(정규직, 계약직 등)", default=None)

# 교육
class EducationProgram(BaseModel):
    program_name: Optional[str] = Field(description="교육명", default=None)
    start_date: Optional[str] = Field(description="시작년월(yyyy 또는 yyyy-mm-dd 또는 yyyy-mm)", default=None)
    end_date: Optional[str] = Field(description="종료년월(yyyy 또는 yyyy-mm-dd 또는 yyyy-mm)", default=None)
    details: Optional[str] = Field(description="교육과정내용", default=None)

# 해외연수
class OverseasExperience(BaseModel):
    country: Optional[str] = Field(description="국가명", default=None)
    start_date: Optional[str] = Field(description="시작년월(yyyy 또는 yyyy-mm-dd 또는 yyyy-mm)", default=None)
    end_date: Optional[str] = Field(description="종료년월(yyyy 또는 yyyy-mm-dd 또는 yyyy-mm)", default=None)
    details: Optional[str] = Field(description="경험내용", default=None)

# 자격증
class Certificate(BaseModel):
    certificate_name: Optional[str] = Field(description="자격명", default=None)
    issuing_authority: Optional[str] = Field(description="발행처", default=None)
    acquisition_date: Optional[str] = Field(description="취득년월(yyyy 또는 yyyy-mm-dd 또는 yyyy-mm)", default=None)
    score: Optional[str] = Field(description="점수/합격여부", default=None)

# 수상/공모전
class Award(BaseModel):
    award_name: Optional[str] = Field(description="수상/공모전명", default=None)
    awarding_institution: Optional[str] = Field(description="수여기관", default=None)
    award_date: Optional[str] = Field(description="수여년월(yyyy 또는 yyyy-mm-dd 또는 yyyy-mm)", default=None)
    details: Optional[str] = Field(description="상세설명", default=None)

# 취업우대
class EmploymentPreference(BaseModel):
    is_veteran_target: Optional[bool] = Field(description="보훈대상여부", default=None)
    veteran_reason: Optional[str] = Field(description="보훈사유", default=None)
    is_employment_protection_target: Optional[bool] = Field(description="취업보호대상여부", default=None)
    is_disabled: Optional[bool] = Field(description="장애여부", default=None)
    disability_grade: Optional[str] = Field(description="장애등급", default=None)

# 병역
class MilitaryService(BaseModel):
    military_status: Optional[str] = Field(description="병역대상(군필, 미필, 면제, 복무중, 해당없음)", default=None)
    service_start_date: Optional[str] = Field(description="입대년월일(yyyy 또는 yyyy-mm-dd 또는 yyyy-mm)", default=None)
    service_end_date: Optional[str] = Field(description="제대년월일(yyyy 또는 yyyy-mm-dd 또는 yyyy-mm)", default=None)
    military_branch: Optional[str] = Field(description="군별(육군,해군,공군,해병 등)", default=None)
    rank: Optional[str] = Field(description="제대계급(이병, 일병, 상병, 병장)", default=None)

# 자기소개서
class CoverLetter(BaseModel):
    full_text: Optional[str] = Field(description="자기소개서 전체 내용", default=None)

# 기타
class EtcInfo(BaseModel):
    details: Optional[str] = Field(description="위의 항목에서 뽑히지 않은 나머지", default=None)

# 최상위 스키마는 모든 클래스 정의 이후에 위치해야 함
class ExtractInfo(BaseModel):
    personal_info: Optional[PersonalInfo] = Field(description="개인정보", default=None)
    summary_info: Optional[SummaryInfo] = Field(description="요약정보", default=None)
    educations: List[Education] = Field(description="학력사항", default_factory=list)
    careers: List[Career] = Field(description="경력", default_factory=list)
    education_programs: List[EducationProgram] = Field(description="교육", default_factory=list)
    overseas_experiences: List[OverseasExperience] = Field(description="해외연수", default_factory=list)
    certificates: List[Certificate] = Field(description="자격증", default_factory=list)
    awards: List[Award] = Field(description="수상/공모전", default_factory=list)
    employment_preference: Optional[EmploymentPreference] = Field(description="취업우대", default=None)
    military_service: Optional[MilitaryService] = Field(description="병역", default=None)
    cover_letter: Optional[CoverLetter] = Field(description="자기소개서", default=None)
    etc_info: Optional[EtcInfo] = Field(description="기타", default=None)