# -*- coding: utf-8 -*-
"""Ứng dụng.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1updUMLcV_mTsFuPtxa6FYFnKDJg5H8Cy

# Thư viện
"""

import pandas as pd
import numpy as np
import re
import string

from underthesea import sent_tokenize
from pyvi import ViTokenizer

import matplotlib.pyplot as plt
import os

from sklearn.feature_extraction.text import TfidfVectorizer

"""# Các file, hàm cần dùng"""

from google.colab import drive
drive.mount('/content/drive')

reference_stwrds = ('/content/drive/MyDrive/NLP/Data/vietnamese-stopwords.txt')
with open(reference_stwrds, 'r', encoding='utf-8') as file:
    vn_stopwords = file.readline()

def remove_punctuation(text):
    return "".join([i for i in text if i not in string.punctuation])

def remove_emoji(text):
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # Emoticons
        u"\U0001F300-\U0001F5FF"  # Symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # Transport & map symbols
        u"\U0001F700-\U0001F77F"  # Alchemical symbols
        u"\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
        u"\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
        u"\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        u"\U0001FA00-\U0001FA6F"  # Chess Symbols
        u"\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
        u"\U00002702-\U000027B0"  # Dingbats
        u"\U000024C2-\U0001F251"  # Enclosed characters
        u"\U0001F1E6-\U0001F1FF"  # Regional Indicator Symbols (flags)
        u"\U0001F3FB-\U0001F3FF"  # Emoji modifiers (skin tones)
        u"\uFE0F"                 # Variation Selector
        "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', text)

def remove_extra_spaces(text):
    # Strip leading/trailing spaces and replace multiple spaces with a single space
    return ' '.join(text.split())

def preprocess(text):
    text = remove_punctuation(text)
    text = remove_emoji(text)
    text = remove_extra_spaces(text)  # Remove unnecessary spaces
    text = text.lower()
    return text

# prompt: def tokenizer

def tokenizer(text):
    text = preprocess(text)
    text = ViTokenizer.tokenize(text)
    text = ' '.join([word for word in text.split() if word not in vn_stopwords])
    return text

"""# Ứng dụng"""

def analyze_comments(file_path, output_path):
    import pickle
    import matplotlib.pyplot as plt
    from wordcloud import WordCloud
    # Load mô hình
    model_filename = '/content/drive/MyDrive/NLP/Models/best_knn_model.sav'
    best_knn_model = pickle.load(open(model_filename, 'rb'))

    model_filename = '/content/drive/MyDrive/NLP/Models/best_nb_model.sav'
    best_nb_model = pickle.load(open(model_filename, 'rb'))

    model_filename = '/content/drive/MyDrive/NLP/Models/best_rf_model.sav'
    best_rf_model = pickle.load(open(model_filename, 'rb'))

    # model_filename = '/content/drive/MyDrive/NLP/Models/biLSTM_model.sav'
    # biLSTM_model = pickle.load(open(model_filename, 'rb'))

    vectorizer = '/content/drive/MyDrive/NLP/Models/vectorizer.sav'
    vectorizer = pickle.load(open(vectorizer, 'rb'))
    # Đọc file CSV
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        print(f"Lỗi khi đọc file: {e}")
        return

    # Kiểm tra cột chứa comment
    if 'comment' not in df.columns:
        print("File CSV phải chứa cột 'comment'!")
        return

    # Tiền xử lý
    df.dropna(inplace=True)
    df.drop_duplicates(inplace=True)
    df['1_comment'] = df['comment'].apply(preprocess)
    df['2_comment'] = df['1_comment'].apply(lambda x: ' '
                      .join([word for word in x.split() if word.lower() not in vn_stopwords]))
    # Giữ lại các cụm từ
    keep_together = ["cũng như", "xịn xò", "vẻ bề ngoài", "thầy cô", "chỉ còn", "làm tiền", "làm mình làm mẩy"]

    comment_column_index = df.columns.get_loc('2_comment')

    # Create an empty list to store tokens for all rows
    all_tokens = []

    for i in range(len(df)):
        text = str(df.iloc[i, comment_column_index]).lower()
        for phrase in keep_together:
            text = re.sub(r'\b' + phrase + r'\b', phrase.replace(" ", "_"), text)

        tokens = ViTokenizer.tokenize(text).split()  # Tokenize after replacing spaces in phrases

        # Instead of assigning to df.loc directly, append to the list
        all_tokens.append(tokens)

    # After processing all rows, assign the list of token lists to the 'tokens' column
    df["tokens"] = all_tokens

    df["sent_tokens"] = df["tokens"].apply(lambda x: " ".join(x)).astype(str)

    X = df['sent_tokens']  # Các câu tokenized
    # vectorizer.fit(X)

    # vectorizer.fit(df['sent_tokens']) # Fit the vectorizer to your preprocessed data

    X_vec = vectorizer.transform(X) # Now you can transform

    # Dự đoán nhãn với cả 3 mô hình
    knn_pred = best_knn_model.predict(X_vec)
    nb_pred = best_nb_model.predict(X_vec)
    rf_pred = best_rf_model.predict(X_vec)
    # biLSTM_pred =  biLSTM_model.predict(X_vec)

    # Kết hợp dự đoán (ví dụ: lấy mode của 3 mô hình)
    df['predicted_label'] = np.apply_along_axis(lambda x: np.argmax(np.bincount(x)), axis=0, arr=np.array([knn_pred, nb_pred, rf_pred]).astype(int))

    # EDA
    negative_comments = len(df[df['predicted_label'] == 0])
    positive_comments = len(df[df['predicted_label'] == 1])
    # print(df)

    plt.figure(figsize=(8, 6))
    plt.bar(['Tiêu cực', 'Tích cực'], [negative_comments, positive_comments], color=['red', 'green'])
    plt.ylabel("Số lượng bình luận")
    plt.title("Số lượng bình luận tiêu cực và tích cực")
    plt.show()

    # Wordcloud for positive comments
    positive_text = " ".join(df[df['predicted_label'] == 1]['sent_tokens'])
    wordcloud_positive = WordCloud(width=800, height=400, background_color='white').generate(positive_text)
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud_positive, interpolation='bilinear')
    plt.axis("off")
    plt.title("Wordcloud for Positive Comments")
    plt.show()

    # Wordcloud for negative comments
    negative_text = " ".join(df[df['predicted_label'] == 0]['sent_tokens'])
    wordcloud_negative = WordCloud(width=800, height=400, background_color='white').generate(negative_text)
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud_negative, interpolation='bilinear')
    plt.axis("off")
    plt.title("Wordcloud for Negative Comments")
    plt.show()

    try:
        # Nếu output_path là thư mục, tự động thêm tên file
        if os.path.isdir(output_path):
            output_path = os.path.join(output_path, "predicted_comments.csv")

        df.to_csv(output_path, index=False)
        print(f"Kết quả phân tích đã được lưu tại: {output_path}")
    except Exception as e:
        print(f"Lỗi khi xuất file: {e}")

# /content/drive/MyDrive/NLP/Data/test ứng dụng.csv
# /content/drive/MyDrive/NLP/Data
if __name__ == "__main__":
    input_file = input("Nhập đường dẫn file CSV chứa bình luận: ")
    output_dir = input("Nhập đường dẫn thư mục lưu kết quả: ")
    analyze_comments(input_file, output_dir)
