from sentence_transformers import SentenceTransformer

# 测试最小化模型
model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
test_text = "Hello, vector database!"
embedding = model.encode(test_text)

print(f"模型加载成功！")
print(f"向量维度: {len(embedding)}")
print(f"前5个值: {embedding[:5]}")