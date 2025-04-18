from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks
import numpy as np
import pandas as pd
from tqdm import tqdm
import torch

class StockSentimentAnalyzer:
    def __init__(self, model_id='iic/nlp_structbert_sentiment-classification_chinese-base'):
        """
        初始化情感分析器
        
        Args:
            model_id (str): ModelScope模型ID
                可选
                'iic/nlp_structbert_sentiment-classification_chinese-base','正面','负面';
                'iic/nlp_structbert_sentiment-classification_chinese-large','正面','负面';
                'iic/nlp_structbert_sentiment-classification_chinese-tiny','正面','负面';
                'Fengshenbang/Erlangshen-RoBERTa-330M-Sentiment','正向','负向';
                'Fengshenbang/Erlangshen-RoBERTa-110M-Sentiment','正向','负向'
        """
        self.semantic_cls = pipeline(Tasks.text_classification, model_id)
        # 情感标签映射 (负面:-1, 正面:1)
        self.label_map = {"负面": -1, "正面": 1}
    
    def predict_sentiment(self, text):
        """预测单条文本的情感"""
        try:
            # 调用ModelScope API
            result = self.semantic_cls(input=text)
            
            if 'scores' in result and 'labels' in result:
                scores = result['scores']
                labels = result['labels']
                
                # 找出正面和负面标签的索引
                positive_idx = -1
                negative_idx = -1
                
                for i, label in enumerate(labels):
                    if label == '正面':
                        positive_idx = i
                    elif label == '负面':
                        negative_idx = i
                
                # 确保找到了正面和负面的标签
                if positive_idx != -1 and negative_idx != -1:
                    positive_prob = scores[positive_idx]
                    negative_prob = scores[negative_idx]
                    
                    # 确定极性 (概率更高的标签作为预测结果)
                    if positive_prob > negative_prob:
                        polarity = self.label_map["正面"]  # 1
                    else:
                        polarity = self.label_map["负面"]  # -1
                    
                    # 计算情感得分 (正面概率 - 负面概率)
                    score = positive_prob - negative_prob
                    
                    # 计算情感强度 (最高概率与次高概率的差距)
                    intensity = abs(positive_prob - negative_prob)
                    
                    return {
                        'score': float(score),
                        'polarity': int(polarity),
                        'intensity': float(intensity),
                        'positive_prob': float(positive_prob),
                        'negative_prob': float(negative_prob),
                        'success': True
                    }
            
            # API调用失败或解析错误时返回默认值
            return {
                'score': 0.0,
                'polarity': 0,
                'intensity': 0.0,
                'positive_prob': 0.5,
                'negative_prob': 0.5,
                'success': False
            }
            
        except Exception as e:
            print(f"预测出错: {e}")
            return {
                'score': 0.0,
                'polarity': 0,
                'intensity': 0.0,
                'positive_prob': 0.5,
                'negative_prob': 0.5,
                'success': False
            }
    
    def predict_batch(self, texts, batch_size=32):
        """批量预测多条文本的情感"""
        results = []
        
        for i in tqdm(range(0, len(texts), batch_size), desc="情感分析进度"):
            batch_texts = texts[i:i+batch_size]
            batch_results = []
            
            for text in batch_texts:
                batch_results.append(self.predict_sentiment(text))
            
            results.extend(batch_results)
        
        return results
    
    def analyze_sentiment_statistics(self, sentiment_results):
        """
        对情感分析结果进行统计分析
        
        Args:
            sentiment_results: 情感分析结果列表
            
        Returns:
            统计信息字典
        """
        # 提取成功的预测结果
        valid_results = [r for r in sentiment_results if r['success']]
        
        if not valid_results:
            return {
                "总评论数": len(sentiment_results),
                "有效分析数": 0,
                "分析成功率": 0.0
            }
        
        # 提取各项指标值
        polarities = [r['polarity'] for r in valid_results]
        scores = [r['score'] for r in valid_results]
        intensities = [r['intensity'] for r in valid_results]
        
        # 统计极性分布
        positive_count = polarities.count(1)
        negative_count = polarities.count(-1)
        
        # 计算统计指标
        stats = {
            "总评论数": len(sentiment_results),
            "有效分析数": len(valid_results),
            "分析成功率": len(valid_results) / len(sentiment_results) * 100,
            "正面评论数": positive_count,
            "负面评论数": negative_count,
            "正面评论比例": positive_count / len(valid_results) * 100,
            "负面评论比例": negative_count / len(valid_results) * 100,
            "平均情感得分": np.mean(scores),
            "情感得分中位数": np.median(scores),
            "情感得分标准差": np.std(scores),
            "平均情感强度": np.mean(intensities),
            "最大情感强度": max(intensities),
            "最小情感强度": min(intensities)
        }
        
        return stats 