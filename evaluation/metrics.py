from __future__ import annotations

import os
import re
import numpy as np
from typing import Dict, Optional
from loguru import logger

from langchain_openai import OpenAIEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
from scipy.optimize import linear_sum_assignment


def normalize_field_path(field_path):
    return re.sub(r'\[(\d+\|\d+|\d+|\-|\d+\|\-|\-\|\d+)\]', '', field_path)


class EmbeddingBackend:
    def __init__(self, provider: str = 'huggingface', model: Optional[str] = None, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.provider = provider
        self.model = model
        self.api_key = api_key
        self.base_url = base_url

        if provider == 'openai':
            self.model = OpenAIEmbeddings(
                model=model or 'text-embedding-ada-002',
            )
        elif provider == 'ollama':
            self.model = OpenAIEmbeddings(
                model=model,
                openai_api_key=os.getenv("OLLAMA_API_KEY", "dummy"),
                openai_api_base=base_url
            )
        elif provider == 'openai_compatible':
            self.model = OpenAIEmbeddings(
                model=model,
                openai_api_key=os.getenv("OPENAI_COMPATIBLE_API_KEY", "dummy"),
                openai_api_base=base_url
            )
        elif provider == 'huggingface':
            self.model = HuggingFaceEmbeddings(model_name=model or 'jhgan/ko-sroberta-multitask')
        else:
            logger.error(f"Unsupported embedding backend: {provider}")
            raise NotImplementedError(f"Backend {provider} not supported.")

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


def normalize_prediction_json(pred_json, gt_json):
    try:
        normalized_data = {}

        def normalize_object(pred_obj, gt_obj):
            result = {}
            for key in gt_obj.keys():
                if key not in pred_obj:
                    if isinstance(gt_obj[key], list):
                        result[key] = []
                    elif isinstance(gt_obj[key], dict):
                        result[key] = {}
                    else:
                        result[key] = None
                    continue
                if isinstance(gt_obj[key], dict) and isinstance(pred_obj[key], dict):
                    result[key] = normalize_object(pred_obj[key], gt_obj[key])
                elif isinstance(gt_obj[key], list) and isinstance(pred_obj[key], list):
                    result[key] = []
                    for idx, item in enumerate(pred_obj[key]):
                        if idx < len(gt_obj[key]) and isinstance(item, dict) and isinstance(gt_obj[key][idx], dict):
                            result[key].append(normalize_object(item, gt_obj[key][idx]))
                        else:
                            result[key].append(item)
                    for _ in range(len(pred_obj[key]), len(gt_obj[key])):
                        if gt_obj[key] and isinstance(gt_obj[key][0], dict):
                            empty_obj = {k: None for k in gt_obj[key][0].keys()}
                            result[key].append(empty_obj)
                        else:
                            result[key].append(None)
                else:
                    result[key] = pred_obj[key]
            return result

        normalized_data = normalize_object(pred_json or {}, gt_json)
        logger.success("JSON 정규화가 성공적으로 완료되었습니다.")
        return normalized_data
    except Exception as e:
        logger.error(f"JSON 정규화 중 오류 발생: {e}")
        return pred_json


def load_embedder(provider, model=None, base_url=None):
    if provider == 'huggingface':
        return EmbeddingBackend('huggingface', model=model)
    elif provider == 'openai':
        return EmbeddingBackend('openai', model=model)
    elif provider == 'openai_compatible':
        if not base_url:
            base_url = os.getenv("OPENAI_COMPATIBLE_BASEURL", "http://localhost:8000/v1")
        return EmbeddingBackend('openai_compatible', model=model, base_url=base_url, api_key=os.getenv("OPENAI_COMPATIBLE_API_KEY", "dummy"))
    elif provider == 'ollama':
        if not base_url:
            base_url = os.getenv("OLLAMA_BASEURL", "http://localhost:11434/v1")
        return EmbeddingBackend('ollama', model=model, base_url=base_url, api_key=os.getenv("OLLAMA_API_KEY", "dummy"))
    else:
        return


def eval_json(gt, pred, host_info, field_eval_criteria=None, weights: Optional[Dict[str, float]] = None):
    report = {}
    total_score = 0.0
    total_weight = 0.0
    field_reports = {}

    embedder = load_embedder(host_info.provider, model=host_info.model, base_url=host_info.base_url)

    def _compare(gt_val, pred_val, key, weight=1.0, path="", field_eval_criteria=None):
        field_path = f"{path}.{key}" if path else key
        norm_field_path = normalize_field_path(field_path)
        result = {"gt": gt_val, "pred": pred_val, "weight": weight}
        eval_criteria = None
        if field_eval_criteria:
            eval_criteria = field_eval_criteria.get(norm_field_path, None)

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
            try:
                row_ind, col_ind = linear_sum_assignment(-sim_matrix)
                match_pairs = [(i, j, sim_matrix[i, j]) for i, j in zip(row_ind, col_ind)]
                gt_matched = set(row_ind)
                pred_matched = set(col_ind)
            except ImportError:
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
            if gt_val.strip() == pred_val.strip():
                sim = 1.0
                reason = "정확히 일치"
            else:
                emb = embedder.embed([gt_val, pred_val])
                sim = cosine_similarity(emb[0], emb[1])
                reason = f"의미 유사도: {sim:.2f}"
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

    for k in gt:
        w = weights.get(k, 1.0) if weights else 1.0
        r = _compare(gt[k], pred.get(k), k, w, "", field_eval_criteria)
        field_reports[k] = r
        total_score += r["score"] * w
        total_weight += w
    content_score = total_score / total_weight if total_weight > 0 else 1.0
    report = {
        "overall_score": content_score,
        "fields": field_reports,
        "field_eval_criteria": field_eval_criteria or {}
    }
    return report
