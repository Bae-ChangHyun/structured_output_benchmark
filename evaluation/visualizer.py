import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict, Any, List, Tuple, Union
import json
import argparse


class EvaluationVisualizer:
    """
    jycm 스타일의 JSON 비교 결과 시각화 클래스
    """

    def __init__(self):
        self.color_scheme = {
            'perfect': '#2E8B57',      # 완벽한 매치 (초록)
            'good': '#32CD32',         # 좋은 매치 (연한 초록)
            'medium': '#FFD700',       # 보통 매치 (노랑)
            'poor': '#FF6347',         # 나쁜 매치 (주황)
            'very_poor': '#DC143C',    # 매우 나쁜 매치 (빨강)
            'missing': '#808080',      # 누락된 필드 (회색)
            'mismatch': '#8B008B'      # 타입 불일치 (보라)
        }

    def get_score_color(self, score: float) -> str:
        if score >= 0.9:
            return self.color_scheme['perfect']
        elif score >= 0.8:
            return self.color_scheme['good']
        elif score >= 0.6:
            return self.color_scheme['medium']
        elif score >= 0.4:
            return self.color_scheme['poor']
        elif score > 0:
            return self.color_scheme['very_poor']
        else:
            return self.color_scheme['missing']

    def get_score_emoji(self, score: float) -> str:
        if score >= 0.9:
            return "🟢"
        elif score >= 0.8:
            return "🟡"
        elif score >= 0.6:
            return "🟠"
        elif score >= 0.4:
            return "🔴"
        elif score > 0:
            return "🔺"
        else:
            return "⚫"

    def visualize_overall_scores(self, report: Dict[str, Any]):
        st.subheader("📊 전체 점수 대시보드")
        fig = make_subplots(
            rows=1, cols=1,
            subplot_titles=('', '', ''),
            specs=[[{"type": "indicator"}]]
        )
        fig.add_trace(
            go.Indicator(
                mode="gauge+number+delta",
                value=report['overall_score'],
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Overall Score"},
                delta={'reference': 0.8},
                gauge={
                    'axis': {'range': [None, 1]},
                    'bar': {'color': self.get_score_color(report['overall_score'])},
                    'steps': [
                        {'range': [0, 0.4], 'color': "lightgray"},
                        {'range': [0.4, 0.8], 'color': "gray"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 0.9
                    }
                }
            ),
            row=1, col=1
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    def extract_field_scores(self, fields: Dict[str, Any], prefix: str = "") -> List[Tuple[str, float, str]]:
        scores = []
        for field_name, field_data in fields.items():
            current_path = f"{prefix}.{field_name}" if prefix else field_name
            score = field_data.get('score', 0)
            field_type = field_data.get('type', 'unknown')
            scores.append((current_path, score, field_type))
            if 'fields' in field_data:
                scores.extend(self.extract_field_scores(field_data['fields'], current_path))
            elif 'items' in field_data:
                for i, item in enumerate(field_data['items']):
                    item_path = f"{current_path}[{i}]"
                    item_score = item.get('score', 0)
                    item_type = item.get('type', 'unknown')
                    scores.append((item_path, item_score, item_type))
        return scores

    def visualize_field_scores(self, report: Dict[str, Any]):
        st.subheader("🔍 필드별 상세 점수")
        field_scores = self.extract_field_scores(report['fields'])
        if not field_scores:
            st.info("표시할 필드 데이터가 없습니다.")
            return

        df = pd.DataFrame(field_scores, columns=['Field', 'Score', 'Type'])
        df['Color'] = df['Score'].apply(self.get_score_color)
        df['Emoji'] = df['Score'].apply(self.get_score_emoji)
        df = df.sort_values('Score', ascending=False)

        fig = px.bar(
            df,
            x='Score',
            y='Field',
            color='Score',
            color_continuous_scale='RdYlGn',
            title='필드별 점수 분포',
            labels={'Score': '점수', 'Field': '필드명'}
        )
        fig.update_layout(height=max(400, len(df) * 25))
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("📈 점수 분포")
        fig_hist = px.histogram(
            df,
            x='Score',
            nbins=20,
            title='점수 분포 히스토그램',
            labels={'Score': '점수', 'count': '필드 수'}
        )
        st.plotly_chart(fig_hist, use_container_width=True)
        st.info(f"총 {len(field_scores)}개 필드의 점수가 표시되었습니다.")

    def visualize_detailed_comparison(self, report: Dict[str, Any]):
        st.subheader("🔎 상세 비교 결과")

        def render_field_summary(field_name: str, field_data: Dict[str, Any], depth: int = 0):
            indent = "　" * depth
            score = field_data.get('score', 0)
            emoji = self.get_score_emoji(score)
            field_type = field_data.get('type', 'unknown')

            col1, col2, col3 = st.columns([4, 1, 1])
            with col1:
                field_display_name = f"{indent}{emoji} {field_name}"
                st.write(field_display_name)
            with col2:
                st.write(f"{score:.3f}")
            with col3:
                st.write(f"{field_type}")

            unique_key = f"detail_{field_name}_{depth}_{hash(str(field_data))}"
            with st.expander(f"🔍 {field_name} 상세 정보", expanded=False):
                if field_type == 'string' and 'criteria' in field_data:
                    st.write(f"💬 {field_data['criteria']}")
                elif field_type in ['number', 'bool'] and 'reason' in field_data:
                    st.write(f"ℹ️ {field_data['criteria']}")

                if 'gt' in field_data and 'pred' in field_data:
                    gt_val = field_data['gt']
                    pred_val = field_data['pred']
                    if gt_val is not None or pred_val is not None:
                        col_gt, col_pred = st.columns(2)
                        with col_gt:
                            st.write("**Ground Truth:**")
                            if isinstance(gt_val, (dict, list)):
                                st.json(gt_val)
                            else:
                                st.write(str(gt_val) if gt_val is not None else "None")
                        with col_pred:
                            st.write("**Prediction:")
                            if isinstance(pred_val, (dict, list)):
                                st.json(pred_val)
                            else:
                                st.write(str(pred_val) if pred_val is not None else "None")

                if 'fields' in field_data:
                    st.write("**하위 필드들:**")
                    for sub_field_name, sub_field_data in field_data['fields'].items():
                        render_field_summary(sub_field_name, sub_field_data, depth + 1)
                elif 'items' in field_data:
                    st.write("**배열 아이템들:**")
                    for i, item in enumerate(field_data['items']):
                        render_field_summary(f"[{i}]", item, depth + 1)

        col1, col2, col3 = st.columns([4, 1, 1])
        with col1:
            st.write("**필드명**")
        with col2:
            st.write("**점수**")
        with col3:
            st.write("**타입**")
        st.divider()

        for field_name, field_data in report['fields'].items():
            render_field_summary(field_name, field_data)

    def visualize_report(self, report: Dict[str, Any]):
        tab1, tab2, tab3 = st.tabs(["📊 전체 점수", "🔍 필드별 점수", " 상세 비교"])
        with tab1:
            self.visualize_overall_scores(report)
        with tab2:
            self.visualize_field_scores(report)
        with tab3:
            self.visualize_detailed_comparison(report)


def render_evaluation_report(eval_result: Union[str, Dict[str, Any]]):
    """Convenience function to render a report in Streamlit.

    Accepts either a path to an evaluation result JSON file or the already-parsed dict.
    """
    data: Dict[str, Any]
    if isinstance(eval_result, str):
        with open(eval_result, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = eval_result

    visualizer = EvaluationVisualizer()
    return visualizer.visualize_report(data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--eval-result', type=str, required=True)
    args, _ = parser.parse_known_args()
    try:
        with open(args.eval_result, 'r', encoding='utf-8') as f:
            eval_result = json.load(f)
    except Exception as e:
        st.error(f"파일을 열거나 파싱할 수 없습니다: {e}")
        st.stop()

    render_evaluation_report(eval_result)
