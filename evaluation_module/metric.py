import os
import re
import numpy as np
import pandas as pd
from typing import Any, Dict, Optional, Union
from loguru import logger

from langchain_openai import OpenAIEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings


def normalize_prediction_json(pred_json, gt_json):
    """
    예측 결과 JSON을 ground truth 구조에 맞게 정규화합니다.
    - ground truth와 동일한 순서로 필드를 정렬합니다.
    - 누락된 필드는 null로 채웁니다.
    - Pydantic 모델을 사용하지 않고, ground truth 구조만 참조합니다.
    
    Args:
        prediction_json (dict): 정규화할 원본 예측 JSON
        ground_truth (dict): 정답 데이터(기준)
        
    Returns:
        dict: ground truth 구조에 맞게 정규화된 JSON
    """
    try:
        # 원본 JSON 사본 생성 (원본 수정 방지)
        normalized_data = {}
        
        # ground_truth를 기반으로 구조 생성
        def normalize_object(pred_obj, gt_obj):
            """중첩 객체를 정규화하는 재귀 함수"""
            result = {}
            
            # ground truth의 모든 키를 반복하며 순서 유지
            for key in gt_obj.keys():
                # 예측에 키가 없는 경우 null 추가
                if key not in pred_obj:
                    # ground truth 값 확인 - 리스트나 딕셔너리인 경우 적절한 빈 구조 생성
                    if isinstance(gt_obj[key], list):
                        result[key] = []
                    elif isinstance(gt_obj[key], dict):
                        result[key] = {}
                    else:
                        result[key] = None
                    continue
                
                # 키가 존재하는 경우 값 유형에 따라 처리
                if isinstance(gt_obj[key], dict) and isinstance(pred_obj[key], dict):
                    # 중첩 객체 재귀 정규화
                    result[key] = normalize_object(pred_obj[key], gt_obj[key])
                elif isinstance(gt_obj[key], list) and isinstance(pred_obj[key], list):
                    # 리스트 항목 정규화
                    result[key] = []
                    for idx, item in enumerate(pred_obj[key]):
                        # ground truth와 예측 결과 리스트 길이가 다를 수 있음
                        if idx < len(gt_obj[key]) and isinstance(item, dict) and isinstance(gt_obj[key][idx], dict):
                            # 리스트 내 객체를 정규화
                            result[key].append(normalize_object(item, gt_obj[key][idx]))
                        else:
                            # 리스트 원소가 객체가 아니거나 참조할 ground truth 항목이 없는 경우 원본 사용
                            result[key].append(item)
                            
                    # 예측 결과의 리스트가 ground truth보다 짧은 경우, 나머지 항목은 빈 객체로 채움
                    for _ in range(len(pred_obj[key]), len(gt_obj[key])):
                        if gt_obj[key] and isinstance(gt_obj[key][0], dict):
                            # ground truth 첫 항목 구조 기반으로 빈 객체 생성
                            empty_obj = {k: None for k in gt_obj[key][0].keys()}
                            result[key].append(empty_obj)
                        else:
                            result[key].append(None)
                else:
                    # 기본 값 처리
                    result[key] = pred_obj[key]
            
            return result
        
        # 전체 JSON 정규화
        normalized_data = normalize_object(pred_json or {}, gt_json)
        
        logger.success("JSON 정규화가 성공적으로 완료되었습니다.")
        return normalized_data
    
    except Exception as e:
        logger.error(f"JSON 정규화 중 오류 발생: {e}")
        # 오류 발생 시 원본 반환
        return pred_json
    
# 임베딩 백엔드 선택: huggingface, openai, vllm, ollama
class EmbeddingBackend:
    def __init__(self, backend: str = 'huggingface', model_name: Optional[str] = None, api_key: Optional[str] = None, api_base: Optional[str] = None):
        self.backend = backend
        self.model_name = model_name
        self.api_key = api_key
        self.api_base = api_base
        if backend == 'openai':
            self.model = OpenAIEmbeddings(
                model=model_name or 'text-embedding-ada-002',
            )
        elif backend in ['vllm', 'ollama']:
            self.model = OpenAIEmbeddings(
                model=model_name,
                openai_api_key=api_key,
                openai_api_base=api_base
            )
        elif backend == 'huggingface':
            self.model = HuggingFaceEmbeddings(model_name=model_name or 'jhgan/ko-sroberta-multitask')
        else:
            logger.error(f"Unsupported embedding backend: {backend}")
            raise NotImplementedError(f"Backend {backend} not supported.")
        

    def embed(self, texts):
        if isinstance(texts, str):
            texts = [texts]
        return np.array(self.model.embed_documents(texts))

def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)
    if a.ndim == 1:
        a = a.reshape(1, -1)
    if b.ndim == 1:
        b = b.reshape(1, -1)
    return float(np.dot(a, b.T) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8))


def compare_json(gt, pred, embedder: EmbeddingBackend, weights: Optional[Dict[str, float]] = None, path="", field_eval_criteria: Optional[Dict[str, str]] = None):

    def normalize_field_path(field_path):
        # 'careers[2|1].company_name' -> 'careers.company_name'
        # 'certificates[0|0].certificate_name' -> 'certificates.certificate_name'
        # 모든 [숫자], [숫자|숫자], [숫자|-], [-|숫자] 패턴 제거
        return re.sub(r'\[(\d+\|\d+|\d+|\-|\d+\|\-|\-\|\d+)\]', '', field_path)
    """
    gt: ground truth json
    pred: prediction json (정규화된)
    embedder: 임베딩 백엔드 객체
    weights: 필드별 가중치 dict
    path: 내부 재귀용
    field_eval_criteria: 필드별 평가기준 dict ("exact" or "embedding")
    """
    report = {}
    total_score = 0.0
    total_weight = 0.0
    structure_score = 1.0  # 정규화된 경우 항상 1.0
    content_score = 0.0
    field_reports = {}

    def _compare(gt_val, pred_val, key, weight=1.0, path="", field_eval_criteria=None):
        field_path = f"{path}.{key}" if path else key
        norm_field_path = normalize_field_path(field_path)
        result = {"gt": gt_val, "pred": pred_val, "weight": weight}
        eval_criteria = None
        if field_eval_criteria:
            # 항상 정규화된 key로만 조회
            eval_criteria = field_eval_criteria.get(norm_field_path, None)

        # 타입 분기
        if isinstance(gt_val, dict) and isinstance(pred_val, dict):
            sub_score = 0.0
            sub_weight = 0.0
            sub_fields = {}
            for k in gt_val:
                w = weights.get(field_path + "." + k, 1.0) if weights else 1.0
                r = _compare(gt_val[k], pred_val.get(k), k, w, field_path, field_eval_criteria)
                sub_score += r["score"] * w
                sub_weight += w
                sub_fields[k] = r
            result["score"] = sub_score / sub_weight if sub_weight > 0 else 1.0
            result["fields"] = sub_fields
            result["type"] = "dict"
            return result
        elif isinstance(gt_val, list) and isinstance(pred_val, list):
            gt_strs = [str(x) for x in gt_val]
            pred_strs = [str(x) for x in pred_val]
            all_texts = gt_strs + pred_strs
            all_embs = embedder.embed(all_texts)
            gt_embs = all_embs[:len(gt_strs)]
            pred_embs = all_embs[len(gt_strs):]
            sim_matrix = np.zeros((len(gt_val), len(pred_val)))
            for i in range(len(gt_val)):
                for j in range(len(pred_val)):
                    sim_matrix[i, j] = cosine_similarity(gt_embs[i], pred_embs[j])
            # Hungarian Algorithm (최대 유사도 매칭)
            try:
                from scipy.optimize import linear_sum_assignment
                # linear_sum_assignment는 최소 비용 매칭이므로, -sim_matrix로 변환
                row_ind, col_ind = linear_sum_assignment(-sim_matrix)
                match_pairs = [(i, j, sim_matrix[i, j]) for i, j in zip(row_ind, col_ind)]
                gt_matched = set(row_ind)
                pred_matched = set(col_ind)
            except ImportError:
                # scipy가 없으면 greedy fallback
                gt_matched = set()
                pred_matched = set()
                match_pairs = []
                for _ in range(min(len(gt_val), len(pred_val))):
                    max_sim = -1
                    max_pair = (None, None)
                    for i in range(len(gt_val)):
                        if i in gt_matched:
                            continue
                        for j in range(len(pred_val)):
                            if j in pred_matched:
                                continue
                            if sim_matrix[i, j] > max_sim:
                                max_sim = sim_matrix[i, j]
                                max_pair = (i, j)
                    if max_pair[0] is not None and max_pair[1] is not None:
                        gt_matched.add(max_pair[0])
                        pred_matched.add(max_pair[1])
                        match_pairs.append((max_pair[0], max_pair[1], max_sim))
            scores = []
            items = []
            for i, j, sim in match_pairs:
                r = _compare(gt_val[i], pred_val[j], f"{key}[{i}|{j}]", weight, path, field_eval_criteria)
                r["match_idx"] = (i, j)
                r["match_sim"] = sim
                # 점수 보정: 체크된 필드는 완전일치만 1점, 아니면 0점
                match_field_path = f"{path}.{key}" if path else key
                norm_match_field_path = normalize_field_path(match_field_path)
                match_criteria = field_eval_criteria.get(norm_match_field_path, None) if field_eval_criteria else None
                if match_criteria == "exact":
                    if (gt_val[i] is not None and pred_val[j] is not None and str(gt_val[i]).strip() == str(pred_val[j]).strip()):
                        r["score"] = 1.0
                        r["reason"] = "완전일치(체크)"
                    else:
                        r["score"] = 0.0
                        r["reason"] = "불일치(체크)"
                scores.append(r["score"])
                items.append(r)
            for i in range(len(gt_val)):
                if i not in gt_matched:
                    r = _compare(gt_val[i], None, f"{key}[{i}|-]", weight, path, field_eval_criteria)
                    r["match_idx"] = (i, None)
                    r["match_sim"] = None
                    scores.append(r["score"])
                    items.append(r)
            for j in range(len(pred_val)):
                if j not in pred_matched:
                    r = _compare(None, pred_val[j], f"{key}[-|{j}]", weight, path, field_eval_criteria)
                    r["match_idx"] = (None, j)
                    r["match_sim"] = None
                    scores.append(r["score"])
                    items.append(r)
            result["score"] = float(np.mean(scores)) if scores else 1.0
            result["items"] = items
            result["type"] = "list"
            return result
        elif isinstance(gt_val, str) and isinstance(pred_val, str):
            # 1. 임베딩 유사도 점수 계산
            if gt_val.strip() == pred_val.strip():
                sim = 1.0
                reason = "정확히 일치"
            else:
                emb = embedder.embed([gt_val, pred_val])
                sim = cosine_similarity(emb[0], emb[1])
                reason = f"의미 유사도: {sim:.2f}"
            # 2. 체크된 필드는 완전일치만 1점, 아니면 0점으로 덮어쓰기
            if eval_criteria == "exact":
                if gt_val.strip() == pred_val.strip():
                    sim = 1.0
                    reason = "완전일치(체크)"
                else:
                    sim = 0.0
                    reason = "불일치(체크)"
            result["score"] = sim
            result["type"] = "string"
            result["similarity"] = sim
            result["reason"] = reason
            result["criteria"] = eval_criteria or "embedding"
            return result
        elif isinstance(gt_val, (int, float)) and isinstance(pred_val, (int, float)):
            sim = 1.0 if gt_val == pred_val else 0.0
            if eval_criteria == "exact":
                sim = 1.0 if gt_val == pred_val else 0.0
            result["score"] = sim
            result["type"] = "number"
            result["reason"] = "정확히 일치" if sim == 1.0 else "불일치"
            result["criteria"] = eval_criteria or "embedding"
            return result
        elif isinstance(gt_val, bool) and isinstance(pred_val, bool):
            sim = 1.0 if gt_val == pred_val else 0.0
            if eval_criteria == "exact":
                sim = 1.0 if gt_val == pred_val else 0.0
            result["score"] = sim
            result["type"] = "bool"
            result["reason"] = "정확히 일치" if sim == 1.0 else "불일치"
            result["criteria"] = eval_criteria or "embedding"
            return result
        elif gt_val is None and pred_val is None:
            result["score"] = 1.0
            result["type"] = "none"
            result["reason"] = "정확히 일치"
            result["criteria"] = eval_criteria or "embedding"
            return result
        elif gt_val is None or pred_val is None:
            result["score"] = 0.0
            result["type"] = "none"
            result["reason"] = "값 없음"
            result["criteria"] = eval_criteria or "embedding"
            return result
        else:
            result["score"] = 0.0
            result["type"] = "mismatch"
            result["reason"] = "타입 불일치"
            result["criteria"] = eval_criteria or "embedding"
            return result

    # 최상위 비교
    for k in gt:
        w = weights.get(k, 1.0) if weights else 1.0
        r = _compare(gt[k], pred.get(k), k, w, "", field_eval_criteria)
        field_reports[k] = r
        total_score += r["score"] * w
        total_weight += w
    content_score = total_score / total_weight if total_weight > 0 else 1.0
    report = {
        "overall_score": content_score,  # 구조 점수는 정규화로 항상 1.0
        "structure_score": structure_score,
        "content_score": content_score,
        "fields": field_reports,
        "field_eval_criteria": field_eval_criteria or {}
    }
    return report

def eval_json(gt_json, norm_pred, embed_backend, model_name=None, api_key=None, api_base=None, run_folder=None, field_eval_criteria=None):
    """
    의미 유사도/완전일치 기반 JSON 평가 metric 실행 (필드별 평가기준 지원)
    """

    api_base = f"{api_base}/v1" if api_base else None
    provider, *model_parts = model_name.split("/") if model_name else (None,)
    model_name_short = "/".join(model_parts) if model_parts else model_name

    # 임베딩 백엔드 객체 생성
    if embed_backend == 'huggingface':
        embedder = EmbeddingBackend('huggingface', model_name=model_name_short)
    elif embed_backend == 'openai':
        embedder = EmbeddingBackend('openai', model_name=model_name_short)
    elif embed_backend == 'vllm':
        embedder = EmbeddingBackend('vllm', model_name=model_name_short, api_base=api_base)
    elif embed_backend == 'ollama':
        embedder = EmbeddingBackend('ollama', model_name=model_name_short, api_base=api_base)
    else:
        return


    report = compare_json(gt_json, norm_pred, embedder, field_eval_criteria=field_eval_criteria)

    return report