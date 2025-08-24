"""
Workflow core execution engine
"""

import os
import json
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from loguru import logger

from structured_output_kit.workflow.config import WorkflowConfig, ParsingConfig, ExtractionConfig, EvaluationConfig
from structured_output_kit.workflow.utils import create_workflow_output_dir, save_workflow_config, create_combination_output_dir, format_combination_name

# 기존 core 함수들 import
from structured_output_kit.parsing.core import run_parsing_core
from structured_output_kit.extraction.core import run_extraction_core
from structured_output_kit.evaluation.core import run_evaluation_core

# 기존 타입들 import
from structured_output_kit.utils.types import (
    ParsingRequest, ParsingResult,
    ExtractionRequest, ExtractionResult,
    EvaluationRequest, EvaluationResult,
    HostInfo
)


class CombinationResult:
    """조합 실행 결과"""
    def __init__(self, parsing_idx: Optional[int], extraction_idx: int, 
                 parsing_config: Optional[ParsingConfig], extraction_config: ExtractionConfig):
        self.parsing_idx = parsing_idx
        self.extraction_idx = extraction_idx
        self.parsing_config = parsing_config
        self.extraction_config = extraction_config
        
        self.parsing_result: Optional[ParsingResult] = None
        self.extraction_result: Optional[ExtractionResult] = None
        self.evaluation_result: Optional[EvaluationResult] = None
        
        self.success = False
        self.error_message: Optional[str] = None
        self.combination_name = self._format_combination_name()
    
    def _format_combination_name(self) -> str:
        """조합 이름을 사람이 읽기 쉬운 형태로 포맷"""
        if self.parsing_config is None:
            # 파싱 없는 경우
            extraction_name = f"{self.extraction_config.framework}({self.extraction_config.schema_name})"
            return f"E{self.extraction_idx+1}({extraction_name}) [Direct Input]"
        else:
            # 파싱 있는 경우
            parsing_name = f"{self.parsing_config.framework}"
            if hasattr(self.parsing_config, 'file_path'):
                file_name = os.path.basename(self.parsing_config.file_path)
                parsing_name += f"({file_name})"
            
            extraction_name = f"{self.extraction_config.framework}({self.extraction_config.schema_name})"
            return f"P{self.parsing_idx+1}({parsing_name}) → E{self.extraction_idx+1}({extraction_name})"


class WorkflowResult:
    """워크플로우 전체 실행 결과"""
    def __init__(self, config: WorkflowConfig, output_dir: str):
        self.config = config
        self.output_dir = output_dir
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None
        self.combination_results: List[CombinationResult] = []
        self.overall_success = False
        
    def add_combination_result(self, result: CombinationResult):
        """조합 결과 추가"""
        self.combination_results.append(result)
    
    def finalize(self):
        """워크플로우 완료 처리"""
        self.end_time = datetime.now()
        self.overall_success = all(result.success for result in self.combination_results)
    
    def get_summary(self) -> Dict[str, Any]:
        """워크플로우 실행 요약"""
        successful_combinations = sum(1 for result in self.combination_results if result.success)
        total_combinations = len(self.combination_results)
        
        return {
            "workflow_name": self.config.name,
            "total_combinations": total_combinations,
            "successful_combinations": successful_combinations,
            "success_rate": successful_combinations / total_combinations if total_combinations > 0 else 0,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": (self.end_time - self.start_time).total_seconds() if self.end_time else None,
            "output_dir": self.output_dir,
            "overall_success": self.overall_success
        }


class WorkflowExecutor:
    """워크플로우 실행 엔진"""
    
    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.output_dir = create_workflow_output_dir(config.name, config.output_dir)
        save_workflow_config(config, self.output_dir)
        
        logger.info(f"워크플로우 시작: {config.name}")
        logger.info(f"총 조합 수: {config.get_total_combinations()}")
        logger.info(f"출력 디렉토리: {self.output_dir}")
    
    async def execute(self) -> WorkflowResult:
        """워크플로우 전체 실행"""
        workflow_result = WorkflowResult(self.config, self.output_dir)
        
        try:
            combinations = self.config.get_combinations()
            
            if self.config.parallel:
                # 병렬 실행
                tasks = [
                    self._execute_combination(parsing_idx, extraction_idx, 
                                            parsing_config, extraction_config)
                    for parsing_idx, extraction_idx, parsing_config, extraction_config in combinations
                ]
                combination_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in combination_results:
                    if isinstance(result, Exception):
                        logger.error(f"조합 실행 중 오류 발생: {result}")
                        # 실패한 조합에 대한 더미 결과 생성
                        dummy_result = CombinationResult(0, 0, combinations[0][2], combinations[0][3])
                        dummy_result.error_message = str(result)
                        workflow_result.add_combination_result(dummy_result)
                    else:
                        workflow_result.add_combination_result(result)
            else:
                # 순차 실행
                for parsing_idx, extraction_idx, parsing_config, extraction_config in combinations:
                    if self.config.fail_fast and workflow_result.combination_results:
                        # fail_fast 모드에서 이전 실행이 실패했다면 중단
                        if not workflow_result.combination_results[-1].success:
                            logger.warning("이전 조합 실행 실패로 인해 워크플로우 중단")
                            break
                    
                    try:
                        result = await self._execute_combination(
                            parsing_idx, extraction_idx, parsing_config, extraction_config
                        )
                        workflow_result.add_combination_result(result)
                    except Exception as e:
                        logger.error(f"조합 실행 중 오류 발생: {e}")
                        dummy_result = CombinationResult(parsing_idx, extraction_idx, 
                                                       parsing_config, extraction_config)
                        dummy_result.error_message = str(e)
                        workflow_result.add_combination_result(dummy_result)
                        
                        if self.config.fail_fast:
                            break
            
            workflow_result.finalize()
            await self._save_workflow_summary(workflow_result)
            
            return workflow_result
            
        except Exception as e:
            logger.error(f"워크플로우 실행 중 치명적 오류 발생: {e}")
            workflow_result.finalize()
            raise
    
    async def _execute_combination(self, parsing_idx: Optional[int], extraction_idx: int,
                                 parsing_config: Optional[ParsingConfig], 
                                 extraction_config: ExtractionConfig) -> CombinationResult:
        """개별 조합 실행"""
        result = CombinationResult(parsing_idx or 0, extraction_idx, parsing_config, extraction_config)
        combination_output_dir = create_combination_output_dir(
            self.output_dir, parsing_idx or 0, extraction_idx
        )
        
        logger.info(f"조합 실행 시작: {result.combination_name}")
        
        try:
            if parsing_config is None:
                # 파싱이 없는 경우: extraction의 input_text 사용
                if not extraction_config.input_text:
                    result.error_message = "파싱 설정이 없는 경우 extraction에서 input_text를 제공해야 합니다"
                    logger.error(f"[{result.combination_name}] {result.error_message}")
                    return result
                
                input_content = extraction_config.input_text
                logger.info(f"[{result.combination_name}] 파싱 없이 직접 입력 텍스트 사용 (길이: {len(input_content)} 문자)")
            else:
                # 1. 파싱 단계 실행
                # parsing 설정이 있으면 항상 파싱을 실행하고, 그 결과를 extraction 입력으로 사용
                logger.info(f"[{result.combination_name}] 파싱 단계 시작")
                parsing_result = await self._execute_parsing(parsing_config, combination_output_dir)
                result.parsing_result = parsing_result
                
                if not parsing_result.success:
                    result.error_message = f"파싱 실패: {parsing_result.content}"
                    logger.error(f"[{result.combination_name}] 파싱 실패")
                    return result
                
                # 파싱 결과를 extraction의 입력으로 사용
                input_content = parsing_result.content
                logger.info(f"[{result.combination_name}] 파싱 결과 → 추출 입력 (길이: {len(input_content)} 문자)")

            # 2. 추출 단계
            logger.info(f"[{result.combination_name}] 추출 단계 시작")
            extraction_result = await self._execute_extraction(
                extraction_config, input_content, combination_output_dir
            )
            result.extraction_result = extraction_result
            
            if not extraction_result.success:
                result.error_message = f"추출 실패"
                logger.error(f"[{result.combination_name}] 추출 실패")
                return result
            
            # 3. 평가 단계 (선택적)
            if self.config.evaluation and self.config.evaluation.enabled:
                logger.info(f"[{result.combination_name}] 평가 단계 시작")
                evaluation_result = await self._execute_evaluation(
                    self.config.evaluation, extraction_result.result_json_path, combination_output_dir
                )
                result.evaluation_result = evaluation_result
                
                if not evaluation_result:
                    result.error_message = "평가 실패"
                    logger.error(f"[{result.combination_name}] 평가 실패")
                    return result
            
            result.success = True
            logger.info(f"[{result.combination_name}] 조합 실행 완료")
            
        except Exception as e:
            result.error_message = str(e)
            logger.error(f"[{result.combination_name}] 조합 실행 중 오류: {e}")
        
        return result
    
    async def _execute_parsing(self, config: ParsingConfig, output_dir: str) -> ParsingResult:
        """파싱 단계 실행"""
        host_info = None
        if config.host_info:
            host_info = HostInfo(**config.host_info)
        
        parsing_request = ParsingRequest(
            file_path=config.file_path,
            framework=config.framework,
            extra_kwargs=config.extra_kwargs,
            host_info=host_info,
            prompt=config.prompt,
            output_dir=output_dir,
            save=config.save
        )
        
        # 기존 run_parsing_core 함수 사용
        return run_parsing_core(parsing_request)
    
    async def _execute_extraction(self, config: ExtractionConfig, 
                                input_text: str, output_dir: str) -> ExtractionResult:
        """추출 단계 실행"""
        host_info = HostInfo(**config.host_info)
        
        extraction_request = ExtractionRequest(
            prompt=config.prompt,
            input_text=input_text,
            retries=config.retries,
            schema_name=config.schema_name,
            extra_kwargs=config.extra_kwargs,
            framework=config.framework,
            host_info=host_info,
            langfuse_trace_id=config.langfuse_trace_id,
            output_dir=output_dir,
            save=config.save
        )
        
        # 기존 run_extraction_core 함수 사용
        return run_extraction_core(extraction_request)
    
    async def _execute_evaluation(self, config: EvaluationConfig, 
                                pred_json_path: str, output_dir: str) -> Optional[EvaluationResult]:
        """평가 단계 실행"""
        if not config.gt_json_path:
            logger.warning("평가를 위한 ground truth 파일이 지정되지 않았습니다")
            return None
        
        host_info = None
        if config.host_info:
            host_info = HostInfo(**config.host_info)
        
        evaluation_request = EvaluationRequest(
            pred_json_path=pred_json_path,
            gt_json_path=config.gt_json_path,
            schema_name=config.schema_name,
            criteria_path=config.criteria_path,
            host_info=host_info,
            output_dir=output_dir,
            save=config.save
        )
        
        try:
            # 기존 run_evaluation_core 함수 사용
            return run_evaluation_core(evaluation_request)
        except Exception as e:
            logger.error(f"평가 실행 중 오류: {e}")
            return None
    
    async def _save_workflow_summary(self, workflow_result: WorkflowResult):
        """워크플로우 실행 요약 저장"""
        summary = workflow_result.get_summary()
        
        # 조합별 상세 결과 추가
        summary["combination_details"] = []
        for result in workflow_result.combination_results:
            detail = {
                "combination_name": result.combination_name,
                "parsing_idx": result.parsing_idx,
                "extraction_idx": result.extraction_idx,
                "success": result.success,
                "error_message": result.error_message,
                "parsing_framework": result.parsing_config.framework,
                "extraction_framework": result.extraction_config.framework,
                "extraction_schema": result.extraction_config.schema_name
            }
            
            if result.parsing_result:
                detail["parsing_output_dir"] = result.parsing_result.output_dir
                detail["parsing_result_path"] = result.parsing_result.result_txt_path
            
            if result.extraction_result:
                detail["extraction_output_dir"] = result.extraction_result.output_dir
                detail["extraction_result_path"] = result.extraction_result.result_json_path
                detail["extraction_success_rate"] = result.extraction_result.success_rate
                detail["extraction_latency"] = result.extraction_result.latency
            
            if result.evaluation_result:
                detail["evaluation_output_dir"] = result.evaluation_result.output_dir
                detail["evaluation_result_path"] = result.evaluation_result.eval_result_path
                detail["evaluation_score"] = result.evaluation_result.overall_score
            
            summary["combination_details"].append(detail)
        
        # 요약 파일 저장
        summary_path = os.path.join(self.output_dir, "workflow_summary.json")
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        logger.info(f"워크플로우 요약 저장: {summary_path}")
        
        # 콘솔에 요약 출력
        self._print_workflow_summary(summary)
    
    def _print_workflow_summary(self, summary: Dict[str, Any]):
        """콘솔에 워크플로우 요약 출력"""
        print("\n" + "="*80)
        print(f"🎯 워크플로우 실행 완료: {summary['workflow_name']}")
        print("="*80)
        print(f"📊 총 조합 수: {summary['total_combinations']}")
        print(f"✅ 성공한 조합: {summary['successful_combinations']}")
        print(f"📈 성공률: {summary['success_rate']:.1%}")
        print(f"⏱️  실행 시간: {summary['duration_seconds']:.1f}초")
        print(f"📁 결과 디렉토리: {summary['output_dir']}")
        
        if summary['combination_details']:
            print(f"\n📋 조합별 상세 결과:")
            for detail in summary['combination_details']:
                status = "✅" if detail['success'] else "❌"
                print(f"  {status} {detail['combination_name']}")
                if not detail['success']:
                    print(f"     오류: {detail['error_message']}")
                else:
                    if detail.get('extraction_result_path'):
                        print(f"     결과: {detail['extraction_result_path']}")
                    if detail.get('evaluation_score') is not None:
                        print(f"     평가점수: {detail['evaluation_score']:.3f}")
        
        print("="*80)
