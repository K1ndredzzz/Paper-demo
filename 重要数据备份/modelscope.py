from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks

p = pipeline(Tasks.text_classification, 'Fengshenbang/Erlangshen-RoBERTa-110M-Sentiment')
result = p(input='这种衣服还好看？')

# 打印结果
print(result)